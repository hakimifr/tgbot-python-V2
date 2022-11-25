#!/usr/bin/env python3

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

import asyncio
import telegram

from api_token import TOKEN

async def main():
    bot = telegram.Bot(TOKEN)
    async with bot:
        pass


if __name__ == '__main__':
    asyncio.run(main())

