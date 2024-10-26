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

from pytz import timezone
from datetime import datetime
from calendar import monthrange
from pathlib import Path
import logging

import util.module
from util.config import Config
from util.help import Help
from telegram import Update, Document, Message
from telegram.ext import CommandHandler, Application, ContextTypes

log: logging.Logger = logging.getLogger(__name__)
config: Config = Config("menu_db.json")
config.write_config()
# Expected json structure
# {"1": [file_id, unique_id]}


class ModuleMetadata(util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("menu", menu, block=False))
        app.add_handler(CommandHandler("tomorrow", tomorrow, block=False))


def get_datetime() -> datetime:
    return datetime.now(timezone("Asia/Kuala_Lumpur"))


async def recycle_if_possible(day: str, update: Update) -> None:
    """Returns whether it is possible"""
    if config.config.get(day):
        log.info("Recycling existing file id")
        await update.message.reply_photo(Document(*config.config.get(day)))  # type: ignore
    else:
        message: Message = await update.message.reply_photo(f"menus/{day}.png")
        add_id(day, message)


def add_id(day: str, message: Message) -> None:
    config.config.update({day: [message.document.file_id, message.document.file_unique_id]})


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # get_datetime().day
    day: str = str(get_datetime().day)
    menu_file: Path = Path(f"menus/{day}.png")

    if not menu_file.exists:
        await update.message.reply_text("Internal error occured")
        log.error(f"File {menu_file.absolute()} does not exist!")
    else:
        await recycle_if_possible(day, update)


async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _, max_day_in_this_month = monthrange(get_datetime().year, get_datetime().month)
    day: str = str(get_datetime().day + 1)

    if int(day) > max_day_in_this_month:
        day = "1"

    await recycle_if_possible(day, update)


Help.register_help("menu", "Return today's menu")
Help.register_help("tomorrow", "Return tomorrow's menu")
