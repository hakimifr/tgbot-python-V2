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

import logging
import tgbot_python_v2.util.module
from pathlib import Path
from telegram import Update
from tgbot_python_v2.util.help import Help
from telegram.ext import ContextTypes, CommandHandler, Application
from tgbot_python_v2.modules.rm6785 import RM6785_MASTER_USER
log: logging.Logger = logging.getLogger(__name__)
TOKEN: str = Path(".token").read_text()


class ModuleMetadata(tgbot_python_v2.util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("getlog", get_log, block=False))


async def get_log(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log_file: Path = Path("bot.log")
    tmp_file: Path = Path("tmp.log")

    # Check if file exist
    if not log_file.is_file():
        log.error("Log file does not exist")
        return

    # Truncate token from log
    tmp_file.write_text(log_file.read_text().replace(TOKEN, "[token redacted]"))

    # Allow only master users for retrieving logs
    if update.message.from_user.id not in RM6785_MASTER_USER:
        await update.message.reply_text("You're not allowed to do this")
        return
    
    await update.message.reply_document(tmp_file)

    tmp_file.unlink()


Help.register_help("getlog", "Retrieve bot log")
