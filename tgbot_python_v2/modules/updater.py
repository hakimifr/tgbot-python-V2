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

import atexit
import logging
import os
import sys
from os import execve, system
from time import sleep

import telegram.error
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import Application, CallbackContext, CommandHandler, ContextTypes

import tgbot_python_v2.util.module
from tgbot_python_v2.modules.rm6785 import RM6785_MASTER_USER
from tgbot_python_v2.util.config import Config
from tgbot_python_v2.util.help import Help

log: logging.Logger = logging.getLogger(__name__)
config: Config = Config("updater.json")
name: str = __name__
"""structure of updater.json:
{
    should_finish_restart: bool,
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


class ModuleMetadata(tgbot_python_v2.util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("update", update))
        app.add_handler(CommandHandler("restart", restart))


async def finish_update(app: Application) -> None:
    if not config.config.get("should_finish_restart", False):
        log.info("Nothing to do")
        return

    if config.config.get("was_updated", False):
        log.info("** Bot was updated")
    else:
        log.info("** Bot was not updated: Restart for other reason")

    try:
        await app.bot.edit_message_text(
            "Bot restarted",
            chat_id=config.config["chat_id"],
            message_id=config.config["message_id"],
        )
    except telegram.error.BadRequest as e:
        log.error("Failed to edit update message, perhaps it's already edited?")
        log.error("Logging traceback.")
        log.error(f"{e}")

    config.config = {}
    config.write_config()


async def update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in RM6785_MASTER_USER:
        await update.message.reply_text("You're not allowed to do this.")
        return

    keyboard: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton("Confirm update", callback_data=f"{__name__}:confirm_update")]
    ]
    await update.message.reply_text("Press this button to confirm", reply_markup=InlineKeyboardMarkup(keyboard))


async def confirm_update(update: Update, context: CallbackContext) -> None:
    if update.callback_query.from_user.id not in RM6785_MASTER_USER:
        await update.callback_query.answer(text="You're not allowed to do this.", show_alert=True)
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
        "should_finish_restart": True,
        "was_updated": True,
        "chat_id": update.callback_query.message.chat_id,
        "message_id": update.callback_query.message.id,
    }
    config.write_config()

    # Make sure the bot does not restart indefinitely
    await context.application.updater._stop_polling()
    try:
        await update.get_bot().get_updates(offset=update.update_id + 1)
    except telegram.error.TimedOut:
        pass

    atexit._run_exitfuncs()
    execve(sys.executable, [sys.executable, *sys.argv], os.environ)


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in RM6785_MASTER_USER:
        await update.message.reply_text("You're not allowed to use this command")
        return

    message = await update.message.reply_text("Restarting")

    await context.application.updater._stop_polling()
    try:
        await update.get_bot().get_updates(offset=update.update_id + 1)
    except telegram.error.TimedOut:
        pass

    config.config = {
        "should_finish_restart": True,
        "was_updated": False,
        "chat_id": update.message.chat.id,
        "message_id": message.id,
    }
    config.write_config()

    atexit._run_exitfuncs()
    execve(sys.executable, [sys.executable, *sys.argv], os.environ)


Help.register_help("update", "Update and restart the bot.")
Help.register_help("restart", "Restart the bot")
