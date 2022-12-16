"""
Modules with useless commands, just for fun.
Available methods:

    random_percentage(update, context)
        returns random gayness/sexiness percentage.

    shuffle(update.context)
        shuffle a sentence.
"""

import logging
import random
import re
from util.help import Help
from util.config import Config
from telegram import Update
from telegram.ext import ContextTypes
log = logging.getLogger("toys")


async def random_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    type_: str
    user: str
    rand_percent: int

    # Check type, whether sexy or gay
    if re.match(r"^/gay", update.message.text):
        type_ = "gay"
    else:
        type_ = "sexy"
    ret = await update.message.reply_text(f"Calculating {type_}ness...")

    if type_ == "gay":
        rand_percent = random.randint(10, 100)
    else:
        rand_percent = random.randint(-50, 100)

    if update.message.reply_to_message is not None:
        user = update.message.reply_to_message.from_user.first_name
    else:
        user = update.message.from_user.first_name

    await ret.edit_text(f"{user} is {rand_percent}% {type_}")


async def shuffle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message is None:
        await update.message.reply_text("You must reply to a message.")
        return

    ret = await update.message.reply_text("Shuffling...")
    text: list[str] = update.message.reply_to_message.text.split(" ")
    random.shuffle(text)

    await ret.edit_text(" ".join(text))


Help.register_help("gay", "Return gayness level of you/replied user.")
Help.register_help("sexy", "Return sexiness level of you/replied user.")
Help.register_help("shuffle", "Shuffle replied message.")
