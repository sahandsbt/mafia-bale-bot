"""Game room model"""

import bale
import random
import asyncio
from collections import defaultdict

class GameRoom:
    def __init__(self, bot: bale.Bot, members_list):
        self.bot = bot
        self.members = members_list.copy()
        self.roles = {}
        self.current_talker = None
        self.current_talker_name = None
        self.game_active = True
        self.execute_condidates = []
        self.maf_count = 0
        self.cit_count = 0
        self.vote_phase = False
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
        maf_count = len(members) // 3 + 2
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
            await self.bot.send_message(chat_id[0], f"🎭 بازی شروع شد! نقش شما {self.roles[member]} است.",components=None)
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
            await self.bot.send_message(chat_id[0], message)
    
    async def start_talking_turn(self, member):
        chat_id, name = member.split(',', 1)
        if member in self.dead_players:
            return
        self.current_talker = chat_id
        self.current_talker_name = name
        if self.execute_condidates:
            await self.broadcast_message(f"🗣️ نوبت دفاعیه {name} است.",exclude_talker=True,exclude_dead=True)
            await self.bot.send_message(chat_id,"⏳ نوبت دفاعیه شماست. تا 45 ثانیه تمام پیام‌های شما برای بقیه ارسال می‌شود.")
        else:
            await self.broadcast_message(f"🗣️ نوبت حرف زدن {name} است.",exclude_talker=True,exclude_dead=True)
            await self.bot.send_message(chat_id,"⏳ نوبت حرف زدن شماست. تا 30 ثانیه تمام پیام‌های شما برای بقیه ارسال می‌شود.")
        asyncio.create_task(self.end_talking_turn())
    
    async def end_talking_turn(self):
        if self.execute_condidates:
            await asyncio.sleep(25) #++++++++++++++++++++++++++++++++++++++++++++++++++(45)
        else:
            await asyncio.sleep(10) #++++++++++++++++++++++++++++++++++++++++++++++++++(30)
        if self.current_talker:
            await self.broadcast_message(
                f"⏰ زمان صحبت {self.current_talker_name} به پایان رسید.",
                exclude_talker=True,exclude_dead=True)
            await self.bot.send_message(self.current_talker,"⏰ زمان صحبت شما به پایان رسید.")
            self.current_talker = None
            self.current_talker_name = None
    
    async def handle_player_message(self, chat_id, message):
        if not self.game_active:
            return False
        member_str = self.get_member_by_chat_id(chat_id)
        if member_str and member_str in self.dead_players:
            await self.bot.send_message(chat_id, "❌ شما مرده‌اید و نمی‌توانید صحبت کنید!")
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
        if self.execute_condidates:
            for member in self.execute_condidates:
                name_id = member.split(',', 1)
                voting_keyboard.add(bale.MenuKeyboardButton(f"رای به {name_id[1]}"))
                await self.start_talking_turn(member)
                await asyncio.sleep(27) #++++++++++++++++++++++++++++++++++++++++++++++++++(47)
        else:
            for member in self.alive_players:
                name_id = member.split(',', 1)
                voting_keyboard.add(bale.MenuKeyboardButton(f"رای به {name_id[1]}"))
        self.vote_phase = True
        for member in self.alive_players:
            chat_id = member.split(',', 1)
            await self.bot.send_message(chat_id[0], f"🗳️ رای‌گیری شروع شد!\n"
            "برای رای دادن از دکمه ها استفاده کنید. سی ثانیه فرصت دارید",components=voting_keyboard)
        await asyncio.sleep(20) #============================================= (30)
        await self.count_votes()
    
    async def handle_vote(self, voter_chat_id, vote_input):
        async with self.vote_lock:
            voter_member = self.get_member_by_chat_id(voter_chat_id)
            if not self.vote_phase:
                await self.bot.send_message(voter_chat_id, "❌ الان مرحله رای‌گیری نیست!")
                return False
            if not voter_member or voter_member in self.dead_players:
                await self.bot.send_message(voter_chat_id, "❌ شما مرده‌اید و نمی‌توانید رای دهید!")
                return False
            
            for i in self.members:
                target_chat_id, target_name = i.split(',', 1)
                if target_name.rstrip() == vote_input[7:]:
                    if self.execute_condidates:
                        if i in self.execute_condidates:
                            if self.votes[voter_chat_id]:
                                await self.bot.send_message(voter_chat_id,f"❌ شما قبلا رای دادید!")
                            else:
                                self.votes[voter_chat_id].add(target_chat_id)
                                await self.bot.send_message(voter_chat_id,f"✅ رای شما به {target_name} ثبت شد!")
                        else:
                            await self.bot.send_message(voter_chat_id, "❌ رای نامعتبر! لطفا از گزینه ها انتخاب کنید")
                    else:
                        self.votes[voter_chat_id].add(target_chat_id)
                        voter_name = voter_member.split(',',1)
                        await self.broadcast_message(f"🎯 رای {voter_name[1]} به {target_name} ثبت شد!")

                    return True
            await self.bot.send_message(voter_chat_id, "❌ رای نامعتبر! لطفا از گزینه ها انتخاب کنید")
            return False
    
    async def count_votes(self):
        if not self.votes:
            await self.broadcast_message("⏭️ هیچ رایی ثبت نشد. به شب می‌رویم...", exclude_dead=True)
            self.vote_phase = False
            self.votes.clear()
            self.execute_condidates.clear()
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
        if self.execute_condidates:
            max_votes = max(vote_count.values())
            candidates = [chat_id for chat_id, count in vote_count.items() if count == max_votes]
            if len(candidates) > 1:
                await self.broadcast_message("⚖️ تساوی در آراء! هیچکس اعدام نمی‌شود.")
            else:
                target_chat_id = candidates[0]
                target_member = self.get_member_by_chat_id(target_chat_id)
                if target_member in self.alive_players:
                    await self.execution(target_member)
            self.votes.clear()
            self.execute_condidates.clear()
            self.vote_phase = False
            await self.broadcast_message("🌙 شب شد...")
        else:
            for exe_vote in vote_count:
                if int(vote_count[exe_vote]) >= ((len(self.alive_players) + 1) // 2):
                    self.execute_condidates.append(self.get_member_by_chat_id(exe_vote))
            self.vote_phase = False
            self.votes.clear()
            await self.start_voting()

    async def execution(self,target_member):
        target_chat_id, target_name = target_member.split(',', 1)
        role = self.roles.get(target_member, "ناشناخته")
        self.dead_players.add(target_member)
        self.alive_players.remove(target_member)
        if role in ['مافیای ساده', 'پدرخوانده', 'دکتر مافیا']:
            self.maf_count -= 1
        else:
            self.cit_count -= 1
        await self.broadcast_message(f"💀 {target_name} اعدام شد!")

    async def night_phase(self):
        await self.broadcast_message(
            "🌙 نقش‌های ویژه اقدامات خود را انجام دهند.\n"
            "مهلت: ۶۰ ثانیه",
            exclude_dead=True
        )
        await asyncio.sleep(30)
        await self.process_night_actions()
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