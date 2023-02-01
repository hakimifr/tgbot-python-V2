import logging
from pathlib import Path
from telegram import Update
from util.help import Help
from telegram.ext import ContextTypes
from modules.rm6785 import RM6785_MASTER_USER
log: logging.Logger = logging.getLogger("modules.log")


async def get_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if file exist
    if not Path("bot.log").is_file():
        log.error("Log file does not exist")
        return

    # Allow only master users for retrieving logs
    if update.message.from_user.id not in RM6785_MASTER_USER:
        await update.message.reply_text("You're not allowed to do this")
        return
    
    await update.message.reply_document(Path("bot.log"))


Help.register_help("getlog", "Retrieve bot log")
