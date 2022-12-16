"""
Module to manage RM6785 community.
Available methods:

    approve(update, context)
        Approve a post to be able to post to the channel.

    disapprove(update, context)
        Revert/decrease approval of a post.

    post(update, context)
        Post the replied message to channel.

    sticker(update, context)
        Post RM6785's update sticker to channel.

    authorize(update, cotext)
        Allow a user to use the module functions.

    deauthorize(update, context)
        Disallow a user from using the module functions.

    listauth(update, context)
        List authorized users.
"""

import logging
from util.help import Help
from util.config import Config
from telegram import Update
from telegram.ext import ContextTypes
log = logging.getLogger("RM6785")
config = Config("rm6785_config.json")


# Constants
REQUIRED_APPROVAL_COUNT: int = 2
RM6785_DEVELOPMENT_CHAT_ID: int = -1001299514785
RM6785_CHANNEL_ID: int = -1001384382397
RM6785_CHAT_ID: int = -1001754321934
RM6785_UPDATE_STICKER: str = "CAACAgUAAxkBAAED_CFiFIVi0Z1YX3MOK9xnaylscRhWbQACNwIAAt6sOFUrmjW-3D3-2yME"
RM6785_MASTER_USER: list = [1024853832, 1138003186]  # Hakimi, Samar


if config.config.get("authorized_users") is None:
    config.config["authorized_users"] = []


# Decorator hell indeed
def check(count_init=False, reply_init=False):
    def decorator(func):
        """Common checks for most RM6785's methods."""
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Make sure we're in rm6785 chat
            if update.effective_chat.id != RM6785_DEVELOPMENT_CHAT_ID:
                await update.message.reply_text("This command is restricted to RM6785 development group only.")
                return

            # Prevent command from being used by unauthorized users
            config.read_config()
            if update.message.from_user.id not in config.config["authorized_users"] + RM6785_MASTER_USER:
                await update.message.reply_text("You are not authorized to use this command.")
                return

            count = 0
            if reply_init:
                if update.message.reply_to_message is None:
                    await update.message.reply_text("You must reply to a message.")
                    return

                if count_init:
                    try:
                        count = config.config[str(update.message.reply_to_message.message_id)]
                    except KeyError:
                        pass

            if reply_init and count_init:
                return await func(update, context, count)
            return await func(update, context)
        return wrapper
    return decorator


@check(reply_init=True, count_init=True)
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE, count):
    if count < 2:
        count += 1
        config.config[str(update.message.reply_to_message.message_id)] = count
        config.write_config()
        await update.message.reply_text(f"Approved. count: {count}")
    else:
        await update.message.reply_text("Message already have enough approval!")


@check(reply_init=True, count_init=True)
async def disapprove(update: Update, context: ContextTypes.DEFAULT_TYPE, count):
    count -= 1
    config.config[str(update.message.reply_to_message.message_id)] = count
    config.write_config()
    await update.message.reply_text(f"Disapproved. count: {count}")


@check(reply_init=True, count_init=True)
async def post(update: Update, context: ContextTypes.DEFAULT_TYPE, count):
    if count < 2:
        await update.message.reply_text("Not enough approval!")
        return

    await update.message.reply_text("One moment...")
    await update.message.reply_to_message.copy(RM6785_CHANNEL_ID)
    result = await update.message.reply_to_message.copy(RM6785_CHAT_ID)
    await result.get_bot().pin_chat_message(RM6785_CHAT_ID, result.message_id)

    del config.config[str(update.message.reply_to_message.message_id)]


@check()
async def sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await update.message.reply_text("Sending sticker...")
    await update.get_bot().send_sticker(RM6785_CHANNEL_ID, RM6785_UPDATE_STICKER)
    await message.edit_text("Sticker sent")


@check(reply_init=True)
async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in RM6785_MASTER_USER:
        await update.message.reply_text("You are not allowed to use this command.")
        return

    if update.message.reply_to_message.from_user.id in config.config["authorized_users"]:
        await update.message.reply_text("User is already authorized")
        return

    config.config["authorized_users"].append(update.message.reply_to_message.from_user.id)
    config.write_config()
    config.read_config()
    await update.message.reply_text(f"User {update.message.reply_to_message.from_user.first_name} is now authorized.")


@check(reply_init=True)
async def deauthorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in RM6785_MASTER_USER:
        await update.message.reply_text("You are not allowed to use this command.")
        return

    if update.message.reply_to_message.from_user.id not in config.config["authorized_users"]:
        await update.message.reply_text("That user was never authorized")
        return

    config.config["authorized_users"].remove(update.message.reply_to_message.from_user.id)
    config.write_config()
    config.read_config()
    await update.message.reply_text(f"User {update.message.reply_to_message.from_user.first_name} is now deauthorized.")


async def listauth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config.read_config()
    await update.message\
        .reply_text("Master users (these users are permanent):\n" + str(user + "\n" for user in RM6785_MASTER_USER) +
                    "Authorized users:\n" + str(user + "\n" for user in config.config["authorized_users"]))


Help.register_help("approve, .+1", "Approve a message to be posted.")
Help.register_help("disapprove, .-1", "Disapprove a message to be posted.")
Help.register_help("post", "Post replied message to @RM6785.")
Help.register_help("sticker", "Send RM6785 sticker to @RM6785.")
Help.register_help("authorize", "Authorize a user for using RM6785 fetures.")
Help.register_help("deauthorize", "Deauthorize a user from using RM6785 fetures.")
Help.register_help("listauth", "List authorized users for RM6785 features.")
