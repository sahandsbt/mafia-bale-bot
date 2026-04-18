"""Shared helpers"""

from dotenv import load_dotenv
import bale
import os

load_dotenv()

async def is_member(bot:bale.Bot, message:bale.Message):
    CHANNEL_ID = os.getenv("CHANNEL_ID")
    return await bot.get_chat_member(chat_id=CHANNEL_ID,user_id=message.from_user.chat_id)

async def ban_user(bot, message, user_id, user_fn):
    OWNER_ID = os.getenv("OWNER_ID")
    ADMINS_ID = os.getenv("ADMINS_ID").split(',')
    if (user_id in ADMINS_ID) and str(message.from_user.id) != OWNER_ID:
        await message.reply("⚠ امکان بن کردن ادمین هارا ندارید!")
        return False
    with open("data/banned.txt", 'r+', encoding="utf-8") as f:
        all_banned = f.readlines()
        if f"{user_id}\n" in all_banned:
            await message.reply("❌ کاربر از قبل بن شده!")
            return False
        f.write(f"{user_id}\n")
        await message.reply("✅ کاربر بن شد.")
        if str(message.from_user.id) != OWNER_ID:
            await bot.send_message(OWNER_ID, f"🚨 {user_fn} توسط {message.from_user.first_name} بن شد.")
    return True

async def unban_user(bot, message, user_id):
    OWNER_ID = os.getenv("OWNER_ID")
    try:
        with open("data/banned.txt", 'r', encoding="utf-8") as f:
            all_banned = f.readlines()
    except:
        await message.reply("❌ کاربر بن نشده!")
        return False
    if f"{user_id}\n" not in all_banned:
        await message.reply("❌ کاربر بن نشده!")
        return False
    all_banned.remove(f"{user_id}\n")
    banned_str = ""
    for i in all_banned:
        banned_str += i
    with open("data/banned.txt", 'w', encoding="utf-8") as f:
        f.write(banned_str)
    await message.reply("✅ کاربر  آن‌بن شد.")
    if str(message.from_user.id) != OWNER_ID:
        await bot.send_message(OWNER_ID, f"🚨 [کاربر](uid:{user_id}) توسط {message.from_user.first_name} آن‌بن شد.")
    return True
