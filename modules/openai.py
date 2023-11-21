import os
import time
import logging
import openai
import util.module

from util.help import Help
from util.config import Config
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application

log: logging.Logger = logging.getLogger(__name__)
API_KEY_OK = True
RESTRICTED_CHATS_KEY: str = "restricted_chats"
LIMIT_IN_SEC: int = 75
COMPLETION_SETTINGS: dict = {
    "model": "gpt-3.5-turbo",
    "max_tokens": 2000,
    "temperature": 0.2
}


class ModuleMetadata(util.module.ModuleMetadata):
    @classmethod
    def setup_module(cls, app: Application):
        app.add_handler(CommandHandler("gpt3", gpt3))


try:
    from api_token import OPENAI_API_KEY
except ImportError:
    if not (OPENAI_API_KEY := os.getenv("OPENAI_API_KEY")):
        log.error("Cannot get OpenAI api key; module will be disabled.")
        API_KEY_OK = False

config: Config = Config("openai.json")
openai.api_key = OPENAI_API_KEY

if not config.config.get(RESTRICTED_CHATS_KEY):
    config.config[RESTRICTED_CHATS_KEY] = {}
    config.write_config()


def check_key(function):
    async def wrapper(*arg, **kwargs):
        if API_KEY_OK:
            await function(*arg, **kwargs)
        else:
            log.error("Module was triggered, but token is not available")
    return wrapper


@check_key
async def gpt3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if timestamp := config.config[RESTRICTED_CHATS_KEY].get(str(update.message.chat_id)):
        if time.time() - timestamp < LIMIT_IN_SEC:
            await update.message.reply_text("Please wait for a few mins before trying again.\n"
                                            f"Currently limit is set to: {LIMIT_IN_SEC}s")
            return

    msg = await update.message.reply_text("Generating response...")

    if not context.args:
        await msg.edit_text("Give some text sir")
        return

    try:
        aresult = await openai.ChatCompletion.acreate(messages=[
                                                        {
                                                           "role": "user",
                                                           "content": f"{' '.join(context.args)}",
                                                        }
                                                      ],
                                                      **COMPLETION_SETTINGS)
    except Exception as e:
        log.error(e)
        await msg.edit_text(f"{e}")
        return

    await msg.edit_text(aresult["choices"][0]["message"]["content"] + f"\n\n---Debug---\n{COMPLETION_SETTINGS}")
    config.config[RESTRICTED_CHATS_KEY].update({str(update.message.chat_id): time.time()})


Help.register_help("gpt3", "Generate a GPT-3 response")
