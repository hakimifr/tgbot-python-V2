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

import os
import re
import logging
import util.module
import telegram
import telegram.error
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, Application, filters
import google.generativeai as genai
log: logging.Logger = logging.getLogger(__name__)

GROUP_WHITELISTS: list[int] = [-1001309495065, -1001754321934, -1001805033064, -1001155763792, -1001299514785]  # r6, rm6785, ai disc, test env, rm6785 test group

base_prompt = """\
You are an advanced fraud detection AI, tasked with analyzing user messages to determine if they contain elements of financial, cryptocurrency, or any other type of fraudulent activity.

Your task is to:

Input: Take in user-sent messages (can be in the form of text, emails, or chats) as inputs.

Analysis: Analyze these messages for signs of fraud based on key indicators such as:

Financial fraud: Suspicious payment requests, loan scams, investment schemes, or phishing attempts for sensitive financial information (e.g., credit card numbers, account details, passwords).

Crypto fraud: Scams involving cryptocurrency wallets, fraudulent ICOs, Ponzi schemes, pump-and-dump schemes, unregulated exchanges, or phishing for private keys.

Other types of fraud: Identity theft, scams involving impersonation, social engineering, pyramid schemes, or any suspicious activity promising returns or seeking personal information.

Accuracy and improvement: Aim to be as accurate as possible by utilizing the latest fraud detection patterns and adapting your analysis to emerging scams. Continuously refine your decision-making process by learning from flagged messages, user feedback, and updated fraud prevention techniques. If a message you received starts with /fban, /ban, /dban, /sban, /warn, then they are admins that are taking actions against spammers. These should not be considered fraud, even if it contains suspicious words as they are the reason field of the bot being used.

Output: Provide a response indicating whether the message likely contains fraudulent activity with:

Fraud detection result: Return "Yes" for suspected fraud and "No" for legitimate or non-suspicious messages.

Confidence level: Provide a confidence percentage (0% to 100%) in your prediction based on the following factors:
The presence of common fraud patterns (e.g., urgency, threats, promises of high returns, requests for personal/financial information).
The context and phrasing of the message (e.g., grammatical mistakes, inconsistent language, suspicious links).
Correlation to known fraud techniques or previously flagged patterns.

Expected format of output:
Fraud detected (Yes/No): [Yes/No]
Confidence rate: [Percentage]


USER-SENT MESSAGE STARTS BELOW THIS LINE::
"""


class ModuleMetadata(util.module.ModuleMetadata):
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

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=generation_config
        )

        app.add_handler(MessageHandler(filters.TEXT, on_message, block=False), group=0)


async def msg_deleter(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    await context.bot.delete_message(job.data[0], job.data[1])


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.chat_id not in GROUP_WHITELISTS:
        log.info(f"chat with id {update.message.chat_id} not in whitelist")
        return

    log.info(f"got message: '{update.message.text}'")
    log.info(f"from chat: {update.message.chat_id}")
    log.info("")

    prompt = base_prompt + update.message.text

    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(prompt)

    pattern = r"Fraud detected \(Yes/No\): (\w+)\s*Confidence rate: (\d+)%"

    match = re.search(pattern, response.text)
    result = {
        'Fraud_detected': match.group(1),
        'Confidence_rate': int(match.group(2))
    }

    fraud_status, confidence_rate = result.values()
    log.info(f"text: {update.message.text}")
    log.info(f"fraud?: {fraud_status}")
    log.info(f"confidence rate: {confidence_rate}")
    log.info("")

    msg = await update.message.reply_text("Gemini 2.0 Flash (exp) debug info\n"
                                         f"Fraud?: {fraud_status}\n"
                                         f"Confidence rate: {confidence_rate}\n\n"
                                         f"This message will auto delete in 5 secs")
    context.job_queue.run_once(msg_deleter, 5, data=[update.message.chat_id, msg.message_id])

    if fraud_status == "Yes" and confidence_rate >= 50:
        try:
            await update.message.delete()
            await update.get_bot().send_message(update.message.chat_id,
                                                f"Deleted message from {update.message.from_user.first_name} due to suspected fraud\n"
                                                f"Gemini 2.0 Flash (experiment) confidence rate: {confidence_rate}%")
        except telegram.error.BadRequest:
            log.warning("Failed to delete message")
