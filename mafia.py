#======================(INIT)======================
import bale
import asyncio
import random
import os
bot = bale.Bot(token = "1629802317:wLbZulANWNKGbL2BIIe-28e5mRUGy-6WAKI")

#======================(KEYBOARDS)======================
start_keyboard = bale.MenuKeyboardMarkup()
start_keyboard.add(bale.MenuKeyboardButton("🎡 ساخت گروه 🎡"),row=1)
start_keyboard.add(bale.MenuKeyboardButton("❓ راهنما"),row=2)
start_keyboard.add(bale.MenuKeyboardButton("☎ پشتیبانی"),row=2)

leader_keyboard = bale.MenuKeyboardMarkup()
leader_keyboard.add(bale.MenuKeyboardButton("🎮 شروع بازی 🎮"),row=1)

invited_keyboard = bale.MenuKeyboardMarkup()
invited_keyboard.add(bale.MenuKeyboardButton("🚪 خروج 🚪"),row=1)

#======================(FUNCTIONS)======================
async def room(members_list):
    members = members_list.copy()
    roles={}
    det_ind = random.randint(0,len(members)-1)
    roles[members[det_ind]] = 'کارآگاه'
    members.pop(det_ind)
    doc_ind = random.randint(0,len(members)-1)
    roles[members[doc_ind]] = 'دکتر'
    members.pop(doc_ind)
    sni_ind = random.randint(0,len(members)-1)
    roles[members[sni_ind]] = 'اسنایپر'
    members.pop(sni_ind)
    god_ind = random.randint(0,len(members)-1)
    roles[members[god_ind]] = 'پدرخوانده'
    members.pop(god_ind)
    mdo_ind = random.randint(0,len(members)-1)
    roles[members[mdo_ind]] = 'دکتر مافیا'
    members.pop(mdo_ind)
    maf_count = (len(members) // 3) + 2
    for i in range(len(members) // 3):
        maf_ind = random.randint(0,len(members)-1)
        roles[members[maf_ind]] = 'مافیای ساده'
        members.pop(maf_ind)
    cit_count = len(members) + 3
    for i in range(len(members)):
        roles[members[i]] = 'شهروند ساده'
    for i in members_list:
        id = i.split(sep=',',maxsplit=1)
        await bot.send_message(id[0],f"بازی شروع شد! نقش شما {roles[i]} است.")
    while True:
        if maf_count == 0:
            for i in members_list:
                id = i.split(sep=',',maxsplit=1)
                await bot.send_message(id[0],f"بازی تمام شد! شهروندان برنده شدند.")
        elif cit_count <= maf_count:
            for i in members_list:
                id = i.split(sep=',',maxsplit=1)
                await bot.send_message(id[0],f"بازی تمام شد! مافیا برنده شد.")
        for i in members_list:
            talker = i.split(sep=',',maxsplit=1)
            for j in members_list:
                id = j.split(sep=',',maxsplit=1)
                if id[0] != talker[0]:
                    await bot.send_message(id[0],f"نوبت حرف زدن {talker[1]} است.")
            await bot.send_message(talker[0],f"نوبت حرف زدن شماست. تا سی ثانیه تمام پیام های شما برای بقیه ارسال میشود.")

#======================(LISTENER)======================
@bot.listen("on_message")
async def when_message(message: bale.Message):
    if "/start" in  message.text:
        if message.text == "/start":
            await message.reply(text="سلام خوش اومدی به بات بازی مافیا🥹\nبرای شروع بازی🎮 کلمه /start رو بفرست😎",components=start_keyboard)
        else:
            invite_code_list = message.text.split()
            invite_code = invite_code_list[1]
            if message.from_user.id != invite_code:
                room_file = open(f"{invite_code}.txt",'r')
                ids = room_file.readlines()
                new_line = f"{message.from_user.chat_id},{message.from_user.first_name}\n"
                if new_line not in ids:
                    with open(f"{invite_code}.txt",'a') as f:
                        f.write(f"{message.from_user.chat_id},{message.from_user.first_name}\n")
                    meschat_id = ids[0].split(',')
                    memberlist=""
                    for i in range(1,len(ids)):
                        temp2 = ids[i].split(sep=',',maxsplit=1)
                        memberlist+=f"🔅{temp2[1]}"
                    await bot.edit_message(meschat_id[0],meschat_id[1][:-1],"افراد اضافه شده:"+memberlist)
                    await message.reply(text="به بازی اضافه شدی. وایستا تا بازی شروع شه.",components=invited_keyboard)
                room_file.close()

    elif message.text == "🎡 ساخت گروه 🎡":
        await message.reply(text=f"اینو برا دوستات بفرست:\nhttps://ble.ir/sasabot?start={message.from_user.id}",components=leader_keyboard)
        with open(f"{message.from_user.id}.txt",'w') as f:
            f.write(f"{message.chat_id},{int(message.message_id)+1}\n")

    elif message.text == "🎮 شروع بازی 🎮":
        members = [f"{message.from_user.chat_id},{message.from_user.first_name}"]
        with open(f"{message.from_user.id}.txt",'r') as f:
            memberlist = f.readlines()
        os.remove(f"{message.from_user.id}.txt")
        for i in range(1,len(memberlist)):
            members.append(memberlist[i][:-1])
        if len(members) > 4:
            await room(members)
        else:
            await message.reply(text="حداقل تعداد برای شروع 5 نفر است!")

    elif message.text == "🚪 خروج 🚪":
        await message.reply(text="Nemishe")

    else:
        await message.reply(text="نمد چی میگی!")

bot.run()