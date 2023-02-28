import logging
import openai

from util.help import Help
from api_token import OPENAI_API_KEY
from telegram import Update
from telegram.ext import ContextTypes
log: logging.Logger = logging.getLogger(__name__)
openai.api_key = OPENAI_API_KEY


async def gpt3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("Generating response...")

    if not context.args:
        await msg.edit_text("Give some text sir")
        return

    aresult = await openai.Completion.acreate(prompt=" ".join(context.args),
                                              engine="text-davinci-003",
                                              max_tokens=2086,
                                              temperature=0.5)

    await msg.edit_text(aresult["choices"][0]["text"])


Help.register_help("gpt3", "Generate a GPT-3 response")
