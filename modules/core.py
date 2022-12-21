import sys
import subprocess
from util.help import Help
from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("A bot written in Python3, by @Hakimi0804.")


async def neofetch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    output = subprocess.check_output(["neofetch", "--stdout"] + context.args)
    await update.message.reply_text(output.decode(sys.stdout.encoding))


Help.register_help("start", "Show bot's about.")
Help.register_help("neofetch", "Run neofetch")
