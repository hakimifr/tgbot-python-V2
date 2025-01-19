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
from pathlib import Path
from pprint import pformat
from tempfile import NamedTemporaryFile, TemporaryDirectory, _TemporaryFileWrapper
from zipfile import ZipFile, is_zipfile

import telegram
import telegram.error
from telegram import Update
from telegram.constants import FileSizeLimit
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.helpers import escape_markdown

import tgbot_python_v2.util.module
from tgbot_python_v2.util.help import Help

log: logging.Logger = logging.getLogger(__name__)


class ModuleMetadata(tgbot_python_v2.util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("unzip", unzip, block=False))
        app.add_handler(CommandHandler("unzipl", unzip, block=False))


async def extract_zip(
    file: telegram.File,
    entry_list: list[str] | None,  # type: ignore
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    just_list: bool = False,
) -> None:
    if entry_list is None:
        entry_list: list[str] = []

    message: telegram.Message = await update.message.reply_text("Processing file")
    tmpdir: TemporaryDirectory = TemporaryDirectory()
    tmpfile: _TemporaryFileWrapper = NamedTemporaryFile()
    extract_all: bool = True
    exist_entry: list[str] = []

    if len(entry_list) > 0:
        extract_all: bool = False

    if file.file_size > FileSizeLimit.FILESIZE_DOWNLOAD:
        await message.edit_text(f"Sorry, bot cannot download file larger than {FileSizeLimit.FILESIZE_DOWNLOAD}")
        tmpfile.close()
        tmpdir.cleanup()
        return

    zipfile: Path = await file.download_to_drive(custom_path=tmpfile.name)
    if not is_zipfile(zipfile):
        await message.edit_text("Not a valid zip file.")
        tmpfile.close()
        tmpdir.cleanup()
        return

    zip: ZipFile = ZipFile(zipfile)
    if just_list:
        await message.edit_text(
            "```python\n" + escape_markdown(pformat(zip.namelist()), version=2) + "\n```",
            parse_mode="MarkdownV2",
        )
        tmpfile.close()
        tmpdir.cleanup()
        return

    if extract_all:
        zip.extractall(path=tmpdir.name)
    else:
        exist_entry: list[str] = [entry for entry in entry_list if entry in zip.namelist()]
        log.info(f"exist_entry: {exist_entry}")
        zip.extractall(path=tmpdir.name, members=exist_entry)

    for entry in zip.namelist():
        if Path(entry).joinpath(tmpdir.name).resolve().exists():
            log.info(f"OK: {entry}")

    oversized_files: list[str] = []

    if extract_all:
        file_to_upload_entry: list[str] = zip.namelist()
    else:
        file_to_upload_entry: list[str] = exist_entry

    for entry in file_to_upload_entry:
        if Path(tmpdir.name).joinpath(entry).stat().st_size > FileSizeLimit.FILESIZE_UPLOAD:
            log.warning(f"File {file} exceed Telegram upload size limit of {FileSizeLimit.FILESIZE_UPLOAD}")
            oversized_files.append(entry)
            continue

        if Path(tmpdir.name).joinpath(entry).is_dir():
            log.info(f"Will not upload directory: '{entry}'")
            continue

        try:
            log.info(f"Uploading {entry}")
            await update.message.reply_document(
                Path(tmpdir.name).joinpath(entry),
                caption="`" + escape_markdown(entry, version=2) + "`",
                parse_mode="MarkdownV2",
            )
        except telegram.error.TelegramError:
            log.error(f"Failed to upload {entry}")

    text: str = "Finished processing.\n"
    if len(oversized_files) > 0:
        text += "Cannot send the following files because they exceed the max size:\n"
        for ofile in oversized_files:
            text += f"- {ofile}\n"

    await message.edit_text(text)

    tmpdir.cleanup()
    tmpfile.close()


async def unzip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.reply_to_message.document is None:
        await update.message.reply_text("Please reply to a file.")
        return

    file: telegram.File = await update.message.reply_to_message.document.get_file()
    if re.match(r"^/unzipl", update.message.text):
        await extract_zip(file, context.args, update, context, just_list=True)
        return

    await extract_zip(file, context.args, update, context)


Help.register_help("unzip", "Unzip to replied file")
Help.register_help("unzipl", "List zip file content")
