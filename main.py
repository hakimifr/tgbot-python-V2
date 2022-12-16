#!/usr/bin/env python3

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


from util.help import Help
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from api_token import TOKEN

import modules.help
import modules.rm6785
# TODO: Implement these modules (ref: github.com/Hakimi0804/tgbot-fish)
# import modules.spam_protect     # Prevent spammers in groups
# import modules.moderation       # /ban, /kick, etc
# import modules.komaru           # Pranaya's komaru GIFs channel management
# import modules.toys             # Useless stuffs for fun, e.g. /shuf, etc


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("A bot written in Python3, by @Hakimi0804.")


Help.register_help("start", "Show bot's about.")
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", modules.help.bot_help))
app.add_handler(CommandHandler("approve", modules.rm6785.approve))
app.add_handler(CommandHandler("disapprove", modules.rm6785.disapprove))
app.add_handler(CommandHandler("post", modules.rm6785.post))
app.add_handler(CommandHandler("sticker", modules.rm6785.sticker))
app.add_handler(CommandHandler("authorize", modules.rm6785.authorize))
app.add_handler(CommandHandler("deauthorize", modules.rm6785.deauthorize))
app.add_handler(MessageHandler(filters.Regex(r"\.\+1"), modules.rm6785.approve))
app.add_handler(MessageHandler(filters.Regex(r"\.-1"), modules.rm6785.disapprove))
app.add_handler(MessageHandler(filters.Regex(r"(?i)\.post"), modules.rm6785.post))
app.add_handler(MessageHandler(filters.Regex(r"(?i)\.sticker"), modules.rm6785.sticker))
app.add_handler(MessageHandler(filters.Regex(r"(?i)\.auth"), modules.rm6785.authorize))
app.add_handler(MessageHandler(filters.Regex(r"(?i)\.deauth"), modules.rm6785.deauthorize))
# app.add_handler(MessageHandler(filters.Regex(r"(?i)crypto"), main))
app.run_polling()
