# SPDX-License-Identifier: GPL-3.0-only
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright (c) 2024, Firdaus Hakimi <hakimifirdaus944@gmail.com>

import sys
import logging
import requests
import subprocess
import util.module
from util.help import Help
from util.config import Config
from modules.rm6785 import RM6785_CHANNEL_ID
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, Application
from telegram.helpers import escape_markdown

main_log: logging.Logger = logging.getLogger(__file__)
auto_forward_state: bool = False


class ModuleMetadata(util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("neofetch", neofetch, block=False))
        app.add_handler(CommandHandler("magisk", magisk, block=False))
        app.add_handler(CommandHandler("toggleautoforward", toggle_auto_forward, block=False))
        app.add_handler(MessageHandler(filters.Regex(r"(?i)#Pratham"), auto_forward, block=False))
        app.add_handler(MessageHandler(filters.ALL, tyagi_sanitizer, block=False), group=2)


async def neofetch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    output: bytes = subprocess.check_output(["bin/neofetch", "--stdout"] + context.args)
    await update.message.reply_text("```\n"
                                    + escape_markdown(output.decode(sys.stdout.encoding))
                                    + "\n```", parse_mode="MarkdownV2")


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


async def tyagi_sanitizer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != RM6785_CHANNEL_ID:
        return

    if update.channel_post.from_user.id == 712305133:
        await update.channel_post.delete()


Help.register_help("magisk", "Get the links to latest magisk apks.")
Help.register_help("neofetch", "Run neofetch")
Help.register_help("toggleautoforward", "(For Pratham) Toggle automatic forwarding")
