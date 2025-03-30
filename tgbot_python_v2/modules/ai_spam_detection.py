# SPDX-License-Identifier: GPL-3.0-only
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright (c) 2024, Firdaus Hakimi <hakimifirdaus944@gmail.com>

import logging
import os
import re

import google.generativeai as genai
from openai import ConflictError
import telegram
import telegram.error
from telegram import Update
from telegram.ext import Application, ContextTypes, JobQueue, MessageHandler, CommandHandler, filters

import tgbot_python_v2.util.module
from tgbot_python_v2.modules.rm6785 import RM6785_MASTER_USER

log: logging.Logger = logging.getLogger(__name__)

GROUP_WHITELISTS: list[int] = [
    -1001309495065,
    -1001754321934,
    -1001155763792,
    -1001267207006,
    -1001717662621,
]  # r6, rm6785, test env, rm6785 photography, abz hub
confidence_rate_threshold: int = 60

base_prompt = """\
You are an advanced fraud detection AI. Analyze user messages (text, emails, or chats) for financial, cryptocurrency, or other fraudulent activity based on these indicators:

Financial Fraud: Payment scams, loan/investment schemes, phishing for sensitive info.
Crypto Fraud: Wallet scams, fraudulent ICOs, pump-and-dump schemes, phishing for private keys.
Other Fraud: Identity theft, impersonation, pyramid schemes, or scams promising returns.

Guidelines:
Don't gaslight with the confidence rate. If you're not confident, give a lower score. If you are confident, give a higher score.
If you slightly sure or unsure, give a mid score. Be precise with it. The scores you output will be used by my program to determine
whether the message should be limited or not, based on my set threshold. That's why it's important.

Output format (they must be exactly like the following. change only the parts in SQUARE brackets, and remove the SQUARE brackets):
Fraud detected (Yes/No): [Yes/No]
Confidence rate: [Percentage]%

USER-SENT MESSAGE STARTS BELOW THIS LINE::
"""


class ModuleMetadata(tgbot_python_v2.util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        if os.getenv("DISABLE_AI_SPAM_DETECTION", "0") == "1":
            log.info("AI spam detection is disabled, returning early")
            return

        genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
        global generation_config
        global model

        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp", generation_config=generation_config)

        app.add_handler(MessageHandler(filters.TEXT | filters.CAPTION, on_message, block=False), group=3)
        app.add_handler(CommandHandler("getconfidencethreshold", get_confidence_rate_threshold, block=False))
        app.add_handler(CommandHandler("setconfidencethreshold", set_confidence_rate_threshold, block=False))


async def set_confidence_rate_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in RM6785_MASTER_USER:
        await update.message.reply_text("Sorry, you're not allowed to do this")
        return

    global confidence_rate_threshold  # pylint: disable=global-statement
    confidence_rate_threshold = context.args[0]


async def get_confidence_rate_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(str(confidence_rate_threshold))


async def timed_deleter(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.delete_message(context.job.data[0], context.job.data[1])


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message is not None
    if update.message.caption is not None:
        text: str = update.message.caption
    else:
        text: str = update.message.text

    if update.message.chat_id not in GROUP_WHITELISTS:
        log.info(f"chat with id {update.message.chat_id} not in whitelist")
        return

    log.info(f"got message: '{text}'")
    log.info(f"from chat: {update.message.chat_id}")
    if len(text.split(" ")) <= 3:
        log.info("skip checking this text, <= 3 words")
        return

    prompt = base_prompt + text

    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(prompt)
    log.info(f"Gemini's response: {response.text}")

    pattern = r"Fraud detected \(Yes/No\): (\w+)\s*Confidence rate: (\d+)%"

    match = re.search(pattern, response.text)
    if not match:
        log.info("something went wrong with regexing Gemini's response!")
        return

    result = {"Fraud_detected": match.group(1), "Confidence_rate": int(match.group(2))}

    fraud_status, confidence_rate = result.values()
    log.info(f"text: {text}")
    log.info(f"fraud?: {fraud_status}")
    log.info(f"confidence rate: {confidence_rate}")
    log.info("")
    if fraud_status == "Yes" and confidence_rate >= confidence_rate_threshold:
        try:
            await update.message.delete()
            message = await update.get_bot().send_message(
                update.message.chat_id,
                f"Deleted message from {update.message.from_user.first_name} due to suspected fraud\n"
                f"Gemini 2.0 Flash (experiment) confidence rate: {confidence_rate}%\n",
                "This message auto deletes in 30 seconds",
            )
            context.job_queue.run_once(timed_deleter, 30, data=[message.chat_id, message.message_id])
        except telegram.error.BadRequest:
            log.warning("Failed to delete message")
