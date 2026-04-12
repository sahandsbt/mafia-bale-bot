import bale
from collections import deque

async def admin_menu(message:bale.Message):
    admin_keyboard = bale.InlineKeyboardMarkup()
    admin_keyboard.add(bale.InlineKeyboardButton("⚔ گروه‌ها ⚔",callback_data="mafiaadmin:groups"),row=1)
    admin_keyboard.add(bale.InlineKeyboardButton("🕹 اتاق‌ها 🕹",callback_data="mafiaadmin:rooms"),row=1)
    admin_keyboard.add(bale.InlineKeyboardButton("🤵 کاربرها 🤵",callback_data="mafiaadmin:users"),row=2)
    await message.reply("👑 به پنل ادمین خوش آمدید.",components=admin_keyboard)

async def active_groups(bot:bale.Bot, queue:dict, callback:bale.CallbackQuery):
    members_str = "⚔ لیست گروه های فعال:\n\n"
    for i in queue.keys():
        temp_name = queue[i][0].split(',',2)
        members_str += f"💎 {temp_name[2]} با {len(queue[i])} عضو\n"
    await bot.send_message(callback.from_user.chat_id, members_str)

async def last_users(bot:bale.Bot, callback:bale.CallbackQuery):
    try:
        with open("data/users.txt", "r", encoding="utf-8") as f:
            last_lines = deque(f, 20)
    except:
        await bot.send_message(callback.from_user.chat_id,"⚠ 20 کاربر آخر یافت نشد.")
        return
    users_str = "🤵 بیست کاربر اخیر:\n\n"
    for i in last_lines:
        temp_info = i.split('|',1)
        users_str += f"➰ {temp_info[1]}\n"
    await bot.send_message(callback.from_user.chat_id, users_str)
