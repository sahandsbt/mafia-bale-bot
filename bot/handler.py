"""Message and event handling"""

from typing import Dict
import asyncio
import bale
import os

from bot.models.gameroom import GameRoom
from config import *

# Keyboards
start_keyboard = bale.MenuKeyboardMarkup()
start_keyboard.add(bale.MenuKeyboardButton("🎡 ساخت گروه 🎡"),row=1)
start_keyboard.add(bale.MenuKeyboardButton("❓ راهنما"),row=2)
start_keyboard.add(bale.MenuKeyboardButton("☎ پشتیبانی"),row=2)

leader_keyboard = bale.MenuKeyboardMarkup()
leader_keyboard.add(bale.MenuKeyboardButton("🎮 شروع بازی 🎮"),row=1)

invited_keyboard = bale.MenuKeyboardMarkup()
invited_keyboard.add(bale.MenuKeyboardButton("🚪 خروج 🚪"),row=1)

null_keyboard = bale.MenuKeyboardMarkup()

async def on_ready(bot: bale.Bot):
    logger.info(f"Logged in as {bot.user.first_name} {bot.user.last_name} ID: {bot.user.id}")
    logger.info("Bot is now ready and online!")

active_rooms: Dict[str, GameRoom] = {}
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
        await game_room.broadcast_message(f"❌ خطا در بازی: {str(e)}")
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
                                else:
                                    await game_room.handle_player_message(chat_id, message.text)
                                return
                            break

    if message.text.startswith("/start"):
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
                    room_file = open(f"{invite_code}.txt", 'r')
                    ids = room_file.readlines()
                    new_line = f"{message.from_user.chat_id},{message.from_user.first_name}\n"
                    if new_line not in ids:
                        with open(f"{invite_code}.txt", 'a') as f:
                            f.write(f"{message.from_user.chat_id},{message.from_user.first_name}\n")
                        meschat_id = ids[0].split(',')
                        memberlist = f"🔅{message.from_user.first_name}\n"
                        for i in range(1, len(ids)):
                            temp = ids[i].split(sep=',', maxsplit=1)
                            await bot.send_message(temp[0],f"💠 {message.from_user.first_name} به گروه اضافه شد.")
                            memberlist += f"🔅{temp[1]}"
                        await bot.edit_message(
                            meschat_id[0], meschat_id[1][:-1],
                            f"⚔ اینو برا دوستات بفرست:\nhttps://ble.ir/sasabot?start={start_code}\n\n⏰ افراد اضافه شده:\n{memberlist}",
                            components=leader_keyboard)
                        await message.reply(
                            text=f"🔥 به بازی اضافه شدی. وایستا تا بازی شروع شه.\n\n⏰ اعضای فعلی:\n{memberlist}",
                            components=invited_keyboard)
                    room_file.close()
                except:
                    await message.reply(text="☹ پیوستن به گروه با مشکل مواجه شد. لطفا به پشتیبانی اطلاع دهید.")
    
    elif message.text == "🎡 ساخت گروه 🎡" or message.text == "/party":
        await message.reply(
            text=f"⚔ اینو برا دوستات بفرست:\nhttps://ble.ir/sasabot?start=party-{message.from_user.id}",
            components=leader_keyboard)
        with open(f"{message.from_user.id}.txt", 'w') as f:
            f.write(f"{message.chat_id},{int(message.message_id) + 1}\n")
    
    elif message.text == "☎ پشتیبانی" or message.text == "/support":
        await message.reply(text="📣 در صورت بروز هرگونه مشکل فنی خواهشمندیم به\n🆔 @sahandsbt\nدر بله یا تلگرام پیام دهید.")
    
    elif message.text == "❓ راهنما" or message.text == "/help":
        await message.reply(text="😑 داریم روش کار میکنیم.")
     
    elif message.text == "🎮 شروع بازی 🎮":
        members = [f"{message.from_user.chat_id},{message.from_user.first_name}"]
        with open(f"{message.from_user.id}.txt", 'r') as f:
            memberlist = f.readlines()
        os.remove(f"{message.from_user.id}.txt")
        for i in range(1, len(memberlist)):
            members.append(memberlist[i][:-1])
        if len(members) > 1: #=======================================( 3 )
            asyncio.create_task(room(bot, members))
            await message.reply("🎆 بازی شروع شد 🎆")
        else:
            await message.reply(text="حداقل تعداد برای شروع 4 نفر است!")
    
    elif message.text == "🚪 خروج 🚪":
        await message.reply(text="😑 داریم روش کار میکنیم.")
    
    else:
        await message.reply(text="😒 دستور نامعتبر!")
        logger.warning(f"Unsupported command sent. | Name: {message.from_user.first_name} - ID: {message.from_user.id}")
