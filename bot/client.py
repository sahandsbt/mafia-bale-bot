"""Main bot client init"""

import asyncio
import bale
import os

from config import *
from bot import handler

# Bot init
bot = bale.Bot(BOT_TOKEN)

@bot.event
async def on_ready():
    await handler.on_ready(bot)

@bot.event
async def on_message(message: bale.Message):
    await handler.on_message(bot, message)

@bot.event
async def on_callback(callback: bale.CallbackQuery):
    await handler.on_callback(bot, callback)

def run_bot():
    try:
        bot.run()
    except Exception as e:
        logger.error(f"An error occured during running the bot: {e}")
    finally:
        logger.info("Bot has shut down.")