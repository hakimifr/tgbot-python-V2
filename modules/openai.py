import time
import logging
import openai

from util.help import Help
from util.config import Config
from api_token import OPENAI_API_KEY
from telegram import Update
from telegram.ext import ContextTypes

RESTRICTED_CHATS_KEY: str = "restricted_chats"
LIMIT_IN_SEC: int = 75
COMPLETION_SETTINGS: dict = {
    "model": "gpt-3.5-turbo",
    "max_tokens": 2000,
    "temperature": 0.2
}

log: logging.Logger = logging.getLogger(__name__)
config: Config = Config("openai.json")
openai.api_key = OPENAI_API_KEY

if not config.config.get(RESTRICTED_CHATS_KEY):
    config.config[RESTRICTED_CHATS_KEY] = {}
    config.write_config()


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

    aresult = await openai.ChatCompletion.acreate(messages=[
                                                    {
                                                       "role": "user",
                                                       "content": f"{' '.join(context.args)}",
                                                    }
                                                  ],
                                                  **COMPLETION_SETTINGS)

    await msg.edit_text(aresult["choices"][0]["message"]["content"] + f"\n\n---Debug---\n{COMPLETION_SETTINGS}")
    config.config[RESTRICTED_CHATS_KEY].update({str(update.message.chat_id): time.time()})


Help.register_help("gpt3", "Generate a GPT-3 response")
