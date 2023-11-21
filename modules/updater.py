import os
import sys
import logging
import telegram.error
import util.module

from time import sleep
from os import system, execve
from telegram import Update, Message, InlineKeyboardMarkup, InlineKeyboardButton
from util.help import Help
from util.config import Config
from telegram.ext import CallbackContext, CommandHandler, ContextTypes, Application
from modules.rm6785 import RM6785_MASTER_USER
log: logging.Logger = logging.getLogger(__name__)
config: Config = Config("updater.json")
name: str = __name__
"""structure of updater.json:
{
    was_updated: bool,
    chat_id: int,
    message_id: int
}

was_updated: bool
    will be used by finish_update() to check whether the
    bot was restarted. when true, the 'Restarting bot' message
    will be edited.

chat_id: int
    chat_id of which the 'Restarting bot' message was sent

message_id: int
    message_id of the 'Restarting bot' message
"""


class ModuleMetadata(util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("update", update))


async def finish_update(app: Application) -> None:
    if not config.config.get("was_updated", False):
        log.info("Bot was not updated")
        return

    try:
        await app.bot.edit_message_text("Bot restarted",
                                        chat_id=config.config["chat_id"],
                                        message_id=config.config["message_id"])
    except telegram.error.BadRequest as e:
        log.error("Failed to edit update message, perhaps it's already edited?")
        log.error("Logging traceback.")
        log.error(f"{e}")

    log.info("Bot was updated")
    config.config = {}
    config.write_config()


async def update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in RM6785_MASTER_USER:
        await update.message.reply_text("You're not allowed to do this.")
        return

    keyboard: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton("Confirm update", callback_data=f"{__name__}:confirm_update")
        ]
    ]
    await update.message.reply_text("Press this button to confirm",
                                        reply_markup=InlineKeyboardMarkup(keyboard)
                                    )


async def confirm_update(update: Update, context: CallbackContext) -> None:
    if update.callback_query.from_user.id not in RM6785_MASTER_USER:
        await update.callback_query.answer(text="You're not allowed to do this.",
                                           show_alert=True)
        return

    await update_start(update, context)


async def update_start(update: Update, context: CallbackContext) -> None:
    log.info("Updating bot")
    retval: int = system("git pull --rebase")
    if retval != 0:
        log.error("git pull failed")
        await update.callback_query.edit_message_text("Failed to git pull")
        return

    await update.callback_query.edit_message_text("Updating bot")
    log.info("Restarting bot")

    config.config = {
        "was_updated": True,
        "chat_id": update.callback_query.message.chat_id,
        "message_id": update.callback_query.message.id
    }
    config.write_config()

    # Make sure the bot does not restart indefinitely
    await context.application.updater._stop_polling()
    try:
        await update.get_bot().get_updates(offset=update.update_id + 1)
    except telegram.error.TimedOut:
        pass

    execve(sys.executable, [sys.executable, *sys.argv], os.environ)


Help.register_help("update", "Update and restart the bot.")
