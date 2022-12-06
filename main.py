#!/usr/bin/env python3

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from api_token import TOKEN

async def start(update, context):
    await update.message.reply_text("Hello, World!")


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
# app.add_handler(MessageHandler(filters.Regex(r"(?i)crypto"), main))
app.run_polling()

