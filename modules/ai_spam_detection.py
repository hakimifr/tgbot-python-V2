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

import re
import logging
import util.module
import telegram
import telegram.error
from util.help import Help
from util.config import Config
from modules.rm6785 import RM6785_MASTER_USER
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, Application, filters
from transformers import pipeline, Pipeline
log: logging.Logger = logging.getLogger(__name__)

GROUP_WHITELISTS: list[int] = [-1001309495065, -1001754321934]  # r6, rm6785
pipe: Pipeline | None = None

base_prompt = """
You are an advanced fraud detection AI, tasked with analyzing user messages to determine if they contain elements of financial, cryptocurrency, or any other type of fraudulent activity.

Your task is to:

Input: Take in user-sent messages (can be in the form of text, emails, or chats) as inputs.

Analysis: Analyze these messages for signs of fraud based on key indicators such as:

Financial fraud: Suspicious payment requests, loan scams, investment schemes, or phishing attempts for sensitive financial information (e.g., credit card numbers, account details, passwords).

Crypto fraud: Scams involving cryptocurrency wallets, fraudulent ICOs, Ponzi schemes, pump-and-dump schemes, unregulated exchanges, or phishing for private keys.

Other types of fraud: Identity theft, scams involving impersonation, social engineering, pyramid schemes, or any suspicious activity promising returns or seeking personal information.

Accuracy and improvement: Aim to be as accurate as possible by utilizing the latest fraud detection patterns and adapting your analysis to emerging scams. Continuously refine your decision-making process by learning from flagged messages, user feedback, and updated fraud prevention techniques.

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
        global pipe
        log.info("Loading AI model, this will take a while")
        pipe = pipeline(
            "text-generation",
            model="google/gemma-2b-it"
        )
        log.info("AI model loaded")

        app.add_handler(MessageHandler(filters.TEXT, on_message, block=False), group=5)


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.chat_id not in GROUP_WHITELISTS:
        return

    prompt = base_prompt + update.message.text
    messages = [{"role": "user", "content": prompt}]
    outputs = pipe(messages, max_new_tokens=256)
    gemma_response = outputs[0]["generated_text"][-1]["content"].strip()

    pattern = r"Fraud detected \(Yes/No\): (\w+)\s*Confidence rate: (\d+)%"

    match = re.search(pattern, gemma_response)
    if match:
        result = {
            'Fraud_detected': match.group(1),
            'Confidence_rate': int(match.group(2))
        }

    fraud_status, confidence_rate = result.values()
    if fraud_status == "Yes" and confidence_rate >= 50:
        try:
            await update.message.delete()
            await update.message.reply_text(f"Deleted message from {update.message.from_user.first_name} due to suspected fraud\n"
                                            f"Gemma's confidence rate: {confidence_rate}%", allow_sending_without_reply=True)
        except telegram.error.BadRequest:
            log.warning("Failed to delete message")