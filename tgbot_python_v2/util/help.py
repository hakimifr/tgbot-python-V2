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

import os
import asyncio
import logging
from telegram import Bot, BotCommand
log: logging.Logger = logging.getLogger(__name__)

try:
    from api_token import TOKEN
except ImportError:
    if not (TOKEN := os.getenv("BOT_TOKEN")):
        log.critical("Failed to get bot token")

class Help:
    """Class for storing help strings. Class methods only."""
    bot: Bot = Bot(TOKEN)
    loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
    help_messages: dict = {}
    cmd_update_pending: bool = False

    @classmethod
    def update_bot_cmd(cls):
        """Update bot cmds in Telegram, eliminating the need to do it manually through @BotFather."""
        # commands: list[BotCommand] = []
        # for cmd in cls.help_messages.keys():
        #     commands.append(BotCommand(cmd, cls.help_messages.get(cmd)))
        commands: list[BotCommand] = [BotCommand(cmd, cls.help_messages.get(cmd, "")) for cmd in cls.help_messages.keys()]

        try:
            log.info("Updating bot cmd")
            cls.loop.run_until_complete(cls.bot.delete_my_commands())
            cls.loop.run_until_complete(cls.bot.set_my_commands(commands))

            cls.cmd_update_pending = False
        except Exception as e:
            log.error("Failed to update bot cmd:\n" + str(e))

    @classmethod
    def register_help(cls, command: str, help_string: str) -> None:
        """Register a unique help string for a command."""
        if cls.help_messages.get(command) is None:
            log.info(f"Registering help for command {command}")
            cls.help_messages[command] = help_string
            cls.cmd_update_pending = True
        else:
            log.warning(f"Command {command} already have help message set!")

    @classmethod
    def remove_help(cls, command: str) -> None:
        """Remove a help string for a command."""
        if cls.help_messages.get(command) is not None:
            log.info(f"Removing help string for command {command}")
            del cls.help_messages[command]
            cls.cmd_update_pending = True
        else:
            log.warning(f"No help message from {command} to be removed!")

    @classmethod
    def get_help(cls, commands: list = None) -> str:
        """Return help string of all commands combined.
        e.g.:
        /foo -> bar
        /baz -> bat"""
        if commands is None:
            commands = []

        help_message = ""
        for cmd in cls.help_messages.keys():
            # help_message += "/" + cmd + " -> " + cls.help_messages[cmd] + '\n'
            help_message += f"/{cmd} -> {cls.help_messages[cmd]}\n"

        return help_message
