import os
import time
import asyncio
import logging
import concurrent.futures

import telegram.error

from util import module

from telegram import Update, Bot
from telegram.ext import Application, ContextTypes, CommandHandler

TOKEN_OK = True
log: logging.Logger = logging.getLogger(__name__)


class ModuleMetadata(module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("fastpurge", fastpurge))


try:
    from api_token import TOKEN
except ImportError:
    if not (TOKEN := os.getenv("BOT_TOKEN")):
        log.error("Cannot get bot token.")
        TOKEN_OK = False


def purge(chat_id, message_id) -> None:
    bot = Bot(TOKEN)
    try:
        asyncio.run(bot.delete_message(chat_id, message_id))
    except telegram.error.TelegramError as e:
        log.error(f"Failed to purge message:: chat_id:{chat_id} message_id: {message_id}")
        log.error(f"caused by: {e}")
        log.error("")


async def fastpurge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assert TOKEN_OK
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message smh")
        return
    admins = await update.effective_chat.get_administrators()
    log.info(f"Chat admins: {admins}")
    if not any(update.effective_user.id == admin.user.id for admin in admins):
        await update.message.reply_text("You're not admin smh")
        return
    if not any(update.get_bot().id == admin.user.id for admin in admins):
        await update.message.reply_text("I'm not admin smh")
        return

    message = await update.message.reply_text(f"Purging {update.message.id - update.message.reply_to_message.id} messages")
    purge_start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        for message_id in range(update.message.reply_to_message.id, update.message.id + 1):
            executor.submit(purge, update.effective_chat.id, message_id)

    purge_end_time = time.time()
    await message.edit_text(f"Purged {update.message.id - update.message.reply_to_message.id} in {purge_end_time - purge_start_time}")
