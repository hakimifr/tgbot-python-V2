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

import util.module

from typing import Callable, Any
from functools import wraps

from util.help import Help

from telegram import Update, ChatMemberAdministrator
from telegram.ext import ContextTypes, Application, CommandHandler
from telegram.error import TelegramError


class ModuleMetadata(util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("ban", ban, block=False))
        app.add_handler(CommandHandler("unban", unban, block=False))
        app.add_handler(CommandHandler("kick", kick, block=False))
        app.add_handler(CommandHandler("promote", promote, block=False))
        app.add_handler(CommandHandler("demote", demote, block=False))


# Decorator hell
# Note to self: This is decorator factory, so when using it, the parenthesis is needed even with no argument
# i.e. @check_admin()
def check_admin(check_reply: bool = True, check_can_promote_member_permission: bool = False) -> Callable:
    def decorator(func: Callable[[Update, ContextTypes.DEFAULT_TYPE], Any]) -> Any:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
            chat_admins: tuple[ChatMemberAdministrator] = await update.effective_chat.get_administrators()  # type: ignore
            chat_admins_id: list[int] = [admin.user.id for admin in chat_admins]
            if update.message.from_user.id not in chat_admins_id:
                await update.message.reply_text("You're not admin")
                return
            if update.get_bot().id not in chat_admins_id:
                await update.message.reply_text("I'm not admin")
                return

            if check_reply:
                if not update.message.reply_to_message:
                    await update.message.reply_text("Please reply to a message")
                    return

            if check_can_promote_member_permission:
                if not chat_admins[chat_admins_id.index(update.get_bot().id)].can_promote_members:
                    await update.message.reply_text("Sorry, but I do not have can_promote_member permission.")
                    return

            return await func(update, context)
        return wrapper
    return decorator


@check_admin()
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.get_bot().ban_chat_member(update.message.chat_id,  # type: ignore
                                           update.message.reply_to_message.from_user.id)


@check_admin()
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.get_bot().unban_chat_member(update.message.chat_id,  # type: ignore
                                             update.message.reply_to_message.from_user.id,
                                             only_if_banned=True)


@check_admin()
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Since unban_chat_member actually ban and then unban the user (unless only_if_banned=True) is given,
    # we can take advantage of that for kicking the user.
    await update.get_bot().unban_chat_member(update.message.chat_id,  # type: ignore
                                             update.message.reply_to_message.from_user.id)


@check_admin(check_can_promote_member_permission=True)
async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE,) -> None:
    # We promote with the same level of admin rights
    # so first get our admin rights
    me: ChatMemberAdministrator = await update.effective_chat.get_member(update.get_bot().id)  # type: ignore
    all_rights = ["can_manage_chat", "can_delete_messages", "can_manage_video_chats",
                  "can_restrict_members", "can_promote_members", "can_change_info",
                  "can_invite_users", "can_post_stories", "can_edit_stories",
                  "can_delete_stories", "can_pin_messages", "can_manage_topics"]
    avail_rights = list(filter(lambda x: getattr(me, x), all_rights))
    avail_rights.remove("can_promote_members")
    rights = {right: True for right in avail_rights}
    try:
        await update.effective_chat.promote_member(update.message.reply_to_message.from_user.id,
                                                   **rights)  # type: ignore
        await update.message.reply_text(f"Promoted!\n"
                                        f"Note that this command promote with the exact same "
                                        f"admin rights as the bot except: 'can_promote_member'.\n"
                                        f"here are the given rights:\n"
                                        f"{rights}")
    except TelegramError as e:
        await update.message.reply_text(f"Uh-oh, that errored out! No clue why that happens."
                                        f"Traceback info: \nTelegramError: {e}")


@check_admin(check_can_promote_member_permission=True)
async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE,) -> None:
    me: ChatMemberAdministrator = await update.effective_chat.get_member(update.get_bot().id)  # type: ignore
    all_rights = ["can_manage_chat", "can_delete_messages", "can_manage_video_chats",
                  "can_restrict_members", "can_promote_members", "can_change_info",
                  "can_invite_users", "can_post_stories", "can_edit_stories",
                  "can_delete_stories", "can_pin_messages", "can_manage_topics"]
    avail_rights = list(filter(lambda x: getattr(me, x), all_rights))
    rights = {right: False for right in avail_rights}
    try:
        await update.effective_chat.promote_member(update.message.reply_to_message.from_user.id,
                                                   **rights)  # type: ignore
    except TelegramError as e:
        await update.message.reply_text(f"Uh-oh, that errored out! Most probably because that person was "
                                        f"promoted by someone else! traceback info: \nTelegramError: {e}")


Help.register_help("ban", "Ban a user")
Help.register_help("unban", "Unban a user")
Help.register_help("kick", "Kick a user")
Help.register_help("promote", "Promote a user")
Help.register_help("demote", "Demote a user")
