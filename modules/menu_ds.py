from pytz import timezone
from datetime import datetime
from calendar import monthrange
from pathlib import Path
import logging

import util.module
from util.config import Config
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


async def recycle_if_possible(day: str, update: Update) -> bool:
    """Returns whether it is possible"""
    if config.config.get(day):
        log.info("Recycling existing file id")
        await update.message.reply_document(Document(*config.config.get(day)))  # type: ignore
        return True

    return False


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
        if not await recycle_if_possible(day, update):
            message = await update.message.reply_document(f"menus/{day}.png")
            add_id(day, message)


async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _, max_day_in_this_month = monthrange(get_datetime().year, get_datetime().month)
    day: str = str(get_datetime().day + 1)

    if int(day) > max_day_in_this_month:
        day = "1"

    if not await recycle_if_possible(day, update):
        message: Message = await update.message.reply_document(f"menus/{day}.png")
        add_id(day, message)
