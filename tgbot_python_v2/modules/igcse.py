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
from html.parser import HTMLParser

import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.helpers import escape_markdown

import tgbot_python_v2.util.module
from tgbot_python_v2.util.help import Help

SAVED_MESSAGE_CHAT_ID = -1001607510711
log: logging.Logger = logging.getLogger(__name__)

LOGIN_URL: str = "https://myresults.cie.org.uk/cie-candidate-results/j_spring_security_check"
RESULTS_URL: str = "https://myresults.cie.org.uk/cie-candidate-results/results"

payload: dict[str, str] = {
    "j_username": os.getenv("IGCSE_USERNAME", ""),
    "j_password": os.getenv("IGCSE_PASSWORD", ""),
}


class MarksParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_exam = False
        self.in_examinfo = False
        self.in_result = False
        self.current_exam = ""
        self.results = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            for attr, value in attrs:
                if attr == "summary" and "Your examination results" in value:
                    self.in_table = True
        if self.in_table and tag == "tr":
            self.in_row = True
        if self.in_row and tag == "span":
            classes = dict(attrs).get("class", "")
            if "exam" in classes:
                self.in_exam = True
            if "examinfo" in classes:
                self.in_examinfo = True
        if self.in_row and tag == "td" and ("result" in dict(attrs).get("class", "")):
            self.in_result = True

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        if tag == "tr":
            self.in_row = False
            self.current_exam = ""  # Reset after processing the row
        if tag == "span" and self.in_exam:
            self.in_exam = False
        if tag == "span" and self.in_examinfo:
            self.in_examinfo = False
        if tag == "td" and self.in_result:
            self.in_result = False

    def handle_data(self, data):
        if self.in_exam or self.in_examinfo:
            self.current_exam += data.strip() + " "
        if self.in_result and self.current_exam.strip():
            result = data.strip()
            if result:
                # Append trimmed exam name and result
                self.results.append((self.current_exam.strip(), result))
                self.current_exam = ""


async def igcse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 2:
        pload = {"j_username": context.args[0], "j_password": context.args[1]}
    else:
        pload = payload

    session = requests.Session()
    session.post(LOGIN_URL, pload)
    response = session.get(RESULTS_URL)
    if response.status_code != 200:
        await update.message.reply_text("error")
        return

    parser = MarksParser()
    parser.feed(response.content.decode())

    if "".join(parser.results).strip() == "":
        await update.message.reply_text("Wrong credentials")
        return

    if len(context.args) != 2:
        text = escape_markdown("Candidate 0009's result (Hakimi):\n", version=2)
    else:
        text = escape_markdown("Your result:\n", version=2)

    for exam, result in parser.results:
        text += f">*{escape_markdown(exam, version=2)}*: _{escape_markdown(result, version=2)}_\n"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)


class ModuleMetadata(tgbot_python_v2.util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("igcse", igcse, block=False))


Help.register_help("igcse", "Get Hakimi's IGCSE result.")
