import sys
import requests
import subprocess
from util.help import Help
from telegram import Update
from telegram.ext import ContextTypes


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


Help.register_help("magisk", "Get the links to latest magisk apks.")
Help.register_help("neofetch", "Run neofetch")
