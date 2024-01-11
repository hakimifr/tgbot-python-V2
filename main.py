#!/usr/bin/env python3

import os
import time
import logging

from importlib import import_module
from pathlib import Path

from util.module import ModuleMetadata

GLOBAL_DEBUG: bool = False
if os.getenv("TGBOT_DEBUG") is not None:
    GLOBAL_DEBUG = True

log_additional_args: dict = {"filename": "bot.log"}
# Print log to stdout if in debug mode
if GLOBAL_DEBUG:
    log_additional_args.clear()

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    level=logging.INFO,
                    **log_additional_args)
log = logging.getLogger(__name__)

import util.config_backuprestore

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

from util.help import Help

log.info("Starting bot startup timer")
import_start_time = time.time()

util.config_backuprestore.fetch_file()

import modules.updater

# TODO: Implement these modules (ref: github.com/Hakimi0804/tgbot-fish)
# import modules.spam_protect     # Prevent spammers in groups
# import modules.moderation       # /ban, /kick, etc
# import modules.komaru           # Pranaya's komaru GIFs channel management

app = ApplicationBuilder().token(TOKEN) \
                          .post_init(modules.updater.finish_update) \
                          .build()


async def callback(update: Update, context: CallbackContext) -> None:
    await modules.updater.confirm_update(update, context)


app.add_handler(CallbackQueryHandler(callback, pattern=lambda data: data == f"{modules.updater.name}:confirm_update",
                                     block=False))

# Load modules
mdls = tuple(Path("modules").glob("*.py"))
log.info(f"Modules found: {mdls}")
for mdl in mdls:
    mod: object = import_module("modules." + mdl.name.removesuffix(".py"))

    log.info(f"Loading module '{mdl}'")
    if not getattr(mod, "ModuleMetadata", None):
        log.error(f"Failure loading module '{mdl}', ModuleMetadata not detected.")
        continue

    if not issubclass(mod.ModuleMetadata, ModuleMetadata):
        log.error(f"ModuleMetadata of module '{mdl}' is not a subclass of util.module.ModuleMetadata")
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
