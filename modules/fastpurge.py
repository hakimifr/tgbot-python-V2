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
