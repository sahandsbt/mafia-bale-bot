#======================(INIT)======================
from collections import defaultdict
from dotenv import load_dotenv
import bale
import asyncio
import random
import os
load_dotenv()
bot = bale.Bot(token = os.getenv("BOT_TOKEN"))

#======================(KEYBOARDS)======================
start_keyboard = bale.MenuKeyboardMarkup()
start_keyboard.add(bale.MenuKeyboardButton("🎡 ساخت گروه 🎡"),row=1)
start_keyboard.add(bale.MenuKeyboardButton("❓ راهنما"),row=2)
start_keyboard.add(bale.MenuKeyboardButton("☎ پشتیبانی"),row=2)

leader_keyboard = bale.MenuKeyboardMarkup()
leader_keyboard.add(bale.MenuKeyboardButton("🎮 شروع بازی 🎮"),row=1)

invited_keyboard = bale.MenuKeyboardMarkup()
invited_keyboard.add(bale.MenuKeyboardButton("🚪 خروج 🚪"),row=1)

null_keyboard = bale.MenuKeyboardMarkup()

class GameRoom:
    def __init__(self, members_list):
        self.members = members_list.copy()
        self.roles = {}
        self.current_talker = None
        self.current_talker_name = None
        self.game_active = True
        self.maf_count = 0
        self.cit_count = 0
        self.day_phase = True
        self.votes = defaultdict(set)
        self.vote_lock = asyncio.Lock()
        self.dead_players = set()
        self.alive_players = self.members.copy()
        
    async def assign_roles(self):
        members = self.members.copy()
        special_roles = ['کارآگاه','دکتر'
                        #  ,'اسنایپر','پدرخوانده','دکتر مافیا' #===============(Remove comment)
                         ]
        for role_name in special_roles:
            ind = random.randint(0, len(members) - 1)
            self.roles[members[ind]] = role_name
            members.pop(ind)
        maf_count = 1 + len(members) // 3
        self.maf_count = maf_count
        for _ in range(maf_count):
            if members:
                maf_ind = random.randint(0, len(members) - 1)
                self.roles[members[maf_ind]] = 'مافیای ساده'
                members.pop(maf_ind)
        self.cit_count = len(members) + 3
        for member in members:
            self.roles[member] = 'شهروند ساده'
        for member in self.members:
            chat_id = member.split(',', 1)
            await bot.send_message(chat_id[0], f"🎭 بازی شروع شد! نقش شما {self.roles[member]} است.",components=null_keyboard)
        role_count = {}
        for role in self.roles.values():
            role_count[role] = role_count.get(role, 0) + 1
        
        # summary = "📊 خلاصه نقش‌ها:\n"
        # for role, count in role_count.items():
        #     summary += f"• {role}: {count} نفر\n"
        # await self.broadcast_message(summary)
    
    async def broadcast_message(self, message, exclude_talker = False, exclude_dead = False):
        for member in self.members:
            chat_id = member.split(',', 1)
            if exclude_talker and self.current_talker == chat_id[0]:
                continue
            if exclude_dead and member in self.dead_players:
                continue
            await bot.send_message(chat_id[0], message)
    
    async def start_talking_turn(self, member: str):
        chat_id, name = member.split(',', 1)
        if member in self.dead_players:
            return
        self.current_talker = chat_id
        self.current_talker_name = name
        await self.broadcast_message(f"🗣️ نوبت حرف زدن {name} است.",exclude_talker=True,exclude_dead=True)
        await bot.send_message(chat_id,"⏳ نوبت حرف زدن شماست. تا ۳۰ ثانیه تمام پیام‌های شما برای بقیه ارسال می‌شود.")
        asyncio.create_task(self.end_talking_turn())
    
    async def end_talking_turn(self):
        await asyncio.sleep(10) #++++++++++++++++++++++++++++++++++++++++++++++++++(30)
        if self.current_talker:
            await self.broadcast_message(
                f"⏰ زمان صحبت {self.current_talker_name} به پایان رسید.",
                exclude_talker=True,exclude_dead=True)
            await bot.send_message(self.current_talker,"⏰ زمان صحبت شما به پایان رسید.")
            self.current_talker = None
            self.current_talker_name = None
    
    async def handle_player_message(self, chat_id, message):
        if not self.game_active:
            return False
        member_str = self.get_member_by_chat_id(chat_id)
        if member_str and member_str in self.dead_players:
            await bot.send_message(chat_id, "❌ شما مرده‌اید و نمی‌توانید صحبت کنید!")
            return True
        if self.current_talker == chat_id:
            await self.broadcast_message(f"📢 {self.current_talker_name}: {message}",exclude_talker=True)
            return True
        return False
    
    def get_member_by_chat_id(self, chat_id):
        for member in self.members:
            member_chat_id, _ = member.split(',', 1)
            if member_chat_id == chat_id:
                return member
        return None
    
    async def start_voting(self):
        voting_keyboard = bale.MenuKeyboardMarkup()
        for member in self.members:
            name_id = member.split(',', 1)
            voting_keyboard.add(bale.MenuKeyboardButton(f"رای به {name_id[1]}"))
        for member in self.members:
            chat_id = member.split(',', 1)
            await bot.send_message(chat_id[0], f"🗳️ مرحله رای‌گیری شروع شد!\n"
            "برای رای دادن از دکمه ها استفاده کنید.",components=voting_keyboard)
        await asyncio.sleep(20)
        await self.count_votes()
    
    async def handle_vote(self, voter_chat_id, vote_input):
        async with self.vote_lock:
            voter_member = self.get_member_by_chat_id(voter_chat_id)
            if not voter_member or voter_member in self.dead_players:
                await bot.send_message(voter_chat_id, "❌ شما مرده‌اید و نمی‌توانید رای دهید!")
                return False
            if not self.day_phase:
                await bot.send_message(voter_chat_id, "❌ الان مرحله رای‌گیری نیست!")
                return False
            for i in self.members:
                target_chat_id, target_name = i.split(',', 1)
                if target_name == vote_input[7:]:
                    self.votes[voter_chat_id].add(target_chat_id)
                    await bot.send_message(voter_chat_id,f"✅ رای شما به {target_name} ثبت شد!")
                    return True
            await bot.send_message(voter_chat_id, "❌ رای نامعتبر! لطفا از گزینه ها انتخاب کنید")
            return False
    
    async def count_votes(self):
        if not self.votes:
            await self.broadcast_message("⏭️ هیچ رایی ثبت نشد. به شب می‌رویم...", exclude_dead=True)
            self.day_phase = False
            self.votes.clear()
            return
        vote_count = {}
        for target_chat_id_list in self.votes.values():
            for target_chat_id in target_chat_id_list:
                vote_count[target_chat_id] = vote_count.get(target_chat_id, 0) + 1
        counts_str = ""
        for i in vote_count:
            vote_targ = self.get_member_by_chat_id(i).split(',', 1)
            counts_str += f"⚜ {vote_targ[1]}: {vote_count[i]} رای\n"
        await self.broadcast_message(counts_str)
        max_votes = max(vote_count.values())
        candidates = [chat_id for chat_id, count in vote_count.items() if count == max_votes]
        if len(candidates) > 1:
            await self.broadcast_message("⚖️ تساوی در آراء! هیچکس اعدام نمی‌شود.", exclude_dead=True)
        else:
            target_chat_id = candidates[0]
            target_member = self.get_member_by_chat_id(target_chat_id)
            if target_member:
                target_chat_id, target_name = target_member.split(',', 1)
                role = self.roles.get(target_member, "ناشناخته")
                self.dead_players.add(target_member)
                if target_member in self.alive_players:
                    self.alive_players.remove(target_member)
                if role in ['مافیای ساده', 'پدرخوانده', 'دکتر مافیا']:
                    self.maf_count -= 1
                else:
                    self.cit_count -= 1
                await self.broadcast_message(f"💀 {target_name} اعدام شد!",exclude_dead=True)
        self.votes.clear()
        self.day_phase = False
        await self.broadcast_message("🌙 شب شد...")
    
    async def night_phase(self):
        await self.broadcast_message(
            "🌙 نقش‌های ویژه اقدامات خود را انجام دهند.\n"
            "مهلت: ۶۰ ثانیه",
            exclude_dead=True
        )
        await asyncio.sleep(30)
        await self.process_night_actions()
        self.day_phase = True
        await self.broadcast_message(f"☀️ صبح شد!")
    
    async def process_night_actions(self):
        #nightttttttttttt
        pass
    
    async def check_game_end(self) -> bool:
        if self.maf_count == 0:
            await self.broadcast_message("🎉 بازی تمام شد! شهروندان برنده شدند!")
            return True
        elif self.maf_count >= self.cit_count:
            await self.broadcast_message("😈 بازی تمام شد! مافیا برنده شد!")
            return True
        return False
    
    async def run_game(self):
        await self.assign_roles()
        while self.game_active:
            self.day_phase = True
            for member in self.alive_players:
                if not self.game_active:
                    break
                await self.start_talking_turn(member)
                await asyncio.sleep(12) #++++++++++++++++++++++++++++++++++++++++++++++++++(32)
                if not self.game_active:
                    break
            if self.game_active:
                await self.start_voting()
            if await self.check_game_end():
                self.game_active = False
                break
            if self.game_active:
                await self.night_phase()
            if await self.check_game_end():
                self.game_active = False
                break

active_rooms = {}
room_locks = {}

async def room(members_list):
    room_id = str(hash(tuple(members_list)))
    room_locks[room_id] = asyncio.Lock()
    game_room = GameRoom(members_list)
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

# ====================== (LISTENER) =======================
@bot.listen("on_message")
async def when_message(message: bale.Message):
    chat_id = str(message.chat_id)
    if message.text.startswith("رای به"):
        target_room = None
        for room_id, game_room in active_rooms.items():
            for member in game_room.members:
                member_chat_id, _ = member.split(',', 1)
                if member_chat_id == chat_id:
                    target_room = game_room
                    break
            if target_room:
                break
        if target_room and target_room.game_active:
            await target_room.handle_vote(chat_id, message.text)

    for room_id, game_room in active_rooms.items():
        async with room_locks.get(room_id, asyncio.Lock()):
            for member in game_room.members:
                member_chat_id, _ = member.split(',', 1)
                if member_chat_id == chat_id:
                    if game_room.game_active and message.text and not message.text.startswith('/'):
                        handled = await game_room.handle_player_message(chat_id, message.text)
                        if handled:
                            return
                    break

    if "/start" in message.text:
        if message.text == "/start":
            await message.reply(
                text="سلام خوش اومدی به بات بازی مافیا🥹\nبرای شروع بازی🎮 کلمه /start رو بفرست😎",
                components=start_keyboard
            )
        else:
            invite_code_list = message.text.split()
            invite_code = invite_code_list[1]
            
            if message.from_user.id != invite_code:
                room_file = open(f"{invite_code}.txt", 'r')
                ids = room_file.readlines()
                new_line = f"{message.from_user.chat_id},{message.from_user.first_name}\n"
                
                if new_line not in ids:
                    with open(f"{invite_code}.txt", 'a') as f:
                        f.write(f"{message.from_user.chat_id},{message.from_user.first_name}\n")
                    
                    meschat_id = ids[0].split(',')
                    memberlist = f"\n🔅{message.from_user.first_name}\n"
                    for i in range(1, len(ids)):
                        temp2 = ids[i].split(sep=',', maxsplit=1)
                        memberlist += f"🔅{temp2[1]}"
                    
                    await bot.edit_message(
                        meschat_id[0],
                        meschat_id[1][:-1],
                        "افراد اضافه شده:" + memberlist,
                        components=leader_keyboard
                    )
                    await message.reply(
                        text="به بازی اضافه شدی. وایستا تا بازی شروع شه.",
                        components=invited_keyboard
                    )
                room_file.close()
    
    elif message.text == "🎡 ساخت گروه 🎡":
        await message.reply(
            text=f"اینو برا دوستات بفرست:\nhttps://ble.ir/sasabot?start={message.from_user.id}",
            components=leader_keyboard
        )
        with open(f"{message.from_user.id}.txt", 'w') as f:
            f.write(f"{message.chat_id},{int(message.message_id) + 1}\n")
    
    elif message.text == "🎮 شروع بازی 🎮":
        members = [f"{message.from_user.chat_id},{message.from_user.first_name}"]
        with open(f"{message.from_user.id}.txt", 'r') as f:
            memberlist = f.readlines()
        os.remove(f"{message.from_user.id}.txt")
        
        for i in range(1, len(memberlist)):
            members.append(memberlist[i][:-1])
        
        if len(members) > 1: #=================================================( >4 )
            asyncio.create_task(room(members))
            await message.reply("بازی شروع شد! نقش‌ها در حال تخصیص هستند...")
        else:
            await message.reply(text="حداقل تعداد برای شروع ۵ نفر است!")
    
    elif message.text == "🚪 خروج 🚪":
        await message.reply(text="Nemishe")
    
bot.run()