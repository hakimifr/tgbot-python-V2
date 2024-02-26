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

import asyncio
import logging
import util.module

from util.help import Help
from util.config import Config

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application, filters, MessageHandler


LISTEN_MODE: bool = False
LISTEN_CHAT_ID: int = 0
KOMARU_CHANNEL_ID: int = -1002033198247
KOMARU_APPROVED_USERS: list[int] = [1024853832, 6920687756]
log: logging.Logger = logging.getLogger(__name__)

# expected json structure:
# {
# "file_unique_id": "file_id",
# "file_unique_id": "file_id",
# "file_unique_id": "file_id",
# "file_unique_id": "file_id"
# }
config: Config = Config("komaru.json")


class ModuleMetadata(util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("toggleupdatekomaru", update_komaru, block=False))
        app.add_handler(CommandHandler("countkomarugifs", count_komaru_gifs, block=False))
        app.add_handler(CommandHandler("clearkomarudb", clear_db, block=False))
        app.add_handler(MessageHandler(filters.ANIMATION, komaru_listener, block=False))


async def update_komaru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LISTEN_CHAT_ID, LISTEN_MODE
    if update.message.from_user.id not in KOMARU_APPROVED_USERS:
        await update.message.reply_text("You are not allowed to use this command")
        return

    LISTEN_CHAT_ID = update.message.chat_id
    LISTEN_MODE = not LISTEN_MODE
    if not LISTEN_MODE:
        config.write_config()
    await update.message.reply_text(f"Listen for komaru gif state changed to: {LISTEN_MODE}")


async def komaru_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id == KOMARU_CHANNEL_ID:
        await komaru_channel_listener(update, context)
        return

    if not LISTEN_MODE:
        return
    if update.message.chat_id != LISTEN_CHAT_ID:
        return
    if update.message.from_user.id not in KOMARU_APPROVED_USERS:
        return

    if update.message.animation.file_unique_id in config.config.keys():
        await update.message.reply_text("Already in database, skipping...")
        return

    config.config[update.message.animation.file_unique_id] = update.message.animation.file_id
    await update.message.copy(KOMARU_CHANNEL_ID)
    await update.message.reply_text(f"Added to database!\n"
                                    f"file_unique_id: {update.message.animation.file_unique_id}\n"
                                    f"file_id: {update.message.animation.file_id}\n")


async def komaru_channel_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post.animation.file_unique_id in config.config.keys():
        await update.channel_post.delete()
    else:
        config.config[update.channel_post.animation.file_unique_id] = update.channel_post.animation.file_id
        msg = await update.channel_post.reply_text(f"Added to database!\n"
                                                   f"file_unique_id: {update.channel_post.animation.file_unique_id}\n"
                                                   f"file_id: {update.channel_post.animation.file_id}\n"
                                                   f"This message will auto-delete in 5 seconds.")
        await asyncio.sleep(5)
        await msg.delete()


async def count_komaru_gifs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Number of komaru gifs in database: {len(config.config.keys())}")


async def clear_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in KOMARU_APPROVED_USERS:
        await update.message.reply_text("You are not allowed to use this command")
        return

    config.config.clear()
    await update.message.reply_text("Database cleared!")


Help.register_help("toggleupdatekomaru", "Toggle Komaru updater listener")
Help.register_help("countkomarugifs", "Count number of komaru gifs in database")
Help.register_help("clearkomarudb", "Clear komaru gifs database (DANGEROUS)")
