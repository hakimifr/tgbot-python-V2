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

import re
import json
import logging
import util.module
from util.help import Help
from util.config import Config
from telegram import Update, Message, MessageId
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, Application
log: logging.Logger = logging.getLogger(__name__)
config: Config = Config("rm6785_config.json")


class ModuleMetadata(util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("approve", approve))
        app.add_handler(CommandHandler("disapprove", disapprove))
        app.add_handler(CommandHandler("post", post))
        app.add_handler(CommandHandler("sticker", sticker))
        app.add_handler(CommandHandler("authorize", authorize))
        app.add_handler(CommandHandler("deauthorize", deauthorize))
        app.add_handler(CommandHandler("listauth", listauth))
        app.add_handler(CommandHandler("dumpconfig", dumpconfig))
        app.add_handler(CommandHandler("loadconfig", loadconfig))
        app.add_handler(CommandHandler("delchmsg", delchmsg))
        app.add_handler(CommandHandler("report", report))
        app.add_handler(MessageHandler(filters.Regex(r"^\.\+1"), approve))
        app.add_handler(MessageHandler(filters.Regex(r"^\.-1"), disapprove))
        app.add_handler(MessageHandler(filters.Regex(r"(?i)^\.post"), post))
        app.add_handler(MessageHandler(filters.Regex(r"(?i)^\.sticker"), sticker))
        app.add_handler(MessageHandler(filters.Regex(r"(?i)^\.auth"), authorize))
        app.add_handler(MessageHandler(filters.Regex(r"(?i)^\.deauth"), deauthorize))


# Constants
REQUIRED_APPROVAL_COUNT: int = 2
RM6785_DEVELOPMENT_CHAT_ID: int = -1001299514785
RM6785_CHANNEL_ID: int = -1001384382397
RM6785_CHAT_ID: int = -1001754321934
RM6785_UPDATE_STICKER: str = "CAACAgUAAxkBAAED_CFiFIVi0Z1YX3MOK9xnaylscRhWbQACNwIAAt6sOFUrmjW-3D3-2yME"
RM6785_MASTER_USER: list = [1024853832, 1138003186, 1583181351]  # Hakimi, Samar, Pratham
REALME6_GROUP_ID: int = -1001309495065
REALME6_ADMIN_GROUP_ID: int = -1001596458040


if config.config.get("authorized_users") is None:
    config.config["authorized_users"] = []
    config.write_config()


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

            count: int = 0
            if reply_init:
                if update.message.reply_to_message is None:
                    await update.message.reply_text("You must reply to a message.")
                    return

                if count_init:
                    try:
                        count: int = config.config[str(update.message.reply_to_message.message_id)]
                    except KeyError:
                        pass

            if reply_init and count_init:
                return await func(update, context, count)
            return await func(update, context)
        return wrapper
    return decorator


@check(reply_init=True, count_init=True)
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE, count) -> None:
    if count < 2:
        count += 1
        config.config[str(update.message.reply_to_message.message_id)] = count
        config.write_config()
        await update.message.reply_text(f"Approved. count: {count}")
    else:
        await update.message.reply_text("Message already have enough approval!")


@check(reply_init=True, count_init=True)
async def disapprove(update: Update, context: ContextTypes.DEFAULT_TYPE, count) -> None:
    count -= 1
    config.config[str(update.message.reply_to_message.message_id)] = count
    config.write_config()
    await update.message.reply_text(f"Disapproved. count: {count}")


@check(reply_init=True, count_init=True)
async def post(update: Update, context: ContextTypes.DEFAULT_TYPE, count) -> None:
    if count < 2:
        await update.message.reply_text("Not enough approval!")
        return

    message: Message = await update.message.reply_text("One moment...")
    await update.message.reply_to_message.copy(RM6785_CHANNEL_ID)
    result: MessageId = await update.message.reply_to_message.copy(RM6785_CHAT_ID)
    await result.get_bot().pin_chat_message(RM6785_CHAT_ID, result.message_id)

    del config.config[str(update.message.reply_to_message.message_id)]
    config.write_config()
    await message.edit_text("Posted")


@check()
async def sticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message: Message = await update.message.reply_text("Sending sticker...")
    await update.get_bot().send_sticker(RM6785_CHANNEL_ID, RM6785_UPDATE_STICKER)
    await message.edit_text("Sticker sent")


@check(reply_init=True)
async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
async def deauthorize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def listauth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config.read_config()
    text = "Master users \(these users are hardcoded in the codebase\):\n"  # noqa: W605
    for userid in RM6785_MASTER_USER:
        text += f"[this dude](tg://user?id={userid}) \({userid}\)\n"  # noqa: W605
    text += "\n"

    text += "Manually authorized users:\n"
    for userid in config.config["authorized_users"]:
        text += f"[this dude](tg://user?id={userid}) \({userid}\)\n"  # noqa: W605

    await update.message.reply_text(text, parse_mode="MarkdownV2")


async def dumpconfig(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conf: str = json.dumps(config.config)
    await update.message.reply_text(conf)


@check()
async def loadconfig(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in RM6785_MASTER_USER:
        await update.message.reply_text("Only master users can do this")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a text message.")
        return

    if not update.message.reply_to_message.text:
        await update.message.reply_text("That message does not contain text.")
        return

    try:
        json.loads(update.message.reply_to_message.text)
    except json.JSONDecodeError:
        await update.message.reply_text("Invalid JSON.")
        return

    with open(config.file, "w") as f:
        json.dump(json.loads(update.message.reply_to_message.text), f)

    config.read_config()
    await update.message.reply_text("New config loaded")


@check()
async def delchmsg(up: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    match = re.search(r"/(\d+)$", ctx.args[0])
    if not match:
        await up.message.reply_text("Invalid link/ID")
        return

    await up.get_bot().delete_message(chat_id=RM6785_CHANNEL_ID,
                                      message_id=match.group(1))
    await up.message.reply_text("Message deleted")


async def report(up: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if up.message.chat_id != REALME6_GROUP_ID:
        return

    await up.get_bot().send_message(REALME6_ADMIN_GROUP_ID, "!New report!\n"
                                                            f"Message link: "
                                                            f"https://t.me/c/{str(REALME6_GROUP_ID).removeprefix('-100')}"
                                                            f"/{up.message.id}")
    await up.message.reply_to_message.forward(REALME6_ADMIN_GROUP_ID)
    await up.message.reply_text("Message forwarded to admin group")


Help.register_help("approve", "Approve a message to be posted.")
Help.register_help("disapprove", "Disapprove a message to be posted.")
Help.register_help("post", "Post replied message to @RM6785.")
Help.register_help("sticker", "Send RM6785 sticker to @RM6785.")
Help.register_help("authorize", "Authorize a user for using RM6785 fetures.")
Help.register_help("deauthorize", "Deauthorize a user from using RM6785 fetures.")
Help.register_help("listauth", "List authorized users for RM6785 features.")
Help.register_help("dumpconfig", "Dump RM6785 config file")
Help.register_help("loadconfig", "Load RM6785 config file")
Help.register_help("delchmsg", "Delete a channel message sent by mistake")
Help.register_help("report", "Report an offending message")
