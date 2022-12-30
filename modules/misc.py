import sys
import subprocess
from util.help import Help
from telegram import Update
from telegram.ext import ContextTypes


async def neofetch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    output = subprocess.check_output(["neofetch", "--stdout"] + context.args)
    await update.message.reply_text(output.decode(sys.stdout.encoding))


Help.register_help("neofetch", "Run neofetch")
