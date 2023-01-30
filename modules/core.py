import sys
import logging
import subprocess
from util.help import Help
from telegram import Update
from telegram.ext import ContextTypes

SAVED_MESSAGE_CHAT_ID = -1001607510711
log = logging.getLogger("modules.core")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("A bot written in Python3, by @Hakimi0804.")


async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != 1024853832:
        log.debug("/save was not sent by owner, ignoring")
        return

    if update.message.reply_to_message is None:
        await update.message.reply_text("You must reply to as message.")
    else:
        ret = await update.message.reply_text("Forwarding...")
        await update.message.reply_to_message.forward(SAVED_MESSAGE_CHAT_ID)
        await ret.edit_text("Message forwarded")


Help.register_help("start", "Show bot's about.")
Help.register_help("save", "Forward message to saving group")
