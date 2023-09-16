import sys
import logging
import requests
import subprocess
from util.help import Help
from telegram import Update
from telegram.ext import ContextTypes

log: logging.Logger = logging.getLogger(__file__)


async def neofetch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    output: bytes = subprocess.check_output(["bin/neofetch", "--stdout"] + context.args)
    await update.message.reply_text(output.decode(sys.stdout.encoding))


async def magisk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    resp: requests.Response = requests.get("https://api.github.com/repos/topjohnwu/Magisk/releases/latest")
    resp_obj: dict = resp.json()
    assets: dict = resp_obj.get("assets")[0]

    dl_stable: str = assets.get("browser_download_url")
    dl_canary: str = "https://raw.githubusercontent.com/topjohnwu/magisk-files/canary/app-debug.apk"

    await update.message.reply_markdown_v2(f"[Latest stable]({dl_stable})\n[Latest canary]({dl_canary})")


async def auto_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logg = log.getChild("auto_forward")
    target_group_id: int = -1001511914394
    user_id = 1583181351

    if update.message.chat_id != target_group_id:
        logg.debug("Not target chat, skip forwarding")
        return

    await update.message.forward(user_id)
    await update.message.reply_text("Message forwarded to Pratham")


Help.register_help("magisk", "Get the links to latest magisk apks.")
Help.register_help("neofetch", "Run neofetch")
