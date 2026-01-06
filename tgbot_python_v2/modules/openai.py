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

import logging
import os
import time

from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import tgbot_python_v2.util.module
from tgbot_python_v2.util.config import Config
from tgbot_python_v2.util.help import Help

log: logging.Logger = logging.getLogger(__name__)
RESTRICTED_CHATS_KEY: str = "restricted_chats"
LIMIT_IN_SEC: int = 75

MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class ModuleMetadata(tgbot_python_v2.util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("gpt3", gpt3, block=False))


OPENAI_API_KEY: str | None
try:
    from api_token import OPENAI_API_KEY as OPENAI_API_KEY  # type: ignore
except ImportError:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

API_KEY_OK: bool = bool(OPENAI_API_KEY)
if not API_KEY_OK:
    log.error("Cannot get OpenAI api key; module will be disabled.")

aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)
config: Config = Config("openai.json")

if not config.config.get(RESTRICTED_CHATS_KEY):
    config.config[RESTRICTED_CHATS_KEY] = {}
    config.write_config()


def check_key(function):
    async def wrapper(*arg, **kwargs):
        if API_KEY_OK:
            await function(*arg, **kwargs)
        else:
            log.error("Module was triggered, but token is not available")

    return wrapper


@check_key
async def gpt3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if timestamp := config.config[RESTRICTED_CHATS_KEY].get(str(update.message.chat_id)):
        if time.time() - timestamp < LIMIT_IN_SEC:
            await update.message.reply_text(
                f"Please wait for a few mins before trying again.\nCurrently limit is set to: {LIMIT_IN_SEC}s"
            )
            return

    msg = await update.message.reply_text("Generating response...")

    if not context.args:
        await msg.edit_text("Give some text sir")
        return

    try:
        response = await aclient.responses.create(
            model=MODEL,
            input=" ".join(context.args),
        )
    except Exception as e:
        log.error(e)
        await msg.edit_text(f"{e}")
        return

    await msg.edit_text(response.output_text + f"\n\n---Debug---\nmodel={MODEL}")
    config.config[RESTRICTED_CHATS_KEY].update({str(update.message.chat_id): time.time()})


Help.register_help("gpt3", "Generate an OpenAI response")
