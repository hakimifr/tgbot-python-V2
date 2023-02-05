import logging
import telegram
import telegram.error

from pathlib import Path
from util.help import Help
from zipfile import ZipFile, is_zipfile
from tempfile import TemporaryDirectory, _TemporaryFileWrapper, NamedTemporaryFile
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import FileSizeLimit
log: logging.Logger = logging.getLogger("modules.archive")


async def extract_zip(file: telegram.File, update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> None:
    message: telegram.Message = await update.message.reply_text("Processing file")
    tmpdir: TemporaryDirectory = TemporaryDirectory()
    tmpfile: _TemporaryFileWrapper = NamedTemporaryFile()

    if file.file_size > FileSizeLimit.FILESIZE_DOWNLOAD:
        await message.edit_text("Sorry, bot cannot download file larger "
                                f"than {FileSizeLimit.FILESIZE_DOWNLOAD}")
        return

    zipfile: Path = await file.download_to_drive(custom_path=tmpfile.name)
    if not is_zipfile(zipfile):
        await message.edit_text("Not a valid zip file.")
        return

    zip: ZipFile = ZipFile(zipfile)
    zip.extractall(path=tmpdir.name)
    for entry in zip.namelist():
        if Path(entry).joinpath(tmpdir.name).resolve().exists():
            log.info(f"OK: {entry}")

    oversized_files: list[str] = []
    for entry in zip.namelist():
        if (Path(entry).joinpath(tmpdir.name).stat().st_size
                > FileSizeLimit.FILESIZE_UPLOAD):
            log.warning(f"File {file} exceed Telegram upload size "
                        f"limit of {FileSizeLimit.FILESIZE_UPLOAD}")
            oversized_files.append(entry)
            continue

        if Path(tmpdir.name).joinpath(entry).is_dir():
            log.info(f"Will not upload directory: '{entry}'")
            continue

        try:
            log.info(f"Uploading {entry}")
            await update.message.reply_document(
                Path(tmpdir.name).joinpath(entry),
                caption=entry
            )
        except telegram.error.TelegramError:
            log.error(f"Failed to upload {entry}")

    text: str = "Finished unzipping.\n"
    if len(oversized_files) > 0:
        text += "Cannot send the following files because they " \
                "exceed the max size:\n"
        for ofile in oversized_files:
            text += f"- {ofile}\n"

    await message.edit_text(text)

    tmpdir.cleanup()
    tmpfile.close()


async def unzip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message.document is None:
        await update.message.reply_text("Please reply to a file.")
        return

    file: telegram.File = await update.message.reply_to_message.document.get_file()
    await extract_zip(file, update, context)


Help.register_help("unzip", "Unzip to replied file")
