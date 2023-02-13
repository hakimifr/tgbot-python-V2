import logging
import telegram.error
from time import sleep
from os import system, execv
from telegram import Update, Message, InlineKeyboardMarkup, InlineKeyboardButton
from util.help import Help
from util.config import Config
from telegram.ext import CallbackContext, ContextTypes, Application
from modules.rm6785 import RM6785_MASTER_USER
log: logging.Logger = logging.getLogger("modules.updater")
config: Config = Config("updater.json")
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


async def finish_update(app: Application) -> None:
    if not config.config.get("was_updated", False):
        log.info("Bot was not updated")
        return

    await app.bot.edit_message_text("Bot restarted",
                                    chat_id=config.config["chat_id"],
                                    message_id=config.config["message_id"])

    log.info("Bot was updated")
    config.config = {}
    config.write_config()


async def update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in RM6785_MASTER_USER:
        await update.message.reply_text("You're not allowed to do this.")
        return

    keyboard: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton("Confirm update", callback_data="updater_confirm")
        ]
    ]
    await update.message.reply_text("Press this button to confirm",
                                        reply_markup=InlineKeyboardMarkup(keyboard)
                                    )


async def confirm_update(update: Update, context: CallbackContext) -> None:
    if update.callback_query.from_user.id not in RM6785_MASTER_USER:
        await update.callback_query.edit_message_text(f"User {update.callback_query.from_user.name} is "
                                          "not allowed to use this.")
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

    execv("/usr/bin/python3", ["/usr/bin/python3", "main.py"])


Help.register_help("update", "Update and restart the bot.")
