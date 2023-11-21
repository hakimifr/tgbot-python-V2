import sys
import logging
import requests
import subprocess
import util.module
from util.help import Help
from util.config import Config
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, Application

main_log: logging.Logger = logging.getLogger(__file__)
auto_forward_state: bool = True


class ModuleMetadata(util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("neofetch", neofetch))
        app.add_handler(CommandHandler("magisk", magisk))
        app.add_handler(CommandHandler("toggleautoforward", toggle_auto_forward))
        app.add_handler(MessageHandler(filters.Regex(r"(?i)#Pratham"), auto_forward))


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


async def toggle_auto_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_forward_state
    log = main_log.getChild("toggle_auto_forward")
    toggle_user_whitelist = [1583181351, 1024853832]

    if update.message.from_user.id not in toggle_user_whitelist:
        await update.message.reply_text("You're not allowed to use this command.")
        return

    log.info(f"Changing auto-forward enabled state from {auto_forward_state} to {not auto_forward_state}")
    auto_forward_state = not auto_forward_state
    await update.message.reply_text(f"Auto-forward state changed to enabled: {auto_forward_state}")


async def auto_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log = main_log.getChild("auto_forward")
    target_group_id: int = -1001511914394
    user_id = 1583181351

    if not auto_forward_state:
        log.info("Returning as auto-forward is disabled")
        return

    if update.message.chat_id != target_group_id:
        log.info("Not target chat, skip forwarding")
        return

    await update.message.forward(user_id)
    await update.message.reply_text("Message forwarded to Pratham")


Help.register_help("magisk", "Get the links to latest magisk apks.")
Help.register_help("neofetch", "Run neofetch")
Help.register_help("toggleautoforward", "(For Pratham) Toggle automatic forwarding")
