# SPDX-License-Identifier: GPL-3.0-only
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
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

"""
Module to send message with help strings when requested.
Available methods:

    bot_help(update, context):
        Sends help message.
"""
import logging
import util.module
from util.help import Help
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, Application, CallbackContext, CallbackQueryHandler
log: logging.Logger = logging.getLogger(__name__)


class ModuleMetadata(util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("help", bot_help, block=False))
        app.add_handler(CallbackQueryHandler(callback_handler, block=False,
                                             pattern=lambda data: data in [f"{__name__}:shrink", f"{__name__}:expand"]))


async def callback_handler(update: Update, context: CallbackContext):
    log.info(f"Callback data received: {update.callback_query.data}")
    if update.callback_query.data not in [f"{__name__}:expand", f"{__name__}:shrink"]:
        return

    if update.callback_query.data == f"{__name__}:expand":
        markup: InlineKeyboardMarkup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Shrink help", callback_data=f"{__name__}:shrink")]]
        )
        await update.callback_query.edit_message_text(Help.get_help(), reply_markup=markup)
    elif update.callback_query.data == f"{__name__}:shrink":
        markup: InlineKeyboardMarkup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Expand help", callback_data=f"{__name__}:expand")]]
        )
        await update.callback_query.edit_message_text("\n".join(Help.get_help().split("\n")[0:5]) + "\n[..more]",
                                                      reply_markup=markup)
    else:
        raise ValueError(f"'{update.callback_query.data}' was not expected here")


async def bot_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(Help.get_help().split("\n")) > 5:
        markup: InlineKeyboardMarkup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Expand help", callback_data=f"{__name__}:expand")]]
        )
        await update.message.reply_text("\n".join(Help.get_help().split("\n")[0:5]) + "\n[..more]", reply_markup=markup)
    else:
        await update.message.reply_text(Help.get_help())

Help.register_help("help", "Show help message.")
