"""
Module to send message with help strings when requested.
Available methods:

    bot_help(update, context):
        Sends help message.
"""
import logging
import util.module
from util.help import Help
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application
log: logging.Logger = logging.getLogger(__name__)


class ModuleMetadata(util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("help", bot_help))


async def bot_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(Help.get_help())

Help.register_help("help", "Show help message.")
