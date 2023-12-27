import re
import string
import logging

import util.module as module

import telegram

from typing import Generator
from tempfile import NamedTemporaryFile

from modules.rm6785 import RM6785_DEVELOPMENT_CHAT_ID

from telegram import Update
from telegram.ext import ContextTypes, Application, MessageHandler, filters

log: logging.Logger = logging.getLogger(__name__)


# https://stackoverflow.com/questions/17195924/python-equivalent-of-unix-strings-utility
def strings(filename, min=4) -> Generator:
    with open(filename, errors="ignore") as f:  # Python 3.x
        result = ""
        for c in f.read():
            if c in string.printable:
                result += c
                continue
            if len(result) >= min:
                yield result
            result = ""
        if len(result) >= min:  # catch result at EOF
            yield result


class ModuleMetadata(module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(MessageHandler(filters.Document.ALL, expdbreader))


async def expdbreader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("Running")
    log.info(f"File name is: {update.message.document.file_name}")
    log.info(f"File size is: {update.message.document.file_size}")

    pattern = r"TP|DISP"
    trigger_file_names: list[str] = ["expdb"]
    expdb_tempf: NamedTemporaryFile = NamedTemporaryFile()
    strings_tempf: NamedTemporaryFile = NamedTemporaryFile()
    grepped_tempf: NamedTemporaryFile = NamedTemporaryFile()
    if update.message.document.file_name not in trigger_file_names:
        return
    if update.effective_chat.id != RM6785_DEVELOPMENT_CHAT_ID:
        return

    # Download the file
    message = await update.message.reply_text("expdb!!, Downloading")
    file: telegram.File = await update.message.document.get_file()
    await file.download_to_drive(custom_path=expdb_tempf.name)

    with open(strings_tempf.name, "w") as f:
        f.write("\n".join(strings(expdb_tempf.name)))
    await message.reply_document(strings_tempf, caption="strings-ed.")

    await message.edit_text(f"grepping, pattern: '{pattern}'")
    lines: list[str] = []
    for line in strings(expdb_tempf.name):
        new_lines = line.split("\n")
        lines = [*lines, *new_lines]

    grepped: Generator[list[str]] = filter(lambda line: re.search(pattern, line), lines)

    with open(grepped_tempf.name, "w") as f:
        f.write("\n".join(grepped))

    await message.edit_text("Done, uploading")
    await message.reply_document(grepped_tempf.name, caption=f"Grepped with pattern: '{pattern}'")
    await message.edit_text("Done")

    expdb_tempf.close()
    grepped_tempf.close()

    assert expdb_tempf.closed
    assert grepped_tempf.closed
