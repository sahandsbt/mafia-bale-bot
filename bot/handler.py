"""Message and event handling"""

from typing import Dict
import asyncio
import bale
import os

from bot.models.gameroom import GameRoom
from config import *
import bot.docs as docs

# Keyboards
start_keyboard = bale.MenuKeyboardMarkup()
start_keyboard.add(bale.MenuKeyboardButton("🎡 ساخت گروه 🎡"),row=1)
start_keyboard.add(bale.MenuKeyboardButton("❓ راهنما"),row=2)
start_keyboard.add(bale.MenuKeyboardButton("☎ پشتیبانی"),row=2)

leader_keyboard = bale.MenuKeyboardMarkup()
leader_keyboard.add(bale.MenuKeyboardButton("🎮 شروع بازی 🎮"))
leader_keyboard.add(bale.MenuKeyboardButton("🛑 حذف گروه 🛑"))

docs_keyboard = bale.InlineKeyboardMarkup()
docs_keyboard.add(bale.InlineKeyboardButton(text="⁉ قوانین", callback_data="mafiabot:rules"))
docs_keyboard.add(bale.InlineKeyboardButton(text="🕵️‍♂️ نقش ها", callback_data="mafiabot:roles"))

helpback_keyboard = bale.InlineKeyboardMarkup()
helpback_keyboard.add(bale.InlineKeyboardButton(text="🔙 بازگشت به راهنما", callback_data="mafiabot:helpback"))

invited_keyboard = bale.MenuKeyboardMarkup()
invited_keyboard.add(bale.MenuKeyboardButton("🚪 خروج 🚪"))

null_keyboard = bale.MenuKeyboardMarkup()

async def on_ready(bot: bale.Bot):
    logger.info(f"Logged in as {bot.user.username} - ID: {bot.user.id}")
    logger.info("Bot is now ready and online!")

active_rooms: Dict[str, GameRoom] = {}
waiting_lobby = {}
room_locks = {}

async def room(bot, members_list):
    room_id = str(hash(tuple(members_list)))
    room_locks[room_id] = asyncio.Lock()
    game_room = GameRoom(bot, members_list)
    active_rooms[room_id] = game_room
    try:
        await game_room.run_game()
    except Exception as e:
        print(f"Error in room {room_id}: {e}")
        await game_room.broadcast_message(f"❌ خطا در بازی: {str(e)}",components=start_keyboard)
    finally:
        if room_id in active_rooms:
            del active_rooms[room_id]
        if room_id in room_locks:
            del room_locks[room_id]

async def on_message(bot: bale.Bot, message: bale.Message):
    if message.text == None:
        logger.warning(f"Unsupported type of message sent. | Name: {message.from_user.first_name} - ID: {message.from_user.id}")
        return
    
    chat_id = str(message.chat_id)
    for room_id, game_room in active_rooms.items():
        async with room_locks.get(room_id, asyncio.Lock()):
            for member in game_room.members:
                member_chat_id, _ = member.split(',', 1)
                if member_chat_id == chat_id:
                    if game_room.game_active and message.text:
                        if message.text.startswith("رای به"):
                            await game_room.handle_vote(chat_id, message.text)
                        elif message.text.startswith("دست دادن با"):
                            await game_room.handle_handshake(chat_id, message.text)
                        elif message.text.startswith("کشتن"):
                            await game_room.handle_kill(chat_id, message.text)
                        elif message.text.startswith("اسنایپ"):
                            await game_room.handle_snipe(chat_id, message.text)
                        elif message.text.startswith("نجات"):
                            await game_room.handle_save(chat_id, message.text)
                        elif message.text.startswith("حفاظت از"):
                            await game_room.handle_prot(chat_id, message.text)
                        elif message.text.startswith("استعلام"):
                            await game_room.handle_detect(chat_id, message.text)
                        elif message.text.startswith("گرفتن استعلام کشته ها"):
                            await game_room.handle_inquire(chat_id)
                        else:
                            await game_room.handle_player_message(chat_id, message.text)
                        return
                    break
    
    if message.text == "🚪 خروج 🚪" and (message.from_user.chat_id in waiting_lobby):
        inviter = waiting_lobby[message.from_user.chat_id]
        room_file = open(f"{inviter}.txt", 'r', encoding="utf-8")
        ids = room_file.readlines()
        new_line = f"{message.from_user.chat_id},{message.from_user.first_name}\n"
        ind = ids.index(new_line)
        ids.pop(ind)
        room_file.close()
        ids_str = ""
        for i in ids:
            ids_str += i
        with open(f"{inviter}.txt", "w", encoding="utf-8") as f:
            f.write(ids_str)
        waiting_lobby.pop(message.from_user.chat_id)
        await message.reply(text="🚦 از گروه خارج شدید.",components=start_keyboard)
        return
    
    if message.from_user.chat_id in waiting_lobby:
        if waiting_lobby[message.from_user.chat_id] != message.from_user.id:
            await message.reply(text="‼ شما در یک انتظار شروع بازی هستید! ابتدا از گروه خارج شوید.")
            return
    
    if message.text == "🎮 شروع بازی 🎮":
        members = [f"{message.from_user.chat_id},{message.from_user.first_name}"]
        with open(f"{message.from_user.id}.txt", 'r', encoding="utf-8") as f:
            memberlist = f.readlines()
        for i in range(1, len(memberlist)):
            members.append(memberlist[i][:-1])
        if len(members) > 3:
            for member in members:
                member_chat_id = member.split(',',1)
                waiting_lobby.pop(member_chat_id[0])
            os.remove(f"{message.from_user.id}.txt")
            asyncio.create_task(room(bot, members))
        else:
            await message.reply(text="حداقل تعداد برای شروع 4 نفر است!")
        return
    
    if message.text == "🛑 حذف گروه 🛑":
        members = [message.from_user.chat_id]
        memberlist = []
        try:
            with open(f"{message.from_user.id}.txt", 'r', encoding="utf-8") as f:
                memberlist = f.readlines()
        except:
            await message.reply("⚠ شما لیدر گروهی نیستید!")
            return
        for i in memberlist:
            chatid = i.split(',',1)
            waiting_lobby.pop(chatid[0])
            await bot.send_message(chatid[0],"📛 گروه توسط لیدر حذف شد!",components=start_keyboard)
        os.remove(f"{message.from_user.id}.txt")
        return
    
    if message.from_user.chat_id in waiting_lobby:
        await message.reply(text="‼ شما لیدر گروه هستید! ابتدا بازی را شروع کنید.")
        return
    
    if message.text.startswith("/start"):
        all_users = []
        new_user = f"{message.from_user.chat_id}|{message.from_user.username}|{message.from_user.first_name}\n"
        try:
            all_users_file = open("data/users.txt", 'r', encoding="utf-8")
            all_users = all_users_file.readlines()
            all_users_file.close()
        except:
            pass
        if new_user not in all_users:
            with open("data/users.txt", 'a', encoding="utf-8") as f:
                f.write(f"{message.from_user.chat_id}|{message.from_user.username}|{message.from_user.first_name}\n")
        if message.text == "/start":
            await message.reply(
                text="سلام خوش اومدی به بات بازی مافیا🥹\n\n💥 برای شروع بازی روی ساخت گروه کلیک کن یا\n➖ /party\nرو بفرست😎",
                components=start_keyboard)
        else:
            start_code_list = message.text.split()
            start_code = start_code_list[1]
            if start_code.startswith("party-") and (message.from_user.id != start_code[6:]) :
                invite_code = start_code[6:]
                try:
                    room_file = open(f"{invite_code}.txt", 'r', encoding="utf-8")
                    ids = room_file.readlines()
                    with open(f"{invite_code}.txt", 'a', encoding="utf-8") as f:
                        f.write(f"{message.from_user.chat_id},{message.from_user.first_name}\n")
                    meschat_id = ids[0].split(',')
                    memberlist = f"🔅{message.from_user.first_name}\n"
                    for i in range(1, len(ids)):
                        temp = ids[i].split(sep=',', maxsplit=1)
                        await bot.send_message(temp[0],f"💠 {message.from_user.first_name} به گروه اضافه شد.")
                        memberlist += f"🔅{temp[1]}"
                    await bot.edit_message(
                        meschat_id[0], meschat_id[1][:-1],
                        f"⚔ اینو برا دوستات بفرست:\nhttps://ble.ir/mafiasbot?start={start_code}\n\n⏰ افراد اضافه شده:\n{memberlist}",
                        components=leader_keyboard)
                    await message.reply(
                        text=f"🔥 به بازی اضافه شدی. وایستا تا بازی شروع شه.\n\n⏰ اعضای فعلی:\n{memberlist}",
                        components=invited_keyboard)
                    waiting_lobby[message.from_user.chat_id] = invite_code
                    room_file.close()
                except:
                    await message.reply(text="🗿 گروه مدنظر وجود ندارد.")
    
    elif message.text == "🎡 ساخت گروه 🎡" or message.text == "/party":
        await message.reply(
            text=f"⚔ اینو برا دوستات بفرست:\nhttps://ble.ir/mafiasbot?start=party-{message.from_user.id}",
            components=leader_keyboard)
        with open(f"{message.from_user.id}.txt", 'w', encoding="utf-8") as f:
            f.write(f"{message.chat_id},{int(message.message_id) + 1}\n")
        waiting_lobby[message.from_user.chat_id] = message.from_user.id
    
    elif message.text == "☎ پشتیبانی" or message.text == "/support":
        await message.reply(text="📣 در صورت بروز هرگونه مشکل فنی خواهشمندیم به\n🆔 @sahandsbt\nدر بله یا تلگرام پیام دهید.")
    
    elif message.text == "❓ راهنما" or message.text == "/help":
        await message.reply(text=docs.main_help,components=docs_keyboard)
     
    else:
        await message.reply(text="😒 دستور نامعتبر!")
        logger.warning(f"Unsupported command sent. | Name: {message.from_user.first_name} - ID: {message.from_user.id}")

async def on_callback(bot: bale.Bot, callback: bale.CallbackQuery):
    if callback.data == "mafiabot:roles":
        await callback.message.edit(docs.roles_help,components=helpback_keyboard)
    elif callback.data == "mafiabot:rules":
        await callback.message.edit(docs.rules_help,components=helpback_keyboard)
    elif callback.data == "mafiabot:helpback":
        await callback.message.edit(docs.main_help,components=docs_keyboard)
