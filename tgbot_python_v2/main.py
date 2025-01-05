#!/usr/bin/env python3

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

import os
import time
import logging
import tgbot_python_v2.util.logging

from importlib import import_module
from pathlib import Path

from tgbot_python_v2 import MODULE_DIR
from tgbot_python_v2.util.module import ModuleMetadata

log = logging.getLogger(__name__)

from telegram import Update
from telegram.error import TimedOut
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    CallbackContext
)

try:
    from api_token import TOKEN
except ImportError:
    if not (TOKEN := os.getenv("BOT_TOKEN")):
        log.critical("Cannot get bot token.")
        raise RuntimeError("Cannot get bot token either from api_token "
                           "file or environment variable.")
Path(".token").write_text(TOKEN)

from tgbot_python_v2.util.help import Help

log.info("Starting bot startup timer")
import_start_time = time.time()

import tgbot_python_v2.modules.updater

# TODO: Implement these modules (ref: github.com/Hakimi0804/tgbot-fish)
# import tgbot_python_v2.modules.spam_protect     # Prevent spammers in groups
# import tgbot_python_v2.modules.moderation       # /ban, /kick, etc
# import tgbot_python_v2.modules.komaru           # Pranaya's komaru GIFs channel management

app = ApplicationBuilder().token(TOKEN) \
                          .post_init(tgbot_python_v2.modules.updater.finish_update) \
                          .build()


async def callback(update: Update, context: CallbackContext) -> None:
    await tgbot_python_v2.modules.updater.confirm_update(update, context)


app.add_handler(CallbackQueryHandler(callback, pattern=lambda data: data == f"{modules.updater.name}:confirm_update",
                                     block=False))

# Load modules
mdls = tuple(Path(f"{MODULE_DIR}/modules").glob("*.py"))
log.info(f"Modules found: {mdls}")
for mdl in mdls:
    try:
        mod: object = import_module("tgbot_python_v2.modules." + mdl.name.removesuffix(".py"))
    except Exception as e:
        log.error(f"failed to import module '{mdl.name}', it will not be loaded at all.")
        log.error(f"error was: {e}")
        continue

    log.info(f"Loading module '{mdl}'")
    if not getattr(mod, "ModuleMetadata", None):
        log.error(f"Failure loading module '{mdl}', ModuleMetadata not detected.")
        continue

    if not issubclass(mod.ModuleMetadata, ModuleMetadata):
        log.error(f"ModuleMetadata of module '{mdl}' is not a subclass of tgbot_python_v2.util.module.ModuleMetadata")
        log.error(f"Refusing to load module '{mdl}'")
        continue

    log.debug(f"Running setup_module() for module '{mdl}'")
    try:
        mod.ModuleMetadata.setup_module(app)
        log.debug("setup_module() finished.")
    except Exception as e:
        log.warning(f"Error while running setup_module() for module '{mdl}', module may not work properly.")
        log.warning(f"More info: {e}")


# After these modules registers their help, we can update telegram commands and description.
log.info("Updating bot commands...")
if Help.cmd_update_pending:
    try:
        Help.update_bot_cmd()
        log.info("Command update successful")
    except TimedOut:
        # Retry one more time because railway moment
        try:
            Help.update_bot_cmd()
            log.info("Command update successful")
        except TimedOut as e:
            log.error(f"Failed to update bot command, cause: {e}")

log.info(f"Bot startup took {(time.time() - import_start_time):.1f}s")
app.run_polling()
