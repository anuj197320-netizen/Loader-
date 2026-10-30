We#!/usr/bin/env python3
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# ═══════════════════════════════════════════════
#   -𝗖ᴏʙʀᴀ 𝗫ᴅ ❄️

# 𝙏𝙚𝙡𝙚𝙜𝙧𝙖𝙢 𝙂𝙧𝙤𝙪𝙥 𝙈𝙖𝙣𝙖𝙜𝙚𝙧 𝙏𝙤𝙤𝙡
# ═══════════════════════════════════════════════
"""

import asyncio
import os
import json
import random
import time
import logging
import re
import sys
import io
from typing import Set, Dict, Optional, List, Any
from datetime import datetime, timedelta, timezone

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, PrefixHandler
from telegram.error import RetryAfter, TimedOut, NetworkError, BadRequest, Forbidden

# Keep credentials in environment variables, never inside the source file.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

BOT_TOKENS = [8710359524:AAH8NF8C3713oN7_l76sCWM8j23Rt6R9Dz4] if BOT_TOKEN else []

OWNER_ID = int(os.getenv("OWNER_ID", "8612705143"))
GLOBAL_DELAY = 0.0
CURRENT_PREFIX = "!"
ALLOWED_PREFIXES = ["!", "."]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

start_time = time.time()
nc_tasks: Dict[int, List[asyncio.Task]] = {}
spam_tasks: Dict[int, List[asyncio.Task]] = {}
slide_tasks: Dict[int, List[asyncio.Task]] = {}
photo_tasks: Dict[int, List[asyncio.Task]] = {}
fwdspam_tasks: Dict[int, List[asyncio.Task]] = {}
chat_photos: Dict[int, List[str]] = {}
nc_counters: Dict[int, int] = {}
spam_counters: Dict[int, int] = {}
fwdspam_counters: Dict[int, int] = {}
react_emojis: Dict[int, str] = {}
GLOBAL_REACT_EMOJI: Optional[str] = None
LOCKED_CHATS: Set[int] = set()
BOT_IDS: Set[int] = set()

SUDO_USERS: Set[int] = set()
ACTIVE_TASKS: Dict[int, str] = {}
AUTHORIZATION_MSG = "𝐒ᴀ𝐘 𝗖ᴏʙʀᴀ 𝐁ᴀᴀ𝐏 𝐌ᴜ𝐉ᴇ 𝐒ᴜ𝐃ᴏ 𝐃ᴇ𝐃ᴏ 𝐌ᴇ 𝐀ᴘ𝐊ᴀ ɢ𝐔ʟ𝐀ᴍ 𝐇ᴜ🖕🏿😂"  
ALL_BOTS = []
ALL_APPS = []
REPLY_BOT = None

SUDO_FILE = "sudo_users.json"
ACCESS_FILE = "access_settings.json"
ACCESS_MODE = "public"  # private = approved groups only; public = any group
APPROVED_GROUPS: Set[int] = set()


def load_access_settings():
    global ACCESS_MODE, APPROVED_GROUPS
    try:
        with open(ACCESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        ACCESS_MODE = data.get("mode", "public")
        if ACCESS_MODE not in {"public", "private"}:
            ACCESS_MODE = "private"
        APPROVED_GROUPS = {int(x) for x in data.get("approved_groups", [])}
    except FileNotFoundError:
        pass
    except Exception as exc:
        logger.warning("Could not load access settings: %s", exc)


def save_access_settings():
    with open(ACCESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"mode": ACCESS_MODE, "approved_groups": sorted(APPROVED_GROUPS)}, f, indent=2)


def is_group_chat(chat) -> bool:
    return bool(chat and chat.type in {"group", "supergroup"})


def chat_is_allowed(update: Update) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return False
    if user.id == OWNER_ID:
        return True
    if not is_group_chat(chat):
        return True  # Existing command decorators still protect privileged DM commands.
    return ACCESS_MODE == "public" or chat.id in APPROVED_GROUPS


load_access_settings()

def load_sudo():
    global SUDO_USERS
    try:
        if os.path.exists(SUDO_FILE):
            with open(SUDO_FILE, "r") as f:
                data = json.load(f)
                SUDO_USERS = set(data.get("users", []))
    except:
        SUDO_USERS = set()

def save_sudo():
    try:
        with open(SUDO_FILE, "w") as f:
            json.dump({"users": list(SUDO_USERS)}, f)
    except:
        pass

load_sudo()

def only_sudo(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.effective_message:
            return
        if REPLY_BOT and context.bot.id != REPLY_BOT.id:
            return
        uid = update.effective_user.id
        if not chat_is_allowed(update):
            try:
                await update.effective_message.reply_text(
                    "🔒 This group is not approved. Ask the bot owner to run !approve here."
                )
            except Exception:
                pass
            return
        if uid != OWNER_ID and uid not in SUDO_USERS:
            try:
                await update.effective_message.reply_text(AUTHORIZATION_MSG)
            except:
                pass
            return
        return await func(update, context)
    return wrapper

def only_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not update.effective_message:
            return
        if REPLY_BOT and context.bot.id != REPLY_BOT.id:
            return
        uid = update.effective_user.id
        if uid != OWNER_ID:
            try:
                await update.effective_message.reply_text("🚫 ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ!")
            except:
                pass
            return
        return await func(update, context)
    return wrapper

@only_owner
async def setprefix_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_PREFIX, ALLOWED_PREFIXES
    if not context.args:
        await update.message.reply_text(f"ᴄᴜʀʀᴇɴᴛ ᴘʀᴇꜰɪxᴇꜱ: `{', '.join(ALLOWED_PREFIXES)}`\nᴜꜱᴀɢᴇ: !setprefix <new_prefix>", parse_mode="Markdown")
        return
    new_prefix = context.args[0].strip()
    if len(new_prefix) > 3:
        await update.message.reply_text("❌ ᴘʀᴇꜰɪx ᴛᴏᴏ ʟᴏɴɢ! ᴍᴀx 3 ᴄʜᴀʀᴀᴄᴛᴇʀꜱ.")
        return
    CURRENT_PREFIX = new_prefix
    if new_prefix not in ALLOWED_PREFIXES:
        ALLOWED_PREFIXES.append(new_prefix)
    await update.message.reply_text(f"✅ ᴘʀᴇꜰɪx ᴄʜᴀɴɢᴇᴅ ᴛᴏ: `{CURRENT_PREFIX}`", parse_mode="Markdown")

# ═══════════════════════════════════════════════ GROUP LOCK (!lock / !unlock) ═══════════════════════════════════════════════
@only_sudo
async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    LOCKED_CHATS.add(chat_id)
    ACTIVE_TASKS[chat_id] = "lock"
    await update.message.reply_text(
        "🔒 ɢʀᴏᴜᴘ ʟᴏᴄᴋᴇᴅ!\n"
        "ᴀʟʟ ᴍᴇꜱꜱᴀɢᴇꜱ ꜱᴇɴᴛ ᴀꜰᴛᴇʀ ᴛʜɪꜱ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ.\n"
        "👑 ᴏɴʟʏ ᴏᴡɴᴇʀ ᴀɴᴅ ꜱᴜᴅᴏ ᴜꜱᴇʀꜱ ᴄᴀɴ ꜱᴇɴᴅ ᴍᴇꜱꜱᴀɢᴇꜱ."
    )

@only_sudo
async def unlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    LOCKED_CHATS.discard(chat_id)
    if ACTIVE_TASKS.get(chat_id) == "lock":
        del ACTIVE_TASKS[chat_id]
    await update.message.reply_text(
        "🔓 ɢʀᴏᴜᴘ ᴜɴʟᴏᴄᴋᴇᴅ!\n"
        "✅ ᴇᴠᴇʀʏᴏɴᴇ ᴄᴀɴ ꜱᴇɴᴅ ᴍᴇꜱꜱᴀɢᴇꜱ ɴᴏᴡ."
    )

async def _delete_msg_fast(chat_id: int, msg_id: int):
    for bot in ALL_BOTS:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            break
        except Exception:
            continue

# ═══════════════════════════════════════════════ REACT FEATURE (!react / !dreact) ═══════════════════════════════════════════════
@only_sudo
async def react_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_REACT_EMOJI
    chat_id = update.effective_chat.id
    if not context.args:
        return await update.message.reply_text("⚠️ ᴜꜱᴇ: !ʀᴇᴀᴄᴛ <ᴇᴍᴏᴊɪ> (ᴇx: `!react 🤣` ᴏʀ `.react 🤣`)")
    
    emoji = context.args[0].strip()
    react_emojis[chat_id] = emoji
    GLOBAL_REACT_EMOJI = emoji
    ACTIVE_TASKS[chat_id] = f"react ({emoji})"
    await update.message.reply_text(
        f"✅ ᴀᴜᴛᴏ-ʀᴇᴀᴄᴛ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ᴡɪᴛʜ {emoji}!\n"
        f"👑 ʀᴇᴀᴄᴛɪɴɢ ᴛᴏ ᴏᴡɴᴇʀ & ᴀʟʟ ɢᴜʟᴀᴍꜱ ᴡɪᴛʜ {len(ALL_BOTS)} ʙᴏᴛꜱ!"
    )

@only_sudo
async def dreact_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_REACT_EMOJI
    chat_id = update.effective_chat.id
    react_emojis.pop(chat_id, None)
    GLOBAL_REACT_EMOJI = None
    if ACTIVE_TASKS.get(chat_id, "").startswith("react"):
        del ACTIVE_TASKS[chat_id]
    await update.message.reply_text("🛑 ᴀᴜᴛᴏ-ʀᴇᴀᴄᴛ ꜱᴛᴏᴘᴘᴇᴅ!")

async def _send_bot_reaction(bot, chat_id: int, message_id: int, emoji: str):
    try:
        await bot.set_message_reaction(
            chat_id=chat_id,
            message_id=message_id,
            reaction=[emoji],
            is_big=True
        )
    except Exception:
        pass

async def master_message_watcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles Group Lock deletion for non-sudo users & Auto-Reactions for Owner + Gulams."""
    if not update.effective_message or not update.effective_user or not update.effective_chat:
        return
    if REPLY_BOT and context.bot.id != REPLY_BOT.id:
        return

    chat_id = update.effective_chat.id
    uid = update.effective_user.id
    msg_id = update.effective_message.message_id

    # Ignore our own bots' messages
    if uid in BOT_IDS:
        return

    is_privileged = (uid == OWNER_ID or uid in SUDO_USERS)

    # 1. Group Lock Check: Delete message if chat is locked and user is not Owner/Sudo
    if chat_id in LOCKED_CHATS and not is_privileged:
        asyncio.create_task(_delete_msg_fast(chat_id, msg_id))
        return

    # 2. Auto-React Check: React if user is Owner or Gulam (Sudo)
    emoji = react_emojis.get(chat_id) or GLOBAL_REACT_EMOJI
    if emoji and is_privileged:
        for bot in ALL_BOTS:
            asyncio.create_task(_send_bot_reaction(bot, chat_id, msg_id, emoji))

# ═══════════════════════════════════════════════ GAME OVER COMMAND ═══════════════════════════════════════════════
@only_owner
async def gameover_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ist = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist)
    current_time = now_ist.strftime("%I:%M:%S %p")
    current_date = now_ist.strftime("%d %B %Y")

    user = update.effective_user
    message = update.effective_message
    name = (
        f"@{user.username}"
        if user and user.username
        else (user.first_name if user else "UNKNOWN USER")
    )
    chat = update.effective_chat
    group_name = chat.title if chat and chat.title else "𝙐𝙉𝙆𝙉𝙊𝙒𝙉 𝙂𝙍𝙊𝙐𝙋"
    text = (
        f"═════════════════════════\n"
        f"Ꮐᴀᴍᴇ ꪮᴠᴇʀ Ͳɪᴍᴇ - {current_time}\n"
        f"Ꭰᴀᴛᴇ - {current_date} (IST)\n\n"
        f"Ꭺʙʙ Ᏼᴀᴀᴘ Ꮶᴇ Ꭺɢɢᴇ\n"
        f"Ꮋᴀᴡᴀʙᴀᴢᴢɪ Ꮶᴀʀɴᴇ Ꮇᴛᴛ Ꭺɴᴀᴀ\n\n"
        f"Ꮐʀᴏᴜᴘ - {group_name}\n\n"
            f"TERI MAA CHUD KE DFN BY - COBRA XD 🌸\n"
        f"═════════════════════════"
    )

    if message:
        await message.reply_video(
            video="https://files.catbox.moe/2pltx5.mp4",
            caption=text,
        )

# ═══════════════════════════════════════════════ NC TARGET TEXT STYLE ═══════════════════════════════════════════════
TARGET_SOURCE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
TARGET_STYLE = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
TARGET_TRANSLATION = str.maketrans(TARGET_SOURCE, TARGET_STYLE)

def transform_nc_target(text: str) -> str:
    return text.translate(TARGET_TRANSLATION)

boltnc_EMOJIS = ["🫠","🫨","🫥","🫡","🤌","🫰","🫶","🫵","🫦","🧏","🦾","🦿","🧠","🫀","🫁","🦷","🪬","🧿","🔮","🪄","⚜️","🔱","⚔️","🗡️","🛡️","🪓","⛓️","🔗","🪝","🪤","🧨","🪫","🧬","🪩","🪞","🪭","🪷","🪻","🪸","🪼","🪲","🪳","🦠","🦂","🕷️","🕸️","🦇","🐉","🐲","🦖","🦕","🦈","🐺","🦅","🦉","🪶","🦚","🦜","🦋","🐈‍⬛","🐦‍⬛","🦄","👹","👺","👻","💀","☠️","🤖","👾","👽","👿","😈","🎭","🃏","🎴","🀄","♠️","♣️","♦️","♥️","♟️","♜","♞","♛","♚","♝","⚛️","☯️","☢️","☣️","⚕️","⚜️","〽️","✳️","✴️","❇️","🔯","♾️","💠","🔰","🔱","〰️","➰","➿","🌀","🌌","🌠","🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘","🌚","🌝","🌛","🌜","🌙","🪐","☄️","🌋","🌪️","🌫️","🌬️","⚡","🔥","💥","💫","✨","🌟","⭐","☀️","🌈","🌊","🧊","❄️","☃️","⛄","💧","🫧","🪷","🖤","🤍","🩶","💜","💙","🩵","💚","💛","🧡","❤️‍🔥","❤️‍🩹","💔","❣️","💕","💞","💓","💗","💖","💘","💝","💟","🩸","💎","🪙","💰","💸","🪙","🧧","🎯","🎲","🪬","🧩","🪄","🪅","🪆","🪇","🪈","🪉","🪏","🪚","🪛","🪜","🛠️","⚙️","🗝️","🔐","🔒","🔓","🔑","📡","🛰️","🚀","🛸","🌐","💻","🖥️","⌨️","🖱️","🖲️","📟","📠","🧮","🧪","🧫","🧯","🧰","🪝","🪬","🪦","⚰️","🪦","🕯️","🪔","🔔","🔕","📿","🧿","🪬","🌀","♨️","㊙️","㊗️","🔆","🔅","〽️","⚡","☄️","🪄","🪬","🪷","🦚","🪼","🫧","🪸","🪻","🪺","🪹","🪵","🪨","🪴","🌵","🍄","🪾","🌘","🌒","🌖","🌗","🌑","🌌","🌠","🌃","🌉","🌁","🏴‍☠️"]

boltnc_WORDS = [
    "ᑕᕼᑌᑭ 尺几ᗪㄚҜ乇 𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂𓍼ֶָ֢⊹ ࣪ ˖❄️𓍼ֶָ֢⊹ ࣪ ˖😂",
]

boltnc_PATTERN = "𓏲 ๋࣭ ࣪˖{emoji}𓂃 ࣪˖ {target} {word} 𓏲 ๋࣭ ࣪˖{emoji}𓂃 ࣪˖"

# ═══════════════════════════════════════════════ NC2 - HEART EMOJIS WITH ABUSE WORDS ═══════════════════════════════════════════════
nc_EMOJIS = ["🥱","😱","🤨","😒","😡","🤬","😤","😮‍💨","🥵","🥶","🤢","🤮","🫩","😈","👿","👽","🧃","🧋","🗻","🃏","💠","🇦🇨","🇦🇩","🇦🇪","🇦🇫","🇦🇬","🇦🇮","🇦🇱","🇦🇲","🇦🇴","🇦🇶","🇦🇷","🇦🇸","🇦🇹","🇦🇺","🇦🇼","🇧🇦","🇧🇶","🇧🇱","🇧🇫","🇨🇮","🇨🇩","🇨🇦","🇨🇿","🇩🇯","🇨🇭","🇪🇬","🇨🇨","🇧🇯","🇧🇶","🇰🇿","🇰🇼","🇰🇳","🇲🇭","🇲🇪","🇲🇬","🇰🇳","🇮🇴","🇯🇵","🇷🇺","🇳🇺","🇵🇬","🇸??","🇵🇷","🇵🇳","🇵🇭","🇳🇫","🇳🇪","🇺🇾","🇺🇸","🇻🇪","🌊","🌬️","❄️","🌀","🌪️","⚡","☔","🌈","💧","☁️","🌨️","🌧️","🌩️","⛈️","🌦️","🌥️","⛅","🌤️","☀️","🌞","🌝","🌚","🌜","🌛","🌙","⭐","🌟","✨","🪐","🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"]

nc_WORDS = [
    "𝗧ᴍᴋʙ",
    "𝗧ᴍᴋᴄ",
    "𝗥ᴀɴᴅ",
    "𝗕ᴋʟ",
    "𝗧ᴍʀ",
    "𝗟ᴜɴ𝗞ʜᴀ",
    "𝗠ᴀᴅᴇʀᴄʜᴏᴅ",
    "𝗕ꜱᴅᴋ",
    "𝗚ᴀɴᴅᴜ",
    "𝗧ᴍᴋᴄ𝗠ᴀᴄᴄʜᴀʀ",
    "𝗣ʟᴀʏ𝗚ɪʀʟ",
    "𝗔ꜱꜱ𝗛ᴏʟᴇ",
    "𝗡ɪɢɢᴀ",
    "𝗙ᴜᴄᴋ𝗬ᴏᴜ",
    "𝗣ᴇʀᴠᴇʀᴛ",
    "𝗦ᴛᴇᴘꜱɪꜱ",
    "𝗠ᴏᴛʜᴇʀ𝗙ᴜᴄᴋᴇʀ",
    "𝗕ᴏʙʙɪᴇ",
    "𝗕ᴀꜱᴛᴀʀᴅ",
    "𝗣ɪᴇᴄᴇ𝗢ꜰ𝗦ʜɪᴛ",
]

nc_PATTERN = "≼ {emoji} ≽ {target} 𓂃{word}𓂃𓈒𓏸≼ {emoji} ≽"

# ═══════════════════════════════════════════════ NC3 - WEATHER & SPACE EMOJIS WITH ABUSE ═══════════════════════════════════════════════
pookienc_EMOJIS = ["🫠","🫨","🫥","🫡","🤌","🫰","🫶","🫵","🫦","🧏","🦾","🦿","🧠","🫀","🫁","🦷","🪬","🧿","🔮","🪄","⚜️","🔱","⚔️","🗡️","🛡️","🪓","⛓️","🔗","🪝","🪤","🧨","🪫","🧬","🪩","🪞","🪭","🪷","🪻","🪸","🪼","🪲","🪳","🦠","🦂","🕷️","🕸️","🦇","🐉","🐲","🦖","🦕","🦈","🐺","🦅","🦉","🪶","🦚","🦜","🦋","🐈‍⬛","🐦‍⬛","🦄","👹","👺","👻","💀","☠️","🤖","👾","👽","👿","😈","🎭","🃏","🎴","🀄","♠️","♣️","♦️","♥️","♟️","♜","♞","♛","♚","♝","⚛️","☯️","☢️","☣️","⚕️","⚜️","〽️","✳️","✴️","❇️","🔯","♾️","💠","🔰","🔱","〰️","➰","➿","🌀","🌌","🌠","🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘","🌚","🌝","🌛","🌜","🌙","🪐","☄️","🌋","🌪️","🌫️","🌬️","⚡","🔥","💥","💫","✨","🌟","⭐","☀️","🌈","🌊","🧊","❄️","☃️","⛄","💧","🫧","🪷","🖤","🤍","🩶","💜","💙","🩵","💚","💛","🧡","❤️‍🔥","❤️‍🩹","💔","❣️","💕","💞","💓","💗","💖","💘","💝","💟","🩸","💎","🪙","💰","💸","🪙","🧧","🎯","🎲","🪬","🧩","🪄","🪅","🪆","🪇","🪈","🪉","🪏","🪚","🪛","🪜","🛠️","⚙️","🗝️","🔐","🔒","🔓","🔑","📡","🛰️","🚀","🛸","🌐","💻","🖥️","⌨️","🖱️","🖲️","📟","📠","🧮","🧪","🧫","🧯","🧰","🪝","🪬","🪦","⚰️","🪦","🕯️","🪔","🔔","🔕","📿","🧿","🪬","🌀","♨️","㊙️","㊗️","🔆","🔅","〽️","⚡","☄️","🪄","🪬","🪷","🦚","🪼","🫧","🪸","🪻","🪺","🪹","🪵","🪨","🪴","🌵","🍄","🪾","🌘","🌒","🌖","🌗","🌑","🌌","🌠","🌃","🌉","🌁","🏴‍☠️"]

pookienc_WORDS = [
    "RΛɴᴅʏᴋΣ𓍯🎀𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀𓍯𓍯🎀",
]

pookienc_PATTERN = "«{emoji}» {target} {word} «{emoji}»"

# ═══════════════════════════════════════════════ NC4 - FLAGS & MIXED EMOJIS WITH ABUSE ═══════════════════════════════════════════════
bignc_EMOJIS = ["🫠","🫨","🫥","🫡","🤌","🫰","🫶","🫵","🫦","🧏","🦾","🦿","🧠","🫀","🫁","🦷","🪬","🧿","🔮","🪄","⚜️","🔱","⚔️","🗡️","🛡️","🪓","⛓️","🔗","🪝","🪤","🧨","🪫","🧬","🪩","🪞","🪭","🪷","🪻","🪸","🪼","🪲","🪳","🦠","🦂","🕷️","🕸️","🦇","🐉","🐲","🦖","🦕","🦈","🐺","🦅","🦉","🪶","🦚","🦜","🦋","🐈‍⬛","🐦‍⬛","🦄","👹","👺","👻","💀","☠️","🤖","👾","👽","👿","😈","🎭","🃏","🎴","🀄","♠️","♣️","♦️","♥️","♟️","♜","♞","♛","♚","♝","⚛️","☯️","☢️","☣️","⚕️","⚜️","〽️","✳️","✴️","❇️","🔯","♾️","💠","🔰","🔱","〰️","➰","➿","🌀","🌌","🌠","🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘","🌚","🌝","🌛","🌜","🌙","🪐","☄️","🌋","🌪️","🌫️","🌬️","⚡","🔥","💥","💫","✨","🌟","⭐","☀️","🌈","🌊","🧊","❄️","☃️","⛄","💧","🫧","🪷","🖤","🤍","🩶","💜","💙","🩵","💚","💛","🧡","❤️‍🔥","❤️‍🩹","💔","❣️","💕","💞","💓","💗","💖","💘","💝","💟","🩸","💎","🪙","💰","💸","🪙","🧧","🎯","🎲","🪬","🧩","🪄","🪅","🪆","🪇","🪈","🪉","🪏","🪚","🪛","🪜","🛠️","⚙️","🗝️","🔐","🔒","🔓","🔑","📡","🛰️","🚀","🛸","🌐","💻","🖥️","⌨️","🖱️","🖲️","📟","📠","🧮","🧪","🧫","🧯","🧰","🪝","🪬","🪦","⚰️","🪦","🕯️","🪔","🔔","🔕","📿","🧿","🪬","🌀","♨️","㊙️","㊗️","🔆","🔅","〽️","⚡","☄️","🪄","🪬","🪷","🦚","🪼","🫧","🪸","🪻","🪺","🪹","🪵","🪨","🪴","🌵","🍄","🪾","🌘","🌒","🌖","🌗","🌑","🌌","🌠","🌃","🌉","🌁","🏴‍☠️"]

bignc_WORDS = [
    "ᑕᕼᑌᑭ ᗰᗩᴋEᒪᴏᗪᴇ 𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙👑𒈙",
]

bignc_PATTERN = "‹{emoji}› {target} {word} ‹{emoji}›"

# ═══════════════════════════════════════════════ NC5 - AESTHETIC EMOJIS WITH ABUSE ═══════════════════════════════════════════════
nccurly_EMOJIS = ["🫠","🫨","🫥","🫡","🤌","🫰","🫶","🫵","🫦","🧏","🦾","🦿","🧠","🫀","🫁","🦷","🪬","🧿","🔮","🪄","⚜️","🔱","⚔️","🗡️","🛡️","🪓","⛓️","🔗","🪝","🪤","🧨","🪫","🧬","🪩","🪞","🪭","🪷","🪻","🪸","🪼","🪲","🪳","🦠","🦂","🕷️","🕸️","🦇","🐉","🐲","🦖","🦕","🦈","🐺","🦅","🦉","🪶","🦚","🦜","🦋","🐈‍⬛","🐦‍⬛","🦄","👹","👺","👻","💀","☠️","🤖","👾","👽","👿","😈","🎭","🃏","🎴","🀄","♠️","♣️","♦️","♥️","♟️","♜","♞","♛","♚","♝","⚛️","☯️","☢️","☣️","⚕️","⚜️","〽️","✳️","✴️","❇️","🔯","♾️","💠","🔰","🔱","〰️","➰","➿","🌀","🌌","🌠","🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘","🌚","🌝","🌛","🌜","🌙","🪐","☄️","🌋","🌪️","🌫️","🌬️","⚡","🔥","💥","💫","✨","🌟","⭐","☀️","🌈","🌊","🧊","❄️","☃️","⛄","💧","🫧","🪷","🖤","🤍","🩶","💜","💙","🩵","💚","💛","🧡","❤️‍🔥","❤️‍🩹","💔","❣️","💕","💞","💓","💗","💖","💘","💝","💟","🩸","💎","🪙","💰","💸","🪙","🧧","🎯","🎲","🪬","🧩","🪄","🪅","🪆","🪇","🪈","🪉","🪏","🪚","🪛","🪜","🛠️","⚙️","🗝️","🔐","🔒","🔓","🔑","📡","🛰️","🚀","🛸","🌐","💻","🖥️","⌨️","🖱️","🖲️","📟","📠","🧮","🧪","🧫","🧯","🧰","🪝","🪬","🪦","⚰️","🪦","🕯️","🪔","🔔","🔕","📿","🧿","🪬","🌀","♨️","㊙️","㊗️","🔆","🔅","〽️","⚡","☄️","🪄","🪬","🪷","🦚","🪼","🫧","🪸","🪻","🪺","🪹","🪵","🪨","🪴","🌵","🍄","🪾","🌘","🌒","🌖","🌗","🌑","🌌","🌠","🌃","🌉","🌁","🏴‍☠️"]

nccurly_WORDS = [
    "𒈙⸻🩵𒈙⸻❤️𒈙⸻🩷𒈙⸻🧡𒈙⸻💛𒈙⸻💚𒈙⸻💙𒈙⸻💜𒈙⸻🖤𒈙⸻🩶𒈙⸻🤍𒈙⸻ 𒈙⸻🩵𒈙⸻❤️𒈙⸻🩷𒈙⸻🧡𒈙⸻💛𒈙⸻💚𒈙⸻💙𒈙⸻💜",
]

nccurly_PATTERN = "᚛{emoji}᚜ {target}  {word} ᚛{emoji}᚜"

# ═══════════════════════════════════════════════ NC6 - AESTHETIC EMOJIS WITH ABUSE ═══════════════════════════════════════════════
fastnc_EMOJIS = [
    "🫠","🫨","🫥","🫡","🤌","🫰","🫶","🫵",
    "🫦","🧏","🦾","🦿","🧠","🫀","🫁","🦷",
    "🪬","🧿","🔮","🪄","⚜️","🔱","⚔️","🗡️",
    "🛡️","🪓","⛓️","🔗","🪝","🪤","🧨","🪫",
    "🧬","🪩","🪞","🪭","🪷","🪻","🪸","🪼",
    "🪲","🪳","🦠","🦂","🕷️","🕸️","🦇","🐉",
    "🐲","🦖","🦕","🦈","🐺","🦅","🦉","🪶",
    "🦚","🦜","🦋","👹","👺","👻","💀","☠️",
    "🤖","👾","👽","👿","😈","🎭","🃏","🎴",
    "🌌","🌙","🪐","☄️","🌋","🌪️","⚡","🔥",
    "💥","✨","🌟","⭐","🌈","🌊","🧊","❄️",
    "💜","💙","🩵","💚","💛","🧡","🖤","🤍",
    "💎","🎯","🎲","🚀","🛸","🌐","💻","⚙️"
]

