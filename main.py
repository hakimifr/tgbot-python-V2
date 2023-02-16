#!/usr/bin/env python3

import logging
logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    level=logging.INFO,
                    filename="bot.log")

from typing import Any
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    CallbackContext
)
from api_token import TOKEN
from util.help import Help

import modules.core
import modules.misc
import modules.help
import modules.rm6785
import modules.toys
import modules.blocker
import modules.log
import modules.updater
import modules.archive

# After these modules registers their help, we can update telegram commands and description.
if Help.cmd_update_pending:
    Help.update_bot_cmd()

# TODO: Implement these modules (ref: github.com/Hakimi0804/tgbot-fish)
# import modules.spam_protect     # Prevent spammers in groups
# import modules.moderation       # /ban, /kick, etc
# import modules.komaru           # Pranaya's komaru GIFs channel management
# import modules.toys             # Useless stuffs for fun, e.g. /shuf, etc

app = ApplicationBuilder().token(TOKEN) \
                          .post_init(modules.updater.finish_update) \
                          .build()


async def callback(update: Update, context: CallbackContext) -> None:
    if update.callback_query.data == f"{modules.updater.name}:confirm_update":
        await modules.updater.confirm_update(update, context)


app.add_handler(CallbackQueryHandler(callback))

app.add_handler(CommandHandler("start", modules.core.start))
app.add_handler(CommandHandler("neofetch", modules.misc.neofetch))
app.add_handler(CommandHandler("magisk", modules.misc.magisk))
app.add_handler(CommandHandler("save", modules.core.save))
app.add_handler(CommandHandler("help", modules.help.bot_help))
app.add_handler(CommandHandler("approve", modules.rm6785.approve))
app.add_handler(CommandHandler("disapprove", modules.rm6785.disapprove))
app.add_handler(CommandHandler("post", modules.rm6785.post))
app.add_handler(CommandHandler("sticker", modules.rm6785.sticker))
app.add_handler(CommandHandler("authorize", modules.rm6785.authorize))
app.add_handler(CommandHandler("deauthorize", modules.rm6785.deauthorize))
app.add_handler(CommandHandler("listauth", modules.rm6785.listauth))
app.add_handler(CommandHandler("gay", modules.toys.random_percentage))
app.add_handler(CommandHandler("sexy", modules.toys.random_percentage))
app.add_handler(CommandHandler("shuffle", modules.toys.shuffle))

# Added by Pratham :sunglasses:
app.add_handler(CommandHandler("insert", modules.toys.insert))
app.add_handler(CommandHandler("add_words", modules.toys.add_words))
app.add_handler(CommandHandler("remove_words", modules.toys.remove_words))
app.add_handler(CommandHandler("reset_words", modules.toys.reset_words))

app.add_handler(MessageHandler(filters.Regex(r"^\.\+1"), modules.rm6785.approve))
app.add_handler(MessageHandler(filters.Regex(r"^\.-1"), modules.rm6785.disapprove))
app.add_handler(MessageHandler(filters.Regex(r"(?i)^\.post"), modules.rm6785.post))
app.add_handler(MessageHandler(filters.Regex(r"(?i)^\.sticker"), modules.rm6785.sticker))
app.add_handler(MessageHandler(filters.Regex(r"(?i)^\.auth"), modules.rm6785.authorize))
app.add_handler(MessageHandler(filters.Regex(r"(?i)^\.deauth"), modules.rm6785.deauthorize))

app.add_handler(CommandHandler("block", modules.blocker.block_unblock))
app.add_handler(CommandHandler("unblock", modules.blocker.block_unblock))
app.add_handler(CommandHandler("gblock", modules.blocker.gblock_gunblock))
app.add_handler(CommandHandler("gunblock", modules.blocker.gblock_gunblock))
app.add_handler(CommandHandler("listblocklist", modules.blocker.list_blocklist))
app.add_handler(MessageHandler(filters.Sticker.ALL, modules.blocker.blocker))
app.add_handler(MessageHandler(filters.ANIMATION, modules.blocker.blocker))

app.add_handler(CommandHandler("getlog", modules.log.get_log))

app.add_handler(CommandHandler("update", modules.updater.update))

app.add_handler(CommandHandler("unzip", modules.archive.unzip))
app.add_handler(CommandHandler("unzipl", modules.archive.unzip))

app.run_polling()
