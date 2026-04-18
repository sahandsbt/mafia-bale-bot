"""Message and event handling"""

from typing import Dict
import asyncio
import bale
import os

from bot.models.gameroom import GameRoom
from bot.models.admin import *
from dotenv import load_dotenv
from config import *
from bot.utils import *
import bot.docs as docs

async def on_ready(bot: bale.Bot):
    logger.info(f"Logged in as {bot.user.username} - ID: {bot.user.id}")
    logger.info("Bot is now ready and online!")

load_dotenv()
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
BOT_USERNAME = os.getenv("BOT_USERNAME")
OWNER_ID = os.getenv("OWNER_ID")
ADMINS_ID = os.getenv("ADMINS_ID").split(',')
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME")
DONATE_URL = os.getenv("DONATE_URL")
active_rooms: Dict[str, GameRoom] = {}
queue_members = {}
public_queue = []
queue_lock = asyncio.Lock()
waiting_lobby = {}
room_locks = {}

# Keyboards
start_keyboard = bale.MenuKeyboardMarkup()
start_keyboard.add(bale.MenuKeyboardButton("🎡 ساخت گروه 🎡"),row=1)
start_keyboard.add(bale.MenuKeyboardButton("🎲 گروه عمومی 🎲"),row=1)
start_keyboard.add(bale.MenuKeyboardButton("❓ راهنما"),row=2)
start_keyboard.add(bale.MenuKeyboardButton("✨ دونیت"),row=2)
start_keyboard.add(bale.MenuKeyboardButton("☎ پشتیبانی"),row=2)

leader_keyboard = bale.InlineKeyboardMarkup()
leader_keyboard.add(bale.InlineKeyboardButton("🎮 شروع بازی 🎮",callback_data="mafiabot:startparty"))
leader_keyboard.add(bale.InlineKeyboardButton("🛑 حذف گروه 🛑",callback_data="mafiabot:deleteparty"))

docs_keyboard = bale.InlineKeyboardMarkup()
docs_keyboard.add(bale.InlineKeyboardButton(text="⁉ قوانین", callback_data="mafiabot:rules"))
docs_keyboard.add(bale.InlineKeyboardButton(text="🕵️‍♂️ نقش ها", callback_data="mafiabot:roles"))

create_keyboard = bale.InlineKeyboardMarkup()
create_keyboard.add(bale.InlineKeyboardButton(text="🌐 عمومی", callback_data="mafiabot:create-public"))
create_keyboard.add(bale.InlineKeyboardButton(text="🛡 خصوصی", callback_data="mafiabot:create-private"))

helpback_keyboard = bale.InlineKeyboardMarkup()
helpback_keyboard.add(bale.InlineKeyboardButton(text="🔙 بازگشت به راهنما", callback_data="mafiabot:helpback"))

invited_keyboard = bale.InlineKeyboardMarkup()
invited_keyboard.add(bale.InlineKeyboardButton("🚪 خروج 🚪",callback_data="mafiabot:exitparty"))

donate_keyboard = bale.InlineKeyboardMarkup()
donate_keyboard.add(bale.InlineKeyboardButton("🎉 دونیت",url=DONATE_URL))

all_banned = []
try:
    with open("data/banned.txt", 'r', encoding="utf-8") as f:
        all_banned = f.readlines()
except:
    print("Error: File banned.txt does not exist")

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
    if f"{message.from_user.id}\n" in all_banned:
        await message.reply(f"🚫 شما از بات بن شده اید!\n\n❕ برای اعتراض به @{SUPPORT_USERNAME} پیام دهید.")
        return
    if message.text == None:
        logger.warning(f"Unsupported type of message sent. | Name: {message.from_user.first_name} - ID: {message.from_user.id}")
        return
    if not message.from_user.first_name:
        return
    
    if message.text == "/report":
        replied_message = message.reply_to_message
        if not replied_message:
            await message.reply("❕ برای استفاده از این دستور، روی پیام یک نفر ریپلای کرده و سپس /report را بفرستید.")
            return
        for admin in ADMINS_ID:
            await bot.send_message(admin,f"🚨 درخواست بن از طرف {message.from_user.first_name}:\n\n-------\n{replied_message.text}")
        return
    
    chat_id = str(message.chat_id)
    for room_id, game_room in active_rooms.items():
        async with room_locks.get(room_id, asyncio.Lock()):
            for member in game_room.members:
                member_chat_id, _ = member.split(',', 1)
                if member_chat_id == chat_id:
                    if game_room.game_active and message.text:
                        if message.text.startswith("رای به "):
                            await game_room.handle_vote(chat_id, message.text)
                        elif message.text.startswith("دست دادن با "):
                            await game_room.handle_handshake(chat_id, message.text)
                        elif message.text.startswith("کشتن "):
                            await game_room.handle_kill(chat_id, message.text)
                        elif message.text.startswith("اسنایپ "):
                            await game_room.handle_snipe(chat_id, message.text)
                        elif message.text.startswith("نجات "):
                            await game_room.handle_save(chat_id, message.text)
                        elif message.text.startswith("حفاظت از "):
                            await game_room.handle_prot(chat_id, message.text)
                        elif message.text.startswith("استعلام "):
                            await game_room.handle_detect(chat_id, message.text)
                        elif message.text.startswith("گرفتن استعلام کشته ها"):
                            await game_room.handle_inquire(chat_id)
                        elif message.text == ("🤏 چالش"):
                            await game_room.handle_challange(chat_id)
                        elif message.text.startswith("چالش به "):
                            await game_room.handle_accept(chat_id,message.text)
                        else:
                            await game_room.handle_player_message(chat_id, message)
                        return
                    break
    
    if message.from_user.chat_id in waiting_lobby:
        if waiting_lobby[message.from_user.chat_id] == message.from_user.id:
            await message.reply("‼ شما لیدر گروه هستید! ابتدا بازی را شروع کنید.", components=leader_keyboard)
        else:
            await message.reply("‼ شما در یک انتظار شروع بازی هستید! ابتدا از گروه خارج شوید.", components=invited_keyboard)
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
        
        sub_check = await is_member(bot, message)
        if sub_check == None:
            new_url = message.text
            new_url = new_url.replace("/","")
            new_url = new_url.replace(" ","=")
            new_url = f"https://ble.ir/{BOT_USERNAME}?" + new_url
            subcheck_keyboard = bale.InlineKeyboardMarkup()
            subcheck_keyboard.add(bale.InlineKeyboardButton("✅ عضو شدم",url=new_url))
            subcheck_keyboard.add(bale.InlineKeyboardButton("💠 عضویت",url=f"https://ble.ir/{CHANNEL_USERNAME}"))
            await message.reply(
                f"سلام! خواهشا ابتدا در کانال اطلاع رسانی بات عضو شوید 🥰\n🆔 @{CHANNEL_USERNAME}\nسپس روی عضو شدم کلیک کنید.✨",
                components=subcheck_keyboard)
            return
        if message.text == "/start":
            await message.reply(
                text="سلام خوش اومدی به بات بازی مافیا🥹\n\n💥 برای شروع بازی روی ساخت گروه کلیک کن یا\n➖ /party\nرو بفرست😎",
                components=start_keyboard)
        else:
            start_code_list = message.text.split()
            start_code = start_code_list[1]
            if start_code.startswith("party-") and (message.from_user.id != start_code[6:]) :
                invite_code = int(start_code[6:])
                try:
                    async with queue_lock:
                        queue_members[invite_code].append(f"{message.from_user.chat_id},{message.from_user.first_name}")
                    ids = queue_members[invite_code]
                    meschat_id = ids[0].split(',')
                    memberlist = f"🔅{meschat_id[2]}\n"
                    for i in range(1, len(ids)):
                        temp = ids[i].split(sep=',', maxsplit=1)
                        await bot.send_message(temp[0],f"💠 {message.from_user.first_name} به گروه اضافه شد.")
                        memberlist += f"🔅{temp[1]}\n"
                    await bot.edit_message(
                        meschat_id[0], meschat_id[1],
                        f"⚔ اینو برا دوستات بفرست:\nhttps://ble.ir/{BOT_USERNAME}?start={start_code}\n\n⏰ افراد اضافه شده:\n{memberlist}",
                        components=leader_keyboard)
                    await message.reply(
                        text=f"🔥 به بازی اضافه شدی. وایستا تا بازی شروع شه.\n\n⏰ اعضای فعلی:\n{memberlist}",
                        components=invited_keyboard)
                    waiting_lobby[message.from_user.chat_id] = invite_code
                except:
                    await message.reply(text="🗿 گروه مدنظر وجود ندارد.")
    
    elif message.text == "🎡 ساخت گروه 🎡" or message.text == "/party":
        await message.reply(text="🕹 لطفا نوع گروه را انتخاب کنید.",components=create_keyboard)
    
    elif message.text == "🎲 گروه عمومی 🎲":
        public_rooms = bale.InlineKeyboardMarkup()
        async with queue_lock:
            for rm in public_queue:
                rm_id, rm_name = rm.split(",",1)
                count = len(queue_members[int(rm_id)])
                invite_url = f"https://ble.ir/{BOT_USERNAME}?start=party-{rm_id}"
                public_rooms.add(bale.InlineKeyboardButton(f"گروه {rm_name} با {count} نفر",url=invite_url),row=public_queue.index(rm)+1)
        await message.reply(text="🌱 گروه های فعال:",components=public_rooms)

    elif message.text == "☎ پشتیبانی" or message.text == "/support":
        await message.reply(text=f"📣 در صورت بروز هرگونه مشکل فنی خواهشمندیم به\n🆔 @{SUPPORT_USERNAME}\nدر بله یا تلگرام پیام دهید.")
    
    elif message.text == "✨ دونیت":
        await message.reply("🎁 با حمایت مالی از بات، به حفظ و توسعه آن کمک شایانی خواهید کرد.",components=donate_keyboard)
        
    elif message.text == "❓ راهنما" or message.text == "/help":
        await message.reply(text=docs.main_help,components=docs_keyboard)

    elif message.text == "/admin" and str(message.from_user.id) in ADMINS_ID:
        await admin_menu(message)

    elif message.text.startswith("/ban ") and str(message.from_user.id) in ADMINS_ID:
        if '@' not in message.text:
            await message.reply("⚠ لطفا یوزرنیم را با @ وارد کنید!")
        unbanned_username = message.text.split('@')
        unbanned_username = unbanned_username[1].lower()
        try:
            with open("data/users.txt", 'r', encoding="utf-8") as f:
                banned_users = f.readlines()
        except:
            await message.reply("❌ کاربر یافت نشد!")
            return
        for user in banned_users:
            user_data = user.split('|',2)
            if user_data[1] == unbanned_username:
                ban_success = await ban_user(bot, message, user_data[0], user_data[2][:-1])
                if ban_success:
                    all_banned.append(f"{user_data[0]}\n")
                return
        await message.reply("❌ کاربر یافت نشد!")

    elif message.text.startswith("/unban ") and str(message.from_user.id) in ADMINS_ID:
        unbanned_user = message.text.split(' ')[1].lower()
        if '@' in unbanned_user:
            unbanned_username = unbanned_user[1:]
            try:
                with open("data/users.txt", 'r', encoding="utf-8") as f:
                    banned_users = f.readlines()
            except:
                await message.reply("❌ کاربر یافت نشد!")
                return
            for user in banned_users:
                user_data = user.split('|',2)
                if user_data[1] == unbanned_username:
                    unban_success = await unban_user(bot, message, user_data[0])
                    if unban_success:
                        all_banned.remove(f"{user_data[0]}\n")
                    return
        elif unbanned_user.isdigit():
            unban_success = await unban_user(bot, message, unbanned_user)
            if unban_success:
                all_banned.remove(f"{user_data[0]}\n")
        else:
            await message.reply("❌ لطفا اطلاعات درست وارد کنید!")

    else:
        await message.reply(text="😒 دستور نامعتبر!")
        logger.warning(f"Unsupported command sent. | Name: {message.from_user.first_name} - ID: {message.from_user.id}")

async def on_callback(bot: bale.Bot, callback: bale.CallbackQuery):
    if f"{callback.from_user.id}\n" in all_banned:
        return
    if callback.data == "mafiabot:roles":
        await callback.message.edit(docs.roles_help,components=helpback_keyboard)

    elif callback.data == "mafiabot:rules":
        await callback.message.edit(docs.rules_help,components=helpback_keyboard)

    elif callback.data == "mafiabot:helpback":
        await callback.message.edit(docs.main_help,components=docs_keyboard)

    elif callback.data == "mafiabot:startparty":
        async with queue_lock:
            if callback.from_user.id not in queue_members:
                await bot.send_message(callback.from_user.chat_id, "⚠ شما لیدر گروهی نیستید!")
                return
            temp_line = f"{callback.from_user.id},{callback.from_user.first_name}"
            if temp_line in public_queue:
                public_queue.remove(temp_line)
            members = [f"{callback.from_user.chat_id},{callback.from_user.first_name}"]
            memberlist = queue_members[callback.from_user.id]
            for i in range(1, len(memberlist)):
                members.append(memberlist[i])
        if len(members) > 3:
            for member in members:
                member_chat_id = member.split(',',1)
                waiting_lobby.pop(member_chat_id[0])
            queue_members.pop(callback.from_user.id)
            asyncio.create_task(room(bot, members))
        else:
            await bot.send_message(callback.from_user.chat_id, "⚠ حداقل تعداد برای شروع 4 نفر است!")
    
    elif callback.data == "mafiabot:deleteparty":
        members = [callback.from_user.chat_id]
        memberlist = []
        async with queue_lock:
            if callback.from_user.id not in queue_members:
                await bot.send_message(callback.from_user.chat_id, "⚠ شما لیدر گروهی نیستید!")
                return
            temp_line = f"{callback.from_user.id},{callback.from_user.first_name}"
            if temp_line in public_queue:
                public_queue.remove(temp_line)
            for i in queue_members[callback.from_user.id]:
                chatid = i.split(',',1)
                waiting_lobby.pop(chatid[0])
                await bot.send_message(chatid[0],"📛 گروه توسط لیدر حذف شد!")
            queue_members.pop(callback.from_user.id)

    elif callback.data == "mafiabot:exitparty" and (callback.from_user.chat_id in waiting_lobby):
        inviter = waiting_lobby[callback.from_user.chat_id]
        async with queue_lock:
            temp_member = f"{callback.from_user.chat_id},{callback.from_user.first_name}"
            ids = queue_members[inviter]
            if temp_member in queue_members[inviter]:
                queue_members[inviter].remove(temp_member)
            else:
                await bot.send_message(callback.from_user.chat_id, "⚠ شما به گروهی دعوت نشده اید!")
                return
        for i in ids:
            temp = i.split(',',1)
            await bot.send_message(temp[0],f"⭕ {callback.from_user.first_name} از گروه خارج شد.")
        waiting_lobby.pop(callback.from_user.chat_id)
        await bot.send_message(callback.from_user.chat_id, "🚦 از گروه خارج شدید.")

    elif callback.from_user.chat_id in waiting_lobby:
        if waiting_lobby[callback.from_user.chat_id] == callback.from_user.id:
            await bot.send_message(callback.from_user.chat_id, "‼ شما لیدر گروه هستید! ابتدا بازی را شروع کنید.",components=leader_keyboard)
        else:
            await bot.send_message(callback.from_user.chat_id, "‼ شما در یک انتظار شروع بازی هستید! ابتدا از گروه خارج شوید.", components=invited_keyboard)

    elif callback.data.startswith("mafiabot:create-"):
        if callback.data == "mafiabot:create-public":
            async with queue_lock:
                public_queue.append(f"{callback.from_user.id},{callback.from_user.first_name}")
        await callback.message.edit(
            text=f"⚔ اینو برا دوستات بفرست:\nhttps://ble.ir/{BOT_USERNAME}?start=party-{callback.from_user.id}",
            components=leader_keyboard)
        async with queue_lock:
            queue_members[callback.from_user.id] = [f"{callback.from_user.chat_id},{callback.message.message_id},{callback.from_user.first_name}"]
        waiting_lobby[callback.from_user.chat_id] = callback.from_user.id
    
    elif callback.data.startswith("mafiaadmin:") and str(callback.from_user.id) in ADMINS_ID:
        if callback.data == "mafiaadmin:groups":
            await active_groups(bot, queue_members, callback)
        elif callback.data == "mafiaadmin:rooms":
            await bot.send_message(callback.from_user.chat_id, f"🕹 {len(active_rooms)} اتاق فعال وجود دارند.")
        elif callback.data == "mafiaadmin:users":
            await last_users(bot, callback)

    elif callback.data.startswith("mafiaroom:"):
        chat_id = str(callback.from_user.chat_id)
        for room_id, game_room in active_rooms.items():
            async with room_locks.get(room_id, asyncio.Lock()):
                for member in game_room.members:
                    member_chat_id, _ = member.split(',', 1)
                    if member_chat_id == chat_id:
                        if game_room.game_active and callback.data:
                            if callback.data == "mafiaroom:like":
                                await game_room.handle_react(chat_id, callback, True)
                            elif callback.data == "mafiaroom:dislike":
                                await game_room.handle_react(chat_id, callback, False)
                            else:
                                await bot.send_message(chat_id,"❗ در بازی فعالی نیستید!")
                        break