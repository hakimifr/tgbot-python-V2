import re
import logging
import telegram.error
from util.help import Help
from util.config import Config
from modules.rm6785 import RM6785_MASTER_USER
from telegram import Update
from telegram.ext import ContextTypes
log = logging.getLogger("modules.sticker")

config = Config("sticker-blocklist.json")
if config.config.get("blocklist") is None:
    config.config["blocklist"] = []


async def blocker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.sticker.set_name in config.config["blocklist"]:
        if update.message.from_user.id in RM6785_MASTER_USER:
            log.info("Will not delete blocklisted sticker sent by master users!")
            return

        try:
            await update.message.delete()
        except telegram.error.BadRequest:
            log.warn("Failed to delete blocklisted sticker")


async def block_unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in RM6785_MASTER_USER:
        await update.message.reply_text("You're not allowed to do this.")
        return

    if update.message.reply_to_message is None:
        await update.message.reply_text("Reply to a message.")
        return

    if update.message.reply_to_message.sticker is None:
        await update.message.reply_text("Not a sticker.")
        return

    if re.match(r"^/unblock", update.message.text):
        if update.message.reply_to_message.sticker.set_name in config.config["blocklist"]:
            config.config["blocklist"].remove(update.message.reply_to_message.sticker.set_name)
            await update.message.reply_text("Blocklist updated.")
        else:
            await update.message.reply_text("Not in blocklist.")

    elif re.match(r"^/block", update.message.text):
        if update.message.reply_to_message.sticker.set_name in config.config["blocklist"]:
            await update.message.reply_text("Sticker already in blacklist.")
        else:
            config.config["blocklist"].append(update.message.reply_to_message.sticker.set_name)
            await update.message.reply_text("Blocklist updated.")


async def list_blocklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = "Blocklisted packs:\n"
    for pack in config.config["blocklist"]:
        text += f"- {pack}\n"

    await update.message.reply_text(text)


Help.register_help("block", "block a sticker pack from being used")
Help.register_help("unblock", "unblock a sticker pack")
Help.register_help("listblocklist", "list blocked sticker pack")
