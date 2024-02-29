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
from decimal import Context
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

# old json structure:
# {
# "file_unique_id": "file_id",
# "file_unique_id": "file_id"
# }
# expected json structure:
# {
# "file_unique_id": {"file_id": id, trigger_keywords: [keyword, keyword, keyword]},
# "file_unique_id": {"file_id": id, trigger_keywords: [keyword, keyword, keyword]}
# }
config_db: Config = Config("komaru.json")
# expected json structure:
# {
# "trigger_chat_whitelist": [chat_id, chat_id, chat_id]
# }
config: Config = Config("komaru-config.json")

if not config.config.get("trigger_chat_whitelist"):
    config.config["trigger_chat_whitelist"] = []

# Migrate to the new json structure
for key in config_db.config.keys():
    if type(config_db.config[key]) is str:
        log.info(f"Migrating komaru gif '{key}' to new json structure")
        config_db.config[key] = {"file_id": config_db.config[key], "trigger_keywords": []}


class ModuleMetadata(util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("toggleupdatekomaru", update_komaru, block=False))
        app.add_handler(CommandHandler("countkomarugifs", count_komaru_gifs, block=False))
        app.add_handler(CommandHandler("clearkomarudb", clear_db, block=False))
        app.add_handler(CommandHandler("whitelist", whitelist, block=False))
        app.add_handler(CommandHandler("unwhitelist", unwhitelist, block=False))
        app.add_handler(CommandHandler("addtrigger", addtrigger, block=False))
        app.add_handler(CommandHandler("removetrigger", removetrigger, block=False))
        app.add_handler(CommandHandler("listtrigger", listtrigger, block=False))
        app.add_handler(MessageHandler(filters.ANIMATION, komaru_listener, block=False))
        app.add_handler(MessageHandler(filters.TEXT, trigger_handler, block=False), group=1)


async def update_komaru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LISTEN_CHAT_ID, LISTEN_MODE
    if update.message.from_user.id not in KOMARU_APPROVED_USERS:
        await update.message.reply_text("You are not allowed to use this command")
        return

    LISTEN_CHAT_ID = update.message.chat_id
    LISTEN_MODE = not LISTEN_MODE
    if not LISTEN_MODE:
        config_db.write_config()
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

    if update.message.animation.file_unique_id in config_db.config.keys():
        await update.message.reply_text("Already in database, skipping...")
        return

    config_db.config[update.message.animation.file_unique_id] = update.message.animation.file_id
    await update.message.copy(KOMARU_CHANNEL_ID)
    await update.message.reply_text(f"Added to database!\n"
                                    f"file_unique_id: {update.message.animation.file_unique_id}\n"
                                    f"file_id: {update.message.animation.file_id}\n")


async def komaru_channel_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post.animation.file_unique_id in config_db.config.keys():
        await update.channel_post.delete()
    else:
        config_db.config[update.channel_post.animation.file_unique_id] = update.channel_post.animation.file_id
        msg = await update.channel_post.reply_text(f"Added to database!\n"
                                                   f"file_unique_id: {update.channel_post.animation.file_unique_id}\n"
                                                   f"file_id: {update.channel_post.animation.file_id}\n"
                                                   f"This message will auto-delete in 5 seconds.")
        await asyncio.sleep(5)
        await msg.delete()


async def count_komaru_gifs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Number of komaru gifs in database: {len(config_db.config.keys())}")


async def clear_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in KOMARU_APPROVED_USERS:
        await update.message.reply_text("You are not allowed to use this command")
        return

    config_db.config.clear()
    await update.message.reply_text("Database cleared!")


async def whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in KOMARU_APPROVED_USERS:
        await update.message.reply_text("You are not allowed to use this command")
        return

    if update.message.chat_id in config.config["trigger_chat_whitelist"]:
        await update.message.reply_text("Already whitelisted")
        return

    config.config["trigger_chat_whitelist"].append(update.message.chat_id)
    await update.message.reply_text("Whitelisted")


async def unwhitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in KOMARU_APPROVED_USERS:
        await update.message.reply_text("You are not allowed to use this command")
        return

    if update.message.chat_id not in config.config["trigger_chat_whitelist"]:
        await update.message.reply_text("Not whitelisted")
        return

    config.config["trigger_chat_whitelist"].remove(update.message.chat_id)
    await update.message.reply_text("Unwhitelisted")


async def addtrigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in KOMARU_APPROVED_USERS:
        await update.message.reply_text("You are not allowed to use this command")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to add triggers to the database")
        return

    if not update.message.reply_to_message.animation:
        await update.message.reply_text("Replied message is not a GIF")
        return

    if update.message.reply_to_message.animation.file_unique_id not in config_db.config.keys():
        await update.message.reply_text("GIF not in database")
        return

    if not context.args or len(context.args) == 0:
        await update.message.reply_text("Usage: /addtrigger <keyword1> <keyword2>...<keywordX>")
        return

    errors: list[str] = []
    for keyword in context.args:
        if keyword in config_db.config[update.message.reply_to_message.animation.file_unique_id]["trigger_keywords"]:
            errors.append(f"Keyword '{keyword}' already exists")
        else:
            config_db.config[update.message.reply_to_message.animation.file_unique_id]["trigger_keywords"].append(keyword)

    if len(errors) > 0:
        joint: str = "\n".join(errors)
        await update.message.reply_text(f"Updated! There were some errors:\n{joint}")
    else:
        await update.message.reply_text(f"Updated!")


async def removetrigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in KOMARU_APPROVED_USERS:
        await update.message.reply_text("You are not allowed to use this command")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to add triggers to the database")
        return

    if not update.message.reply_to_message.animation:
        await update.message.reply_text("Replied message is not a GIF")
        return

    if update.message.reply_to_message.animation.file_unique_id not in config_db.config.keys():
        await update.message.reply_text("GIF not in database")
        return

    if not context.args or len(context.args) == 0:
        await update.message.reply_text("Usage: /removetrigger <keyword1> <keyword2>...<keywordX>")
        return

    errors: list[str] = []
    for keyword in context.args:
        if keyword in config_db.config[update.message.reply_to_message.animation.file_unique_id]["trigger_keywords"]:
            config_db.config[update.message.reply_to_message.animation.file_unique_id]["trigger_keywords"].remove(keyword)
        else:
            errors.append(f"Keyword '{keyword}' does not exist")

    if len(errors) > 0:
        joint: str = "\n".join(errors)
        await update.message.reply_text(f"Updated! There were some errors:\n{joint}")
    else:
        await update.message.reply_text(f"Updated!")


async def listtrigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a GIF to list triggers!")
        return

    if not update.message.reply_to_message.animation:
        await update.message.reply_text("Replied message is not a GIF!")
        return

    if not update.message.reply_to_message.animation.file_unique_id in config_db.config.keys():
        await update.message.reply_text("Replied GIF is not in DB.")
        return

    anim = update.message.reply_to_message.animation
    await update.message.reply_text(f"{','.join(config_db.config[anim.file_unique_id]['trigger_keywords'])}")


async def trigger_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id not in config.config["trigger_chat_whitelist"]:
        return

    for value in config_db.config.values():
        for keyword in value["trigger_keywords"]:
            if keyword.lower() in update.message.text.lower():
                await update.message.reply_animation(value["file_id"])
                return


Help.register_help("toggleupdatekomaru", "Toggle Komaru updater listener")
Help.register_help("countkomarugifs", "Count number of komaru gifs in database")
Help.register_help("clearkomarudb", "Clear komaru gifs database (DANGEROUS)")
Help.register_help("whitelist", "Whitelist the chat for komaru keyword trigger")
Help.register_help("unwhitelist", "Unwhitelist the chat from komary keyword trigger")
Help.register_help("addtrigger", "Add keyword(s) to be triggered for a gif")
Help.register_help("removetrigger", "Remove keyword(s) trigger from a gif")
