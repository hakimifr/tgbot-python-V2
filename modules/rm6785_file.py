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

# Based on https://github.com/AgentFabulous/mtk-expdb-extract
def extract_expdb(expdb, out):
    f = open(expdb, 'r', encoding='ISO-8859-1')
    lines = f.readlines()
    dumps = []
    dump = {
        'pl_lk': [],
    }

    for line in lines:
        if "Preloader Start" in line:
            if dump['pl_lk']:
                dumps.append(dump)
            dump = {'pl_lk': []}
        dump['pl_lk'].append(line)

    pl_lk_stripped = [i.replace('\x00', '') for i in dumps[-1]['pl_lk']]

    with open(out, 'w', encoding='ISO-8859-1') as f:
        f.writelines(''.join(pl_lk_stripped))

class ModuleMetadata(module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(MessageHandler(filters.Document.ALL, expdbreader))


async def expdbreader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("Running")
    log.info(f"File name is: {update.message.document.file_name}")
    log.info(f"File size is: {update.message.document.file_size}")

    expdb_tempf: NamedTemporaryFile = NamedTemporaryFile()
    out_tempf: NamedTemporaryFile = NamedTemporaryFile()
    if not re.match(r"expdb.*", update.message.document.file_name):
        return
    if update.effective_chat.id != RM6785_DEVELOPMENT_CHAT_ID:
        return

    # Download the file
    message = await update.message.reply_text("expdb!!, Downloading")
    file: telegram.File = await update.message.document.get_file()
    await file.download_to_drive(custom_path=expdb_tempf.name)

    extract_expdb(expdb_tempf.name, out_tempf.name)
    await message.reply_document(out_tempf.name, caption="Trimmed latest dump")

    expdb_tempf.close()
    out_tempf.close()
    assert expdb_tempf.closed
    assert out_tempf.closed
