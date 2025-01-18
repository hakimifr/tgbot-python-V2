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

import inspect

from telegram import BotCommand, Update
from telegram.ext import Application, BaseHandler, CommandHandler, ContextTypes
from telegram.helpers import escape_markdown

from tgbot_python_v2.util import module
from tgbot_python_v2.util.help import Help


class ModuleMetadata(module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("get_source", get_command_source, block=False))


async def get_command_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not 0 < len(context.args) < 2:
        await update.message.reply_text("Give a command to get source.")
        return

    target_command = context.args[0]

    handlers_dict: dict[BaseHandler, list[BaseHandler]] = context.application.handlers
    for handlers in handlers_dict.values():
        for handler in handlers:
            if not isinstance(handler, CommandHandler):
                continue

            if target_command in handler.commands:
                await update.message.reply_text(
                    "```python\n" + escape_markdown(inspect.getsource(handler.callback), version=2) + "\n```",
                    parse_mode="MarkdownV2",
                )
                return

    await update.message.reply_text("Error: command does not exist.")


Help.register_help("get_source", "Get a source code for a command.")
