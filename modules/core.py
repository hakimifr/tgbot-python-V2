import sys
import logging
import subprocess
import util.module
from util.help import Help
from telegram import Update, Message
from telegram.ext import ContextTypes, CommandHandler, Application

SAVED_MESSAGE_CHAT_ID = -1001607510711
log: logging.Logger = logging.getLogger(__name__)


class ModuleMetadata(util.module.ModuleMetadata):
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
