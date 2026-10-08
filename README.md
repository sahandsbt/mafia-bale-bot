# 🕵️‍♂️ Mafia Game Bot for Bale Messenger

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Bale%20Messenger-green.svg)](https://ble.ir/)
[![License](https://img.shields.io/badge/license-MIT-red.svg)](LICENSE)

An asynchronous, feature-rich **Mafia Game Bot** built specifically for the **Bale Messenger** platform using Python. This bot brings the thrill, strategy, and deception of the classic Mafia party game straight into group chats and private lobbies!

> 🇮🇷 **Note on Language:** While the developer documentation and README are written in English, **the bot's interface, player messages, and in-game storytelling are completely in Persian (Farsi)** to provide a seamless experience for Persian-speaking communities.

---

## ✨ Features

- 🎭 **Classic & Dynamic Roles:**
  - **Mafia Side:** Godfather (پدرخوانده), Mafia Doctor / Dr. Lecter (دکتر لکتر), Simple Mafia (مافیای ساده).
  - **Citizen Side:** Doctor (دکتر), Detective (کارآگاه), Sniper (تک‌ تیرانداز), Simple Citizen (شهروند ساده).
- 🎲 **Flexible Lobby Management:**
  - **Public Queue:** Matchmake with players across the platform.
  - **Private Parties:** Create custom game lobbies via invite links to play with friends.
- 🗣️ **Turn-Based Speech & Challenge System:**
  - Time-limited turns for players to present their facts and arguments.
  - Interactive **Challenge Request** system (`🤏 چالش`) allowing players to request speaking time from the current talker.
- 💬 **In-Game Reactions:**
  - Real-time like (`👍`) and dislike (`👎`) reaction system during speeches.
- 🗳️ **Democratic Voting & Defense Phase:**
  - Dynamic voting UI to put suspects on trial and candidate defense turns before execution.
- 🌙 **Interactive Night Phase:**
  - Dedicated private mafia chat phase for strategic coordination.
  - Asynchronous night actions for Doctors, Detectives, and Snipers.
- 💣 **Chaos Mode:**
  - Triggers when only 3 players remain (2 Citizens vs 1 Mafia). Includes a 2-minute free discussion phase followed by a high-stakes **Handshake Mechanism**.
- 📊 **Inquiry & Dead Role Reveals:**
  - Limited-use day inquiries to voting on revealing deceased players' roles.
- 🛡️ **Admin Panel & Moderation:**
  - Built-in administrative tools to monitor active lobbies/rooms, manage users, and handle `/ban` or `/unban` moderation actions.

---

## 🛠️ Project Structure

```
.
├── bot/
│   ├── models/
│   │   └── gameroom.py     # Core Mafia game engine & match state logic
│   ├── utils/              # Helper utilities and permission checks
│   ├── admin.py            # Administrative panel handlers
│   ├── docs.py             # In-game rules, role guides, and Persian texts
│   └── handler.py          # Message routing, event handling, and keyboards
├── client.py               # Bot client initialization and startup
├── config.py               # Environment configuration & logger setups
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables configuration
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher.
- A **Bale Bot Token** (Obtained from [@BotFather](https://ble.ir/BotFather) on Bale Messenger).

### Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/sahandsbt/Mafia-Bale-Bot.git
   cd Mafia-Bale-Bot
   ```

2. **Create a Virtual Environment (Optional but recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup:**
   Create a `.env` file in the root directory with the following variables:
   ```env
   BOT_TOKEN=your_bale_bot_token_here
   DONATE_URL=https://your-donation-link.com
   CHANNEL_ID=your_channel_id
   OWNER_ID=your_owner_user_id
   ADMINS_ID=admin_id1,admin_id2
   SUPPORT_USERNAME=your_support_username
   CHANNEL_USERNAME=your_channel_username
   BOT_USERNAME=your_bot_username
   LOG_LEVEL=INFO
   ```

5. **Run the Bot:**
   ```bash
   python main.py
   ```

---

## 📜 In-Game Commands

| Command | Description |
| :--- | :--- |
| `/start` | Start the bot and access the main menu |
| `/party` | Open the lobby creation menu |
| `/help` | View game rules and role explanations |
| `/support` | Contact support |
| `/report` | Reply to a user's message to report them to admins |
| `/admin` | Open the admin control panel *(Admins only)* |
| `/ban @username` | Ban a user from using the bot *(Admins only)* |
| `/unban @username` | Unban a user *(Admins only)* |

---

## 📄 License & Terms of Use

This project is open-source and released under the **MIT License**.

> ⚠️ **Notice & Compliance:**  
> All intellectual rights for this codebase belong to the original developers. Spamming, DDoS attacks, or abusing the bot API is strictly prohibited and will result in permanent ban procedures. Please ensure proper attribution when using or modifying this project.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/sahandsbt/Mafia-Bale-Bot/issues) if you want to contribute.

---

⭐ **If you like this project, don't forget to give it a star on GitHub!**