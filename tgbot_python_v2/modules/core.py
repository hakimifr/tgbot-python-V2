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
import subprocess
import sys

from telegram import Message, Update
from telegram.ext import Application, CommandHandler, ContextTypes

import tgbot_python_v2.util.module
from tgbot_python_v2.util.help import Help

SAVED_MESSAGE_CHAT_ID = -1001607510711
log: logging.Logger = logging.getLogger(__name__)


class ModuleMetadata(tgbot_python_v2.util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("start", start, block=False))
        app.add_handler(CommandHandler("save", save, block=False))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("A bot written in Python3, by @Hakimi0804.")


async def save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id != 1024853832:
        log.debug("/save was not sent by owner, ignoring")
        return

    if update.message.reply_to_message is None:
        await update.message.reply_text("You must reply to as message.")
    else:
        ret: Message = await update.message.reply_text("Forwarding...")
        await update.message.reply_to_message.forward(SAVED_MESSAGE_CHAT_ID)
        await ret.edit_text("Message forwarded")


Help.register_help("start", "Show bot's about.")
Help.register_help("save", "Forward message to saving group")
