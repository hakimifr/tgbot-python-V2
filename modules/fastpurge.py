# SPDX-License-Identifier: GPL-3.0-only
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
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
import time
import asyncio
import logging

import telegram.error

from util import module
from util.help import Help

from telegram import Update, Bot
from telegram.ext import Application, ContextTypes, CommandHandler

TOKEN_OK = True
log: logging.Logger = logging.getLogger(__name__)


class ModuleMetadata(module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("fastpurge", fastpurge, block=False))


try:
    from api_token import TOKEN
except ImportError:
    if not (TOKEN := os.getenv("BOT_TOKEN")):
        log.error("Cannot get bot token.")
        TOKEN_OK = False


async def fastpurge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assert TOKEN_OK
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message smh")
        return

    message = await update.message.reply_text("Checking admin status")
    admins = await update.effective_chat.get_administrators()
    log.info(f"Chat admins: {admins}")
    if not any(update.effective_user.id == admin.user.id for admin in admins):
        await message.edit_text("You're not admin smh")
        return
    if not any(update.get_bot().id == admin.user.id for admin in admins):
        await message.edit_text("I'm not admin smh")
        return

    await message.edit_text(f"Purging {update.message.id - update.message.reply_to_message.id} messages")
    purge_start_time = time.time()

    message_list: list[int] = [msgid for msgid in range(update.message.reply_to_message.id, update.message.id + 1)]
    while len(message_list) > 0:
        if len(message_list) > 100:
            await update.get_bot().delete_messages(update.effective_chat.id, message_list[:100])
            message_list = message_list[100:]
        else:
            await update.get_bot().delete_messages(update.effective_chat.id, message_list)
            message_list.clear()

    purge_end_time = time.time()
    await message.edit_text(f"Purged {update.message.id - update.message.reply_to_message.id} in {purge_end_time - purge_start_time:.3f}")


Help.register_help("fastpurge", "Purge message with insane speed")
