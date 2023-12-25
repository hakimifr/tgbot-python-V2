import inspect

from util import module
from util.help import Help

from telegram import Update, BotCommand
from telegram.helpers import escape_markdown
from telegram.ext import Application, ContextTypes, BaseHandler, CommandHandler


class ModuleMetadata(module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("get_source", get_command_source))


async def get_command_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not 0 < len(context.args) < 2:
        await update.message.reply_text("Give a command to get source.")
        return

    target_command = context.args[0]

    handlers_dict: dict[BaseHandler, list[BaseHandler]] = context.application.handlers
    for handlers in handlers_dict.values():
        for handler in handlers:
            if not isinstance(handler, CommandHandler):
                continue

            if target_command in handler.commands:
                await update.message.reply_text("```python\n"
                                                + escape_markdown(inspect.getsource(handler.callback), version=2)
                                                + "\n```", parse_mode="MarkdownV2")
                return

    await update.message.reply_text("Error: command does not exist.")


Help.register_help("get_source", "Get a source code for a command.")
