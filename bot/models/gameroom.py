"""Game room model"""

import bale
import random
import asyncio
from collections import defaultdict
from typing import List

class GameRoom:
    def __init__(self, bot: bale.Bot, members_list: List[str]):
        self.bot = bot
        self.members = members_list.copy()
        self.roles = {}
        self.current_talker = None
        self.current_talker_name = None
        self.game_active = True
        self.first_day = True
        self.execute_condidates = []
        self.maf_count = 0
        self.cit_count = 0
        self.mafia_phase = False
        self.vote_phase = False
        self.godfa_phase = False
        self.snipe_phase = False
        self.doctor_phase = False
        self.lecter_phase = False
        self.detect_phase = False
        self.inquire_phase = False
        self.chaos_phase = False
        self.handshake_phase = False
        self.godfather_prot = True
        self.doctor_selfsave = True
        self.lecter_selfsave = True
        self.chaos_win = []
        self.godfather = ""
        self.maf_leader = ""
        self.doctor = ""
        self.sniper = ""
        self.lecter = ""
        self.detective = ""
        self.votes = defaultdict(set)
        self.vote_lock = asyncio.Lock()
        self.dead_players = set()
        self.inquired_roles = []
        self.inquire_vote = []
        self.left_inquire = 2
        self.alive_players = self.members.copy()
        self.mafia_team = []
        self.night_target = ""
        self.sniper_target = ""
        
    async def assign_roles(self):
        members = self.members.copy()
        all_roles_str = "➰ نقش‌های داخل بازی: "
        special_roles = ['کارآگاه','دکتر','پدرخوانده','اسنایپر','شهروند ساده','دکتر مافیا']
        for role_name in special_roles:
            if members:
                ind = random.randint(0, len(members) - 1)
                self.roles[members[ind]] = role_name
                if role_name != 'شهروند ساده':
                    all_roles_str += f"{role_name}، "
                if role_name in ['پدرخوانده','دکتر مافیا']:
                    self.maf_count +=1
                    self.mafia_team.append(members[ind])
                else:
                    self.cit_count +=1
                members.pop(ind)
        simple_maf_count = 0
        if len(members) > 2:
            simple_maf_count = (len(members) - 1) // 3
            all_roles_str += f"{str(simple_maf_count)} × مافیای ساده و "
        self.maf_count += simple_maf_count
        for _ in range(simple_maf_count):
            maf_ind = random.randint(0, len(members) - 1)
            self.roles[members[maf_ind]] = 'مافیای ساده'
            self.mafia_team.append(members[maf_ind])
            members.pop(maf_ind)
        self.cit_count += len(members)
        if len(self.members) > 4:
            all_roles_str += f"{str(len(members)+1)} × شهروند ساده."
        else:
            all_roles_str = all_roles_str[:-2] + "."
        for member in members:
            self.roles[member] = 'شهروند ساده'
        for member in self.members:
            chat_id = member.split(',', 1)
            await self.bot.send_message(chat_id[0], f"🎭 بازی شروع شد! نقش شما {self.roles[member]} است.\n\n{all_roles_str}",components=None)
        role_count = {}
        for role in self.roles.values():
            role_count[role] = role_count.get(role, 0) + 1
    
    async def broadcast_message(self, message, exclude_talker = False, exclude_dead = False, component = None):
        for member in self.members:
            chat_id = member.split(',', 1)
            if exclude_talker and self.current_talker == chat_id[0]:
                continue
            if exclude_dead and member in self.dead_players:
                continue
            await self.bot.send_message(chat_id[0], message, components=component)
    
    async def start_talking_turn(self, member):
        chat_id, name = member.split(',', 1)
        if member in self.dead_players:
            return
        self.current_talker = chat_id
        self.current_talker_name = name
        if self.execute_condidates:
            await self.broadcast_message(f"🗣️ نوبت دفاعیه {name} است.",exclude_talker=True,exclude_dead=True)
            await self.bot.send_message(chat_id,"⏳ نوبت دفاعیه شماست. تا 60 ثانیه تمام پیام‌های شما برای بقیه ارسال می‌شود.")
        else:
            await self.broadcast_message(f"🗣️ نوبت حرف زدن {name} است.",exclude_talker=True,exclude_dead=True)
            await self.bot.send_message(chat_id,"⏳ نوبت حرف زدن شماست. تا 45 ثانیه تمام پیام‌های شما برای بقیه ارسال می‌شود.")
        asyncio.create_task(self.end_talking_turn())
    
    async def end_talking_turn(self):
        if self.execute_condidates:
            await asyncio.sleep(60)
        else:
            await asyncio.sleep(45)
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
        if self.mafia_phase and (member_str in self.mafia_team):
            talker = member_str.split(',', 1)
            for member in self.mafia_team:
                temp_chat_id = member.split(',', 1)
                if member != member_str:
                    await self.bot.send_message(temp_chat_id[0], f"📢 {talker[1]}: {message}")
                    return True
            return True
        if self.chaos_phase:
            talker = member_str.split(',', 1)
            for member in self.members:
                temp_chat_id = member.split(',', 1)
                if member != member_str:
                    await self.bot.send_message(temp_chat_id[0], f"📢 {talker[1]}: {message}")
            return True
        await self.bot.send_message(chat_id, "❌ نوبت صحبت شما نیست!")
    
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
                current_row = (self.execute_condidates.index(member) + 3) // 3
                voting_keyboard.add(bale.MenuKeyboardButton(f"رای به {name_id[1]}"),row=current_row)
                await self.start_talking_turn(member)
                await asyncio.sleep(62)
        else:
            for member in self.alive_players:
                name_id = member.split(',', 1)
                current_row = (self.alive_players.index(member) + 3) // 3
                voting_keyboard.add(bale.MenuKeyboardButton(f"رای به {name_id[1]}"),row=current_row)
        self.vote_phase = True
        for member in self.alive_players:
            chat_id = member.split(',', 1)
            await self.bot.send_message(chat_id[0], f"🗳️ رای‌گیری شروع شد!\n"
            "برای رای دادن از دکمه ها استفاده کنید. 30 ثانیه فرصت دارید",components=voting_keyboard)
        await asyncio.sleep(30)
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
            
            for i in self.alive_players:
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
            await self.broadcast_message("⏭️ هیچ رایی ثبت نشد.")
            self.vote_phase = False
            self.votes.clear()
            self.execute_condidates.clear()
            return
        vote_count = {}
        for target_chat_id_list in self.votes.values():
            for target_chat_id in target_chat_id_list:
                vote_count[target_chat_id] = vote_count.get(target_chat_id, 0) + 1
        counts_str = "🔮 تعداد آرا:\n\n"
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
                if max_votes >= ((len(self.alive_players) + 1) // 2):
                    if target_member in self.alive_players:
                        await self.execution(target_member)
                else:
                    target_name = target_member.split(',', 1)
                    await self.broadcast_message(f"⚖️ {target_name[1]} رای کافی نیاورد.")
            self.votes.clear()
            self.execute_condidates.clear()
            self.vote_phase = False
        else:
            for exe_vote in vote_count:
                if int(vote_count[exe_vote]) >= ((len(self.alive_players) + 1) // 2):
                    self.execute_condidates.append(self.get_member_by_chat_id(exe_vote))
            self.vote_phase = False
            self.votes.clear()
            if self.execute_condidates:
                await self.start_voting()
            else:
                await self.broadcast_message("⚖️ کسی رای کافی نیاورد.")

    async def execution(self,target_member,night_mode=False):
        self.dead_players.add(target_member)
        self.alive_players.remove(target_member)
        if target_member in self.mafia_team:
            self.maf_count -= 1
            self.mafia_team.remove(target_member)
        else:
            self.cit_count -= 1
        if not night_mode:
            target_chat_id, target_name = target_member.split(',', 1)
            await self.broadcast_message(f"💀 {target_name} اعدام شد!")

    async def night_phase(self):
        mafia_team_str = ""
        for member in self.mafia_team:
            temp = member.split(',', 1)
            mafia_team_str+=f"◼{temp[1]}\n"
        for member in self.alive_players:
            chat_id = member.split(',', 1)
            if member in self.mafia_team:
                await self.bot.send_message(chat_id[0], f"🎩 گروه مافیا 60 ثانیه فرصت مشورت و ارسال پیام به یکدیگر دارند.\n🔔 اعضای مافیا:\n{mafia_team_str}")
            else:
                await self.bot.send_message(chat_id[0], "🎩 گروه مافیا در حال مشورت هستند.")
        self.mafia_phase = True
        await asyncio.sleep(60)
        if not self.first_day:
            await self.mafia_kill()
            await asyncio.sleep(20)
            self.godfa_phase = False
            if 'اسنایپر' not in self.inquired_roles:
                await self.sniper_snipe()
                await asyncio.sleep(20)
                self.snipe_phase = False
            if 'دکتر' not in self.inquired_roles:
                await self.doctor_save()
                await asyncio.sleep(20)
                self.doctor_phase = False
            if 'دکتر مافیا' not in self.inquired_roles and len(self.members) > 5:
                await self.lecter_prot()
                await asyncio.sleep(20)
                self.lecter_phase = False
            if 'کارآگاه' not in self.inquired_roles:
                await self.detective_ask()
                await asyncio.sleep(20)
                self.detect_phase = False
            await self.night_events()
            if await self.check_game_end():
                self.game_active = False
            if self.left_inquire > 0:
                await self.day_inquire()
        else:
            self.mafia_phase = False
            await self.broadcast_message("☀️ صبح شد!")
            self.first_day = False
    
    async def mafia_kill(self):
        self.mafia_phase = False
        self.godfa_phase = True
        self.godfather = ""
        self.maf_leader = ""
        for member in self.alive_players:
            if self.roles[member] == 'پدرخوانده':
                self.godfather = member
                self.maf_leader = member
                break
        if not self.maf_leader:
            for member in self.alive_players:
                if self.roles[member] == 'دکتر مافیا':
                    self.maf_leader = member
                    break
        if not self.maf_leader:
            for member in self.alive_players:
                if self.roles[member] == 'مافیای ساده':
                    self.maf_leader = member
                    break
        leader_id, leader_name = self.maf_leader.split(',', 1)
        godfather_keyboard = bale.MenuKeyboardMarkup()
        for member in self.alive_players:
            name_id = member.split(',', 1)
            current_row = (self.alive_players.index(member) + 3) // 3
            godfather_keyboard.add(bale.MenuKeyboardButton(f"کشتن {name_id[1]}"),row=current_row)
            if member != self.maf_leader:
                await self.bot.send_message(name_id[0],"🚬 مافیا آماده شلیک است!")
        await self.bot.send_message(leader_id,"🔫 شکار شب را تا 20 ثانیه دیگر انتخاب کنید!",components=godfather_keyboard)

    async def handle_kill(self, killer_chat_id, kill_input):
        async with self.vote_lock:
            killer_member = self.get_member_by_chat_id(killer_chat_id)
            if killer_member != self.maf_leader:
                await self.bot.send_message(killer_chat_id, "❌ شما لیدر مافیا نیستید!")
                return False
            if not self.godfa_phase:
                await self.bot.send_message(killer_chat_id, "❌ الان وقت شکار نیست!")
                return False
            for i in self.alive_players:
                target_chat_id, target_name = i.split(',', 1)
                if target_name.rstrip() == kill_input[5:]:
                    self.night_target = i
                    for member in self.mafia_team:
                        temp_chat_id = member.split(',', 1)
                        await self.bot.send_message(temp_chat_id[0], f"☠ به {target_name} شلیک شد!")
                    self.godfa_phase = False
                    return True
            await self.bot.send_message(killer_chat_id, "❌ لطفا از گزینه ها انتخاب کنید")
            return False
        
    async def sniper_snipe(self):
        self.snipe_phase = True
        self.sniper = ""
        for member in self.alive_players:
            if self.roles[member] == 'اسنایپر':
                self.sniper = member
        for member in self.alive_players:
            if member != self.detective:
                name_id = member.split(',', 1)
                await self.bot.send_message(name_id[0],"🏹 اسنایپر بیدار شد!")
        if self.sniper:
            sniper_id, sniper_name = self.sniper.split(',', 1)
            sniper_keyboard = bale.MenuKeyboardMarkup()
            for member in self.alive_players:
                name_id = member.split(',', 1)
                current_row = (self.alive_players.index(member) + 3) // 3
                sniper_keyboard.add(bale.MenuKeyboardButton(f"اسنایپ {name_id[1]}"),row=current_row)
            await self.bot.send_message(sniper_id,"🔫 در صورت تمایل اسنایپ شب را تا 20 ثانیه دیگر انتخاب کنید!",components=sniper_keyboard)

    async def handle_snipe(self, sniper_chat_id, kill_input):
        async with self.vote_lock:
            sniper_member = self.get_member_by_chat_id(sniper_chat_id)
            if sniper_member != self.sniper:
                await self.bot.send_message(sniper_chat_id, "❌ شما اسنایپر نیستید!")
                return False
            if not self.snipe_phase:
                await self.bot.send_message(sniper_chat_id, "❌ الان وقت اسنایپ نیست!")
                return False
            for i in self.alive_players:
                target_chat_id, target_name = i.split(',', 1)
                if target_name.rstrip() == kill_input[7:]:
                    if i in self.mafia_team:
                        self.sniper_target = i
                    else:
                        self.sniper_target = self.sniper
                    await self.bot.send_message(sniper_chat_id, f"☠ به {target_name} شلیک شد!")
                    self.sniper_phase = False
                    return True
            await self.bot.send_message(sniper_chat_id, "❌ لطفا از گزینه ها انتخاب کنید")
            return False
    
    async def doctor_save(self):
        self.doctor_phase = True
        self.doctor = ""
        for member in self.alive_players:
            if self.roles[member] == 'دکتر':
                self.doctor = member
        for member in self.alive_players:
            if member != self.detective:
                name_id = member.split(',', 1)
                await self.bot.send_message(name_id[0],"💞 دکتر بیدار شد!")
        if self.doctor:
            doci_id, doci_name = self.doctor.split(',', 1)
            doctor_keyboard = bale.MenuKeyboardMarkup()
            for member in self.alive_players:
                name_id = member.split(',', 1)
                current_row = (self.alive_players.index(member) + 3) // 3
                doctor_keyboard.add(bale.MenuKeyboardButton(f"نجات {name_id[1]}"),row=current_row)
            await self.bot.send_message(doci_id,"💞 تا 20 ثانیه دیگر انتخاب کنید چه کسی را نجات میدهید!",components=doctor_keyboard)

    async def handle_save(self, doctor_chat_id, save_input):
        async with self.vote_lock:
            doctor_member = self.get_member_by_chat_id(doctor_chat_id)
            if doctor_member != self.doctor:
                await self.bot.send_message(doctor_chat_id, "❌ شما دکتر نیستید!")
                return False
            if not self.doctor_phase:
                await self.bot.send_message(doctor_chat_id, "❌ الان وقت نجات نیست!")
                return False
            for i in self.alive_players:
                save_chat_id, save_name = i.split(',', 1)
                if save_name.rstrip() == save_input[5:]:
                    if i == self.doctor:
                        if self.doctor_selfsave:
                            self.doctor_selfsave = False
                        else:
                            await self.bot.send_message(doctor_chat_id, f"⚰ قبلا یکبار خودتان را نجات دادید! شخص دیگری انتخاب کنید.")
                            return False
                    if i == self.night_target:
                        self.night_target = ""
                    if i == self.sniper_target and self.sniper_target != self.sniper:
                        self.sniper_target = ""
                    await self.bot.send_message(doctor_chat_id, f"💗 {save_name} شفا یافت.")
                    self.doctor_phase = False
                    return True
            await self.bot.send_message(doctor_chat_id, "❌ لطفا از گزینه ها انتخاب کنید")
            return False
    
    async def lecter_prot(self):
        self.lecter_phase = True
        self.lecter = ""
        for member in self.alive_players:
            if self.roles[member] == 'دکتر مافیا':
                self.lecter = member
        for member in self.alive_players:
            if member != self.detective:
                name_id = member.split(',', 1)
                await self.bot.send_message(name_id[0],"💉 دکتر مافیا بیدار شد!")
        if self.lecter:
            doci_id, doci_name = self.lecter.split(',', 1)
            lecter_keyboard = bale.MenuKeyboardMarkup()
            for member in self.mafia_team:
                name_id = member.split(',', 1)
                current_row = (self.mafia_team.index(member) + 3) // 3
                lecter_keyboard.add(bale.MenuKeyboardButton(f"حفاظت از {name_id[1]}"),row=current_row)
            await self.bot.send_message(doci_id,"💞 تا 20 ثانیه دیگر انتخاب کنید چه کسی را نجات میدهید!",components=lecter_keyboard)

    async def handle_prot(self, doctor_chat_id, save_input):
        async with self.vote_lock:
            doctor_member = self.get_member_by_chat_id(doctor_chat_id)
            if doctor_member != self.lecter:
                await self.bot.send_message(doctor_chat_id, "❌ شما دکتر نیستید!")
                return False
            if not self.lecter_phase:
                await self.bot.send_message(doctor_chat_id, "❌ الان وقت نجات نیست!")
                return False
            for i in self.mafia_team:
                save_chat_id, save_name = i.split(',', 1)
                if save_name.rstrip() == save_input[9:]:
                    if i == self.lecter:
                        if self.lecter_selfsave:
                            self.lecter_selfsave = False
                        else:
                            await self.bot.send_message(doctor_chat_id, f"⚰ قبلا یکبار خودتان را نجات دادید! شخص دیگری انتخاب کنید.")
                            return False
                    if i == self.sniper_target:
                        self.sniper_target = ""
                    await self.bot.send_message(doctor_chat_id, f"💗 {save_name} شفا یافت.")
                    self.lecter_phase = False
                    return True
            await self.bot.send_message(doctor_chat_id, "❌ لطفا از گزینه ها انتخاب کنید")
            return False
        
    async def detective_ask(self):
        self.detect_phase = True
        self.detective = ""
        for member in self.alive_players:
            if self.roles[member] == 'کارآگاه':
                self.detective = member
        for member in self.alive_players:
            if member != self.detective:
                name_id = member.split(',', 1)
                await self.bot.send_message(name_id[0],"🕵️‍♂️ کارآگاه بیدار شد!")
        if self.detective:
            detec_id, detec_name = self.detective.split(',', 1)
            detective_keyboard = bale.MenuKeyboardMarkup()
            for member in self.alive_players:
                name_id = member.split(',', 1)
                current_row = (self.alive_players.index(member) + 3) // 3
                detective_keyboard.add(bale.MenuKeyboardButton(f"استعلام {name_id[1]}"),row=current_row)
            await self.bot.send_message(detec_id,"🔎 تا 20 ثانیه دیگر انتخاب کنید استعلام چه کسی را میگیرید!",components=detective_keyboard)

    async def handle_detect(self, detect_chat_id, asked_input):
        async with self.vote_lock:
            detect_member = self.get_member_by_chat_id(detect_chat_id)
            if detect_member != self.detective:
                await self.bot.send_message(detect_chat_id, "❌ شما کارآگاه نیستید!")
                return False
            if not self.detect_phase:
                await self.bot.send_message(detect_chat_id, "❌ الان وقت استعلام نیست!")
                return False
            for i in self.alive_players:
                condi_chat_id, condi_name = i.split(',', 1)
                if condi_name.rstrip() == asked_input[8:]:
                    if i == self.godfather and self.godfather_prot:
                        await self.bot.send_message(detect_chat_id, f"🔹 {condi_name} شهروند است.")
                        self.godfather_prot = False
                    elif i in self.mafia_team:
                        await self.bot.send_message(detect_chat_id, f"‼ {condi_name} مافیا است!")
                    else:
                        await self.bot.send_message(detect_chat_id, f"🔹 {condi_name} شهروند است.")
                    self.detect_phase = False
                    return True
            await self.bot.send_message(detect_chat_id, "❌ لطفا از گزینه ها انتخاب کنید")
            return False
    
    async def day_inquire(self):
        inquire_keyboard = bale.MenuKeyboardMarkup()
        inquire_keyboard.add(bale.MenuKeyboardButton("گرفتن استعلام کشته ها"))
        self.inquire_phase = True
        for member in self.alive_players:
            chat_id = member.split(',', 1)
            await self.bot.send_message(chat_id[0], f"🧿 برای رای به گرفتن استعلام کشته ها 20 ثانیه فرصت دارید. تنها دوبار میتوان استعلام گرفت!",components=inquire_keyboard)
        await asyncio.sleep(20)
        await self.count_inquire()
    
    async def handle_inquire(self, inquire_chat_id):
        async with self.vote_lock:
            inquire_member = self.get_member_by_chat_id(inquire_chat_id)
            if not self.inquire_phase:
                await self.bot.send_message(inquire_chat_id, "❌ الان وقت استعلام نیست!")
                return False
            if not inquire_member or inquire_member in self.dead_players:
                await self.bot.send_message(inquire_chat_id, "❌ شما مرده‌اید و نمی‌توانید رای دهید!")
                return False
            if inquire_member in self.inquire_vote:
                await self.bot.send_message(inquire_chat_id, "❌ شما قبلا رای دادید!")
                return False
            self.inquire_vote.append(inquire_member)
            await self.bot.send_message(inquire_chat_id, "✅ رای شما ثبت شد.")
    
    async def count_inquire(self):
        counts_str = f"🏳 تعداد آرای موافق: {len(self.inquire_vote)}/{len(self.alive_players)}\n\n🖐 افراد موافق: "
        for i in self.inquire_vote:
            inq_targ = i.split(',', 1)
            counts_str += f"{inq_targ[1]}، "
        await self.broadcast_message(counts_str[:-2])
        if len(self.inquire_vote) >= ((len(self.alive_players) + 1) // 2):
            self.left_inquire -= 1
            left_str = "🔮 نقش‌های بیرون بازی: "
            self.inquired_roles.clear()
            for i in self.dead_players:
                left_str += f"{self.roles[i]}، "
                self.inquired_roles.append(self.roles[i])
            await self.broadcast_message(left_str)
        self.inquire_phase = False
        self.inquire_vote.clear()
        
    async def night_events(self):
        kills = "☀️ صبح شد!\n\n🖤 کشته های شب:\n"
        if self.night_target:
            temp = self.night_target.split(',',1)
            kills += f"♦ {temp[1]}\n"
            await self.execution(self.night_target,night_mode=True)
            self.night_target = ""
        if self.sniper_target and (self.sniper_target in self.alive_players):
            temp = self.sniper_target.split(',',1)
            kills += f"♦ {temp[1]}\n"
            await self.execution(self.sniper_target,night_mode=True)
            self.sniper_target = ""
        await self.broadcast_message(kills)

    async def chaos_mode(self):
        self.chaos_phase = True
        for member in self.dead_players:
            member_chat_id = member.split(',',1)
            await self.bot.send_message(member_chat_id[0],"💣 آشوب شروع شد 💣")
        await self.broadcast_message("💣 آشوب شروع شد 💣\n\n👁 120 ثانیه فرصت دارید دارید همزمان گفتگو کنید.",exclude_dead=True)
        await asyncio.sleep(120)
        await self.start_handshake()

    async def start_handshake(self):
        self.chaos_phase = False
        handshake_keyboard = bale.MenuKeyboardMarkup()
        for member in self.alive_players:
            name_id = member.split(',', 1)
            handshake_keyboard.add(bale.MenuKeyboardButton(f"دست دادن با {name_id[1]}"))
        self.handshake_phase = True
        for member in self.alive_players:
            chat_id = member.split(',', 1)
            if member in self.mafia_team:
                await self.bot.send_message(chat_id[0], "👾 منتظر نتیجه دست دادن بمانید")
            else:
                await self.bot.send_message(chat_id[0], "🤝 30 ثانیه فرصت دارید با شهروند دیگر دست دهید. بادقت انتخاب کنید!\n❗ اگر در این فرصت دست ندهید مافیا برنده میشود.",components=handshake_keyboard)
        await asyncio.sleep(20)
        for member in self.alive_players:
            chat_id = member.split(',', 1)
            if (member not in self.mafia_team) and (member not in self.chaos_win):
                await self.bot.send_message(chat_id[0], "‼ عجله کن. فقط 10 ثانیه فرصت دست دادن داری!",components=handshake_keyboard)
        await asyncio.sleep(10)
        if self.game_active:
            roles_str = "💡 نقش ها:\n"
            for member in self.roles:
                member_name = member.split(',',1)
                roles_str += f"🔹 {member_name[1]}: {self.roles[member]}\n"
            if len(self.chaos_win) < 2:
                await self.broadcast_message(f"💔 همه شهروندان دست ندادند!\n\n😈 بازی تمام شد! مافیا برنده شد!\n\n{roles_str}")
            else:
                await self.broadcast_message(f"🔥 شهروندان با هم دست دادند!\n\n🎉 بازی تمام شد! شهروندان برنده شدند!\n\n{roles_str}")
            self.game_active = False
    
    async def handle_handshake(self, voter_chat_id, vote_input):
        async with self.vote_lock:
            shaker_member = self.get_member_by_chat_id(voter_chat_id)
            if not self.handshake_phase or shaker_member in self.mafia_team:
                await self.bot.send_message(voter_chat_id, "❌ الان مرحله دست دادن نیست!")
                return False
            if not shaker_member or shaker_member in self.dead_players:
                await self.bot.send_message(voter_chat_id, "❌ شما مرده‌اید و نمی‌توانید دست دهید!")
                return False
            if shaker_member in self.chaos_win:
                await self.bot.send_message(voter_chat_id, "❌ شما قبلا دست دادید!")
                return False
            for i in self.alive_players:
                target_chat_id, target_name = i.split(',', 1)
                if target_name.rstrip() == vote_input[12:]:
                    shaker_id, shaker_name = shaker_member.split(',',1)
                    if shaker_member == i:
                        await self.bot.send_message(voter_chat_id, "❌ نمیتوانید با خودتان دست دهید!")
                        return False
                    if i in self.mafia_team:
                        roles_str = "💡 نقش ها:\n"
                        for member in self.roles:
                            member_name = member.split(',',1)
                            roles_str += f"🔹 {member_name[1]}: {self.roles[member]}\n"
                        await self.broadcast_message(f"💔 {shaker_name} با مافیا دست داد!\n\n😈 بازی تمام شد! مافیا برنده شد!\n\n{roles_str}")
                        self.game_active = False
                    else:
                        self.chaos_win.append(shaker_member)
                        await self.bot.send_message(shaker_id,f"🎯 ثبت شد.")
                    return True
            await self.bot.send_message(voter_chat_id, "❌ نامعتبر! لطفا از گزینه ها انتخاب کنید")
            return False
      
    async def check_game_end(self):
        roles_str = "💡 نقش ها:\n"
        if self.maf_count == 0 or self.maf_count >= self.cit_count:
            for member in self.roles:
                member_name = member.split(',',1)
                roles_str += f"🔹 {member_name[1]}: {self.roles[member]}\n"
        if self.maf_count == 0:
            await self.broadcast_message(f"🎉 بازی تمام شد! شهروندان برنده شدند!\n\n{roles_str}")
            return True
        elif self.maf_count >= self.cit_count:
            await self.broadcast_message(f"😈 بازی تمام شد! مافیا برنده شد!\n\n{roles_str}")
            return True
        return False
    
    async def run_game(self):
        await self.assign_roles()
        while self.game_active:
            if self.game_active and len(self.alive_players) < 4:
                await self.chaos_mode()
                break
            for member in self.alive_players:
                if not self.game_active:
                    break
                await self.start_talking_turn(member)
                await asyncio.sleep(47)
                if not self.game_active:
                    break
            if self.game_active and not self.first_day:
                await self.start_voting()
            if await self.check_game_end():
                self.game_active = False
                break
            if self.game_active:
                await self.night_phase()
            if await self.check_game_end():
                self.game_active = False
                break