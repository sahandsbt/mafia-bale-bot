#======================(INIT)======================
from bale import Bot, MenuKeyboardButton, MenuKeyboardMarkup, Message
import bale
import asyncio
bot = Bot(token = "1629802317:wLbZulANWNKGbL2BIIe-28e5mRUGy-6WAKI")

#======================(KEYBOARDS)======================
start_keyboard = MenuKeyboardMarkup()
start_keyboard.add(MenuKeyboardButton("شروع بازی"),row=1)

#======================(FUNCTIONS)======================
async def room(members,message):
    await message.reply(text="سلام "+message.from_user.first_name)
    await asyncio.sleep(10)
    await message.reply(text="بای "+message.from_user.first_name)

#======================(LISTENER)======================
@bot.listen("on_message")
async def when_message(message: Message):
    members = {}
    if "/start" in  message.text:
        if message.text == "/start":
            await message.reply(text="سلام خوش اومدی به بات بازی مافیا🥹\nبرای شروع بازی🎮 کلمه /start رو بفرست😎",components=start_keyboard)
        else:
            invite_code_list = message.text.split()
            invite_code = invite_code_list[1]
            if message.from_user.id != invite_code:
                try:
                    room_file = open(f"{invite_code}.txt",'r')
                except:
                    room_file = open(f"{invite_code}.txt",'w')
                    room_file.close()
                    room_file = open(f"{invite_code}.txt",'r')
                ids = room_file.readlines()
                if message.from_user.id not in ids:
                    room_file_ = open(f"{invite_code}.txt",'a')
                    room_file_.write(f"{message.from_user.id}\n")
                    room_file_.close()
                    room_file_ = open(f"{invite_code}.txt",'r')
                    temp = room_file_.readlines()
                    meschat_id = temp[0].split(',')
                    memberlist=""
                    for i in range(1,len(temp)):
                        memberlist+=f"\n🔅{temp[i]}"
                    print(meschat_id[0],meschat_id[1])
                    await bot.edit_message(meschat_id[0],meschat_id[1],"افراد اضافه شده:"+memberlist)
                    room_file_.close()
                room_file.close()
    elif message.text == "شروع بازی":
        await message.reply(text=f"اینو برا دوستات بفرست:\nhttps://ble.ir/sasabot?start={message.from_user.id}")
        room_file_ = open(f"{message.from_user.id}.txt",'w')
        room_file_.write(f"{message.chat_id},{int(message.message_id)+1}\n")
        room_file_.close()
        await bot.edit_message(message.chat_id,int(message.message_id)+1,"افراد اضافه شده:")
        # await room([],message)
    elif message.text == "kir":
        print(members)
    else:
        await message.reply(text="سلام بر تو پونی کوشولوی عزیز! دکتر ثابت نابغه است ❤")

bot.run()