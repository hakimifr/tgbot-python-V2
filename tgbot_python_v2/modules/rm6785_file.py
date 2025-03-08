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
import re
import string
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
from traceback import format_exception
from typing import Generator, cast
from pathlib import Path

import telegram
from telegram import Document, Update
from telegram.constants import FileSizeLimit
from telegram.ext import Application, ContextTypes, MessageHandler, filters

import tgbot_python_v2.util.module as module
from tgbot_python_v2.modules.rm6785 import RM6785_DEVELOPMENT_CHAT_ID

log: logging.Logger = logging.getLogger(__name__)


# Based on https://github.com/AgentFabulous/mtk-expdb-extract
def extract_expdb(expdb, out) -> tuple[bool, Exception | None]:
    f = open(expdb, "r", encoding="ISO-8859-1")
    lines = f.readlines()
    dumps = []
    dump = {
        "pl_lk": [],
    }

    for line in lines:
        if "Preloader Start" in line:
            if dump["pl_lk"]:
                dumps.append(dump)
            dump = {"pl_lk": []}
        dump["pl_lk"].append(line)

    try:
        pl_lk_stripped = [i.replace("\x00", "") for i in dumps[-1]["pl_lk"]]

        with open(out, "w", encoding="ISO-8859-1") as f:
            f.writelines("".join(pl_lk_stripped))

        return (True, None)
    except Exception as e:
        return (False, e)


class ModuleMetadata(module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(MessageHandler(filters.Document.ALL, expdbreader, block=False))


async def expdbreader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # we're already using PTB's filters, there's no way update.message.document
    # will be none, so let's satisfy the type checker
    update.message.document = cast(Document, update.message.document)
    update.message.document.file_name = cast(str, update.message.document.file_name)

    log.info("Running")
    log.info(f"File name is: {update.message.document.file_name}")
    log.info(f"File size is: {update.message.document.file_size}")

    if not re.match(r"expdb.*", update.message.document.file_name):
        return
    if update.effective_chat.id != RM6785_DEVELOPMENT_CHAT_ID:
        return

    # Download the file
    with NamedTemporaryFile() as expdb_tempf, NamedTemporaryFile() as out_tempf:
        message = await update.message.reply_text("Found expdb!!")
        file: telegram.File = await update.message.document.get_file()
        await file.download_to_drive(custom_path=expdb_tempf.name)

        result: tuple[bool, Exception | None] = extract_expdb(expdb_tempf.name, out_tempf.name)

        if not result[0]:
            await message.edit_text(f"Failed to trim the expdb dump because: {''.join(format_exception(result[1]))}")
            return

        if (size := Path(out_tempf.name).stat().st_size) > FileSizeLimit.FILESIZE_UPLOAD:
            await message.edit_text(
                f"expdb trimmed successfully, but the size '{size}' exceeds 50MB!\nunable to upload it."
            )
            return

        await message.edit_text("Successfully trimmed the expdb dump")
        await message.reply_document(out_tempf.name, caption="Trimmed latest dump")
