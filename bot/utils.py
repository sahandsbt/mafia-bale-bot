"""Shared helpers"""

from dotenv import load_dotenv
import bale
import os

load_dotenv()

async def is_member(bot:bale.Bot, message:bale.Message):
    CHANNEL_ID = os.getenv("CHANNEL_ID")
    return await bot.get_chat_member(chat_id=CHANNEL_ID,user_id=message.from_user.chat_id)