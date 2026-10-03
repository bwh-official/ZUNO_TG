import os, re
import time
import binascii
import asyncio
import aiohttp
import pycountry
import urllib.parse
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant
from telethon import TelegramClient
from telethon.tl.functions.account import GetAuthorizationsRequest, ResetAuthorizationRequest
from telethon.sessions import MemorySession
from telethon.crypto import AuthKey
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Initialize AsyncIOScheduler
scheduler = AsyncIOScheduler()

# Configuration Variables
API_ID = int(os.environ.get("API_ID", "39408219"))
API_HASH = os.environ.get("API_HASH", "1469d15958c8748dbbb6161170014a30")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8912569186:AAHCTBwpu9oO9HYknuB7NA2txILYmmD3UsM")
LZT_API_KEY = os.environ.get("LZT_API_KEY", "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzUxMiJ9.eyJzdWIiOjEwOTU0ODkyLCJpc3MiOiJsenQiLCJpYXQiOjE3OTA5Mzc5MTYsImp0aSI6IjEwMjE0MTgiLCJzY29wZSI6ImJhc2ljIHJlYWQgcG9zdCBjb252ZXJzYXRlIHBheW1lbnQgaW52b2ljZSBjaGF0Ym94IG1hcmtldCIsImV4cCI6MTk0ODYxNzkxNn0.g-J1wonAt90ipY5rAKuaKJDoaUBIUBaX5H46JUXUNoesbjVvrH9g1243p840cq2mIkCd0R3YyqdtA02FtYCcEbGebujCuXk6lcNegYyWva8Wf1I6SnQjzRifYzz4bO4y7tgZ3cyFAsECVwj_1ww7CEqMJ-VVr9T8GDuyvv1iQOQ")

ADMIN_ID = int(os.environ.get("ADMIN_ID", "8667271525"))  # Replace with actual Admin User ID
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", "-1003555056142"))

# Payment Credentials
UPI_ID = os.environ.get("UPI_ID", "ᴢᴜɴᴏˍᴛɢ")
UPI_QR_URL = os.environ.get("UPI_QR_URL", "")
CRYPTO_ADDRESS = os.environ.get("CRYPTO_ADDRESS", "0x636e0cfb86bdd462dcf4e79e0f7b49a7acffa4b8")

# MongoDB URI
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://zunotg:zunotg@zunotg.nfrpdb4.mongodb.net/?appName=ZUNOTG")
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["lzt_shop_db"]
users_col = db["users"]
orders_col = db["orders"]
prices_collection = db["country_prices"]

SUPPORT_USERNAME = "@ZUNO_S" 
SOURCE_CODE_TEXT = "🤖 **Source Code Information**\n\n**Price is ₹3000 / $30**\n\nTo buy or get access to this bot's source code, contact support:@ZUNO_S "

# Replace with your actual Channel and Group usernames or IDs
CHANNEL_USERNAME = "ZUNO_TG_L"  # without '@'
GROUP_USERNAME = "ZUNO_TG_G"      # without '@'

GROUP_ID = int("-1004456887820")

USD_TO_INR = 100.0
PROFIT_MARGIN = 1.40

# Anti-spam tracker: {usetimestamp}
USER_COOLDOWNS = {}
COOLDOWN_SECONDS = 120

# Global cache: Stores fetched data to serve instantly
CACHE_DATA = {"timestamp": 0, "response_text": "", "lines": []}
CACHE_TTL = 600  # Refresh cache every 300 seconds

# Expanded to 200+ global ISO country codes
ALL_COUNTRIES = [
    # North America & Caribbean
    "US", "CA", "MX", "JM", "TT", "BS", "BB", "BZ", "CR", "SV", 
    "GT", "HN", "NI", "PA", "DO", "HT", "CU", "PR", "AG", "DM", 
    "GD", "KN", "LC", "VC", "AW", "CW", "KY", "BM", "GP", "MQ",

    # South America
    "BR", "AR", "CL", "CO", "PE", "VE", "EC", "BO", "PY", "UY", 
    "GY", "SR", "GF",

    # Western & Northern Europe
    "GB", "DE", "FR", "IT", "ES", "NL", "BE", "CH", "AT", "SE", 
    "NO", "FI", "DK", "IE", "PT", "LU", "IS", "IM", "JE", "GG", 
    "FO", "AX",

    # Eastern & Southern Europe
    "RU", "UA", "PL", "RO", "CZ", "HU", "GR", "BG", "BY", "SK", 
    "HR", "RS", "SI", "LT", "LV", "EE", "MD", "AL", "MK", "BA", 
    "ME", "XK", "CY", "MT", "GI", "AD", "SM", "MC", "VA",

    # Central Asia & Caucasus
    "KZ", "UZ", "AZ", "AM", "GE", "KG", "TJ", "TM",

    # Middle East
    "TR", "AE", "SA", "IL", "IR", "IQ", "JO", "LB", "KW", "QA", 
    "OM", "BH", "YE", "SY", "PS",

    # South Asia
    "IN", "PK", "BD", "LK", "NP", "AF", "MV", "BT",

    # East & Southeast Asia
    "ID", "PH", "VN", "TH", "MY", "SG", "KR", "JP", "CN", "HK", 
    "TW", "KH", "LA", "MM", "MN", "MO", "BN", "TL",

    # Oceania
    "AU", "NZ", "PG", "FJ", "SB", "VU", "NC", "PF", "GU", "WS", 
    "TO", "FM", "KI", "MH", "NR", "PW", "TV",

    # Northern & Western Africa
    "EG", "MA", "DZ", "TN", "LY", "NG", "GH", "CI", "CM", "SN", 
    "GN", "BF", "ML", "NER", "TG", "BJ", "LR", "SL", "MR", "GM", 
    "GW", "CV",

    # Eastern, Central & Southern Africa
    "KE", "ZA", "TZ", "UG", "ET", "AO", "MZ", "ZW", "ZM", "RW", 
    "CD", "CG", "GA", "SD", "SS", "SS", "TD", "CF", "BI", "MW", 
    "MG", "MU", "SC", "LS", "SZ", "BW", "NA", "KM", "DJ", "ER", 
    "SO"
]

app = Client("lzt_shop_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

PURCHASED_SESSIONS = {}
USER_STATES = {}

def get_lzt_headers():
    return {
        "Authorization": f"Bearer {LZT_API_KEY}",
       # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

def format_last_active(timestamp):
    if not timestamp:
        return "Unknown"
    now = int(time.time())
    diff = max(0, now - int(timestamp))
    days = diff // 86400
    hours = (diff % 86400) // 3600
    if days > 0:
        return f"{days} day{'s' if days > 1 else ''}, {hours} hour{'s' if hours > 1 else ''} ago"
    elif hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        return "Just now"

def save_hex_to_session_file(item_id: str, hex_str: str) -> str:
    filename = f"temp_session_{item_id}.session"
    raw_bytes = binascii.unhexlify(hex_str)
    with open(filename, "wb") as f:
        f.write(raw_bytes)
    return filename

def cleanup_session_file(item_id: str):
    filename = f"temp_session_{item_id}.session"
    if os.path.exists(filename):
        os.remove(filename)
    

def resolve_country_code(user_input: str) -> str | None:
    query = user_input.strip().lower()
    if len(query) == 2:
        country = pycountry.countries.get(alpha_2=query.upper())
        if country:
            return country.alpha_2
    try:
        matches = pycountry.countries.search_fuzzy(query)
        if matches:
            return matches[0].alpha_2
    except Exception:
        pass
    return None

async def is_subscribed(client: Client, user_id: int) -> bool:
    """Checks if a user is a member of both the channel and group."""
    try:
        # Check Channel
        channel_member = await client.get_chat_member(CHANNEL_USERNAME, user_id)
        if channel_member.status == "kicked":
            return False
            
        # Check Group
        group_member = await client.get_chat_member(GROUP_USERNAME, user_id)
        if group_member.status == "kicked":
            return False

        return True
    except UserNotParticipant:
        return False
    except Exception as e:
        # Handles cases where the bot isn't an admin in the group/channel
        print(f"Error checking force sub: {e}")
        return True  # Allows access if there's an administrative/bot-permission error 

def get_flag_emoji(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return "🌐"
    country_code = country_code.upper()
    return chr(127397 + ord(country_code[0])) + chr(127397 + ord(country_code[1]))

async def get_or_create_user(user_id: int, username: str = None):
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        user_data = {
            "user_id": user_id,
            "username": username,
            "balance": 0.0,
            "created_at": time.time()
        }
        await users_col.insert_one(user_data)
        return user_data
    return user

async def update_balance(user_id: int, amount: float):
    await users_col.update_one({"user_id": user_id}, {"$inc": {"balance": amount}}, upsert=True)


# Broadcast Command 

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID) & filters.reply)
async def broadcast_handler(client: Client, message: Message):
    target_message = message.reply_to_message
    status_msg = await message.reply_text("🔄 Starting broadcast...")

    total_users = 0
    successful = 0
    removed_users = 0
    failed = 0

    cursor = users_col.find({}, {"user_id": 1, "_id": 0})
    
    async for user in cursor:
        user_id = user.get("user_id")
        if not user_id:
            continue
            
        total_users += 1
        try:
            await target_message.copy(chat_id=user_id)
            successful += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await target_message.copy(chat_id=user_id)
            successful += 1
        except (UserIsBlocked, InputUserDeactivated):
            # Delete inactive or blocking user directly from MongoDB
            await users_col.delete_one({"user_id": user_id})
            removed_users += 1
        except Exception:
            failed += 1

        # Rate limit protection: 0.05s delay (~20 msgs/sec limit)
        await asyncio.sleep(0.05)

    report = (
        "✅ **Broadcast Completed**\n\n"
        f"👥 **Total Processed:** `{total_users}`\n"
        f"🟢 **Successfully Sent:** `{successful}`\n"
        f"🗑️ **Deleted from DB:** `{removed_users}`\n"
        f"❌ **Failed (Other):** `{failed}`"
    )
    await status_msg.edit_text(report)


# ----------------------------------------------------
# 1. /start COMMAND WITH DEPOSIT & REORDERED BUTTONS
# ----------------------------------------------------
START_TEXT = (
    "👋 **Welcome to TG Accounts Shop Bot!**\n"
    "Your one-stop market for high-quality Telegram accounts.\n\n"
    "**⚡ Quick Overview:**\n"
    "• 📱 **Telegram Accounts:** Browse & buy instant session accounts.\n"
    "• 🔥 **Cheap Price Checker:** Type /cheap to view real-time cheapest prices across 200+ countries.\n"
    "• 🔍 **Search Country:** Type /search then send country name or symbol.\n"
    "• 💳 **Deposit:** Add funds to your wallet using crypto or UPI.\n"
    "• 💰 **Balance:** Check your active wallet balance.\n"
    "• 📦 **My Orders:** View purchase history and download files.\n"
    "• 🛠️ **Support:** Get help from our admin team.\n"
    "• 💻 **Source Code:** Get access to custom bot development.\n"
    "• ⚠️ **NO REFUNDS IN ANY CASE.**\n\n"
    "**🧑‍💻 Bot Is Developed Or Maintained By @ZUNO_S**\n\n"
    "👇 **Select an option below to get started:**"
)


START_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📱 Telegram Accounts", callback_data="main_menu")],
    [
        InlineKeyboardButton("💳 Deposit", callback_data="deposit_start"),
        InlineKeyboardButton("💰 Balance", callback_data="show_balance")
    ],
    [
        InlineKeyboardButton("📦 My Orders", callback_data="my_orders_1"),
        InlineKeyboardButton("🛠️ Support", callback_data="show_support")
    ],
    [InlineKeyboardButton("💻 Source Code", callback_data="show_source_code")]
])


@app.on_message(filters.private & filters.command(["start"]))
async def start_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    await get_or_create_user(user_id, username)

    # Force Sub Check
    if not await is_subscribed(client, user_id):
        join_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}"),
                InlineKeyboardButton("💬 Join Group", url=f"https://t.me/{GROUP_USERNAME}")
            ],
            [
                InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{client.me.username}?start=start")
            ]
        ])
        
        return await message.reply_text(
            "⚠️ **Access Denied!**\n\nTo use this bot, you must join our updates channel and group first.",
            reply_markup=join_keyboard
        )
    
    await message.reply_text(START_TEXT, reply_markup=START_KEYBOARD)


@app.on_callback_query(filters.regex(r"^back_to_start$"))
async def back_to_start_callback(client: Client, callback_query: CallbackQuery):
    # Handles media messages safely when navigating back to main menu
    if callback_query.message.photo or callback_query.message.media:
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await client.send_message(
            chat_id=callback_query.message.chat.id,
            text=START_TEXT,
            reply_markup=START_KEYBOARD
        )
    else:
        await callback_query.message.edit_text(START_TEXT, reply_markup=START_KEYBOARD)



# ----------------------------------------------------
# 2. DEPOSIT & PAYMENT SYSTEM
# ----------------------------------------------------
@app.on_message(filters.private & filters.text & ~filters.command(["start", "cheap", "addbalance", "search", "otp"]))
async def handle_text_inputs(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = USER_STATES.get(user_id)

    if not isinstance(user_data, dict):
        return

    state = user_data.get("state")

    # Deposit Amount Input
    if state == "awaiting_deposit_amount":
        try:
            amount = float(message.text.strip())
            if amount <= 0:
                raise ValueError()
        except ValueError:
            await message.reply_text("❌ Please enter a valid positive number.")
            return

        USER_STATES[user_id] = {"state": "selected_payment_method", "amount": amount}

        text = (
            f"💳 **Deposit Amount:** ₹{amount:.2f}\n\n"
            f"Please select your preferred payment method below: UPI OR QR PAYMENT NOT AVAILABLE RIGHTNOW. INSTEAD OF SEND PHONEPAY GIFT CARD SCREENSHOT"
        )
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🇮🇳 UPI Payment", callback_data="pay_upi"),
                InlineKeyboardButton("🪙 Crypto (USDT)", callback_data="pay_crypto")
            ],
            [InlineKeyboardButton("⬅️ Cancel", callback_data="back_to_start")]
        ])
        await message.reply_text(text, reply_markup=keyboard)
        return

    # Country Search Input
    if state == "awaiting_country_query":
        user_input = message.text.strip()
        country_code = resolve_country_code(user_input)
        USER_STATES.pop(user_id, None)

        if not country_code:
            await message.reply_text(
                f"❌ Could not find any country matching `{user_input}`.\n"
                "Please try searching again or return to `/start`."
            )
            return

        flag = get_flag_emoji(country_code)
        text = (
            f"{flag} **Country Selected: {country_code}**\n\n"
            f"Please select the quality/type menu you want for **{country_code}**:"
        )
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📧 Cheap + Mail", callback_data=f"reg_cheap_mail_{country_code}"),
                InlineKeyboardButton("🚫 Cheap + NoMail", callback_data=f"reg_cheap_nomail_{country_code}")
            ],
            [
                InlineKeyboardButton("⭐ Good + Mail 📧", callback_data=f"reg_good_mail_{country_code}"),
                InlineKeyboardButton("⭐ Good + NoMail 🚫", callback_data=f"reg_good_nomail_{country_code}")
            ],
            [
                InlineKeyboardButton("📊 Cheapest Price Accounts", callback_data=f"reg_cheapest_{country_code}")
            ],
            [
                InlineKeyboardButton("💎 Telegram Premium Account", callback_data=f"reg_premium_{country_code}")
            ],
            [
                InlineKeyboardButton("🚫 Spammed Block Account", callback_data=f"reg_spam_{country_code}")
            ]
        ])
        await message.reply_text(text, reply_markup=keyboard)

    if state == "awaiting_old_account_country":
        query = message.text.strip().upper()
        country_code = query if len(query) == 2 else resolve_country_code(query) 
        
        USER_STATES.pop(user_id, None)

        if not country_code:
            await message.reply_text(
                f"❌ Could not find any country matching `{query}`.\n"
                "Please try searching again or return to `/start`."
            )
            return

        flag = get_flag_emoji(country_code) if country_code != "GLOBAL" else "🌐"
        text = (
            f"{flag} **Country Selected: {country_code}**\n\n"
            f"Please select the quality for **{country_code}** Old Accounts:"
        )
        # Quality buttons pass both quality and country_code in callback_data
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📧 Cheap + Mail", callback_data=f"oldqual_cheap_mail_{country_code}"),
                InlineKeyboardButton("🚫 Cheap + NoMail", callback_data=f"oldqual_cheap_nomail_{country_code}")
            ],
            [
                InlineKeyboardButton("⭐ Good + Mail 📧", callback_data=f"oldqual_good_mail_{country_code}"),
                InlineKeyboardButton("⭐ Good + NoMail 🚫", callback_data=f"oldqual_good_nomail_{country_code}")
            ],
            [
                InlineKeyboardButton("📊 Cheapest", callback_data=f"oldqual_cheapest_{country_code}")
            ],
            [InlineKeyboardButton("⬅️ Back", callback_data="random_old_accounts")]
        ])
        await message.reply_text(text, reply_markup=keyboard)



# ----------------------------------------------------
# CANCEL BUTTON & DEPOSIT HANDLERS
# ----------------------------------------------------
@app.on_callback_query(filters.regex(r"^cancel_deposit$"))
async def cancel_deposit_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Remove waiting state
    USER_STATES.pop(user_id, None)

    text = "❌ **Deposit Cancelled.**\n\nYour deposit request has been cancelled."
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^deposit_start$"))
async def deposit_start_callback(client: Client, callback_query: CallbackQuery):
    
    user_id = callback_query.from_user.id
    USER_STATES[user_id] = {"state": "awaiting_deposit_amount"}

    text = "💳 **Deposit Funds**\n\nPlease enter the amount you wish to deposit in INR (₹):"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_deposit")]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^pay_(upi|crypto)$"))
async def payment_method_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    method = callback_query.data.split("_")[1]
    user_data = USER_STATES.get(user_id, {})
    amount = user_data.get("amount", 0.0)

    if not amount:
        await callback_query.answer("⚠️ Deposit session expired. Try again.", show_alert=True)
        return

    USER_STATES[user_id] = {"state": "awaiting_screenshot", "amount": amount, "method": method}

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_deposit")]
    ])

    if method == "upi":
        # Dynamic UPI URI with user amount
        upi_uri = f"upi://pay?pa={UPI_ID}&am={amount:.2f}&cu=INR&pn=Shop"
        encoded_upi_uri = urllib.parse.quote(upi_uri, safe="")
        dynamic_qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_upi_uri}"

        text = (
            f"🇮🇳 **UPI Payment**\n\n"
            f"💰 Amount: **₹{amount:.2f}**\n"
            f"🆔 UPI ID: `{UPI_ID}`\n\n"
            f"Scan the QR code above to pay exactly **₹{amount:.2f}**.\n"
            f"📸 **Send the payment screenshot here once completed.**"
        )
        
        try: await callback_query.message.delete()
        except: pass
        await client.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=dynamic_qr_url,
            caption=text,
            reply_markup=keyboard
        )

    elif method == "crypto":
        usdt_amount = amount / 100.0
        text = (
            f"🪙 **Crypto Payment (USDT)**\n\n"
            f"💰 INR Amount: **₹{amount:.2f}**\n"
            f"💵 USDT Equivalent (1 USDT = ₹100): **{usdt_amount:.2f} USDT**\n\n"
            f"📍 Bep20 (BNB) Address: `{CRYPTO_ADDRESS}`\n\n"
            f"🧑‍💻 For Other Address Contact @KingVJ03\n\n"
            f"📸 **Send the transaction screenshot/receipt here once completed.**"
        )
        await callback_query.message.edit_text(text, reply_markup=keyboard)



@app.on_message(filters.photo & filters.private)
async def handle_payment_screenshot(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = USER_STATES.get(user_id)

    if isinstance(user_data, dict) and user_data.get("state") == "awaiting_screenshot":
        amount = user_data.get("amount")
        method = user_data.get("method", "N/A").upper()
        USER_STATES.pop(user_id, None)

        admin_caption = (
            f"📥 **New Deposit Request**\n\n"
            f"👤 User: {message.from_user.mention} (`{user_id}`)\n"
            f"💵 Amount: **₹{amount:.2f}**\n"
            f"💳 Method: {method}\n\n"
            f"Approve or reject this deposit:"
        )
        admin_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"dep_accept_{user_id}_{amount}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"dep_reject_{user_id}_{amount}")
            ]
        ])
        try: await client.send_photo(ADMIN_ID, photo=message.photo.file_id, caption=admin_caption, reply_markup=admin_keyboard)
        except:
            await message.reply_text("**Something Went Wrong Send Screenshot Again Or Try Later**")
            return 
        await message.reply_text("✅ **Payment screenshot sent!** Admin will review and credit your balance shortly.\n\n**Due to my study deposit approval may take some time, if you deposit fund after 11 PM in Night Then Your Deposit Approved In Morning Around 7 AM.**")


@app.on_callback_query(filters.regex(r"^dep_(accept|reject)_(\d+)_(.+)"))
async def admin_deposit_approval(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ Unauthorized.", show_alert=True)
        return

    action, target_user_id, amount_str = callback_query.data.split("_")[1:]
    target_user_id = int(target_user_id)
    amount = float(amount_str)

    if action == "accept":
        await update_balance(target_user_id, amount)
        await callback_query.message.edit_caption(callback_query.message.caption + "\n\n✅ **Approved & Credited.**")
        try:
            await client.send_message(
                target_user_id,
                f"🎉 **Deposit Approved!**\n\n₹{amount:.2f} has been added to your wallet balance."
            )
        except Exception:
            pass
    else:
        await callback_query.message.edit_caption(callback_query.message.caption + "\n\n❌ **Rejected.**")
        try:
            await client.send_message(
                target_user_id,
                f"❌ **Deposit Rejected.**\n\nYour deposit of ₹{amount:.2f} was rejected by admin."
            )
        except Exception:
            pass


@app.on_message(filters.command(["addbalance"]) & filters.user(ADMIN_ID))
async def admin_add_balance(client: Client, message: Message):
    args = message.command
    if len(args) < 3:
        await message.reply_text("⚠️ Usage: `/addbalance <user_id> <amount>`")
        return

    try:
        target_id = int(args[1])
        amount = float(args[2])
    except ValueError:
        await message.reply_text("❌ Invalid user ID or amount.")
        return

    await update_balance(target_id, amount)
    await message.reply_text(f"✅ Added ₹{amount:.2f} to user `{target_id}`.")

    try:
        await client.send_message(target_id, f"💳 **Balance Updated!**\n\nAdmin added **₹{amount:.2f}** to your balance.")
    except Exception:
        pass

# ----------------------------------------------------
# 3. BALANCE & ORDERS NAVIGATION
# ----------------------------------------------------
@app.on_callback_query(filters.regex(r"^show_balance$"))
async def show_balance_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_data = await get_or_create_user(user_id, callback_query.from_user.username)
    balance = user_data.get("balance", 0.0)

    text = (
        f"💳 **Your Wallet Balance**\n\n"
        f"👤 User ID: `{user_id}`\n"
        f"💰 Available Balance: **₹{balance:.2f}**"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Deposit Funds", callback_data="deposit_start")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^my_orders_(\d+)$"))
async def my_orders_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    page = int(callback_query.data.split("_")[2])
    limit = 5
    skip = (page - 1) * limit

    total_orders = await orders_col.count_documents({"user_id": user_id})
    cursor = orders_col.find({"user_id": user_id}).sort("timestamp", -1).skip(skip).limit(limit)
    orders = await cursor.to_list(length=limit)

    if not orders:
        text = "📦 **You have no past orders.**"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")]])
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        return

    text = f"📦 **Your Order History** (Page {page})\n\nClick any order below to view full details:"
    buttons = []

    for order in orders:
        item_id = order.get("item_id")
        price = order.get("price_inr")
        buttons.append([InlineKeyboardButton(f"🆔 #{item_id} - ₹{price}", callback_data=f"order_info_{item_id}")])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"my_orders_{page - 1}"))
    if total_orders > skip + limit:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"my_orders_{page + 1}"))

    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")])

    await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@app.on_callback_query(filters.regex(r"^order_info_(.+)"))
async def order_info_callback(client: Client, callback_query: CallbackQuery):
    item_id = callback_query.data.split("_")[2]
    user_id = callback_query.from_user.id

    order = await orders_col.find_one({"item_id": str(item_id), "user_id": user_id})
    if not order:
        await callback_query.answer("⚠️ Order not found.", show_alert=True)
        return

    phone = order.get("phone", "N/A")
    price = order.get("price_inr", "0")
    hex_session = order.get("hex_session", "N/A")
    dc_id = order.get("dc_id", "4")
    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(order.get("timestamp", time.time())))

    PURCHASED_SESSIONS[str(item_id)] = {
        "hex_session": hex_session,
        "phone": phone,
        "dc_id": dc_id
    }

    text = (
        f"📦 **Order Details for Account #{item_id}**\n\n"
        f"📅 Date: {date_str}\n\n"
        f"📱 **Phone No**: `{phone}`\n\n"
        f"💳 Paid: ₹{price}\n"
        f"📡 DC ID: {dc_id}\n\n"
        f"🔑 **Hex Session:**\n<blockquote expandable><code>{hex_session}</code></blockquote>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 Get OTP", callback_data=f"getotp_{item_id}")],
        [InlineKeyboardButton("📱 Devices", callback_data=f"devices_{item_id}")],
        [InlineKeyboardButton("⬅️ Back to Orders", callback_data="my_orders_1")]
    ])

    await callback_query.message.edit_text(text, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^show_support$"))
async def show_support_callback(client: Client, callback_query: CallbackQuery):
    text = (
        f"🛠️ **Customer Support**\n\n"
        f"For any issues, queries, or assistance, contact:\n"
        f"👉 Admin: {SUPPORT_USERNAME}"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")]])
    await callback_query.message.edit_text(text, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^show_source_code$"))
async def show_source_code_callback(client: Client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")]])
    await callback_query.message.edit_text(SOURCE_CODE_TEXT, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^cat_"))
async def show_regions(client: Client, callback_query: CallbackQuery):
    category = callback_query.data.replace("cat_", "")
    text = f"⭐ Selected Category: `{category.replace('_', ' ').title()}`\n\n👇 **Select a region to browse stock:**"
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇮🇳 India", callback_data=f"reg_{category}_IN"),
            InlineKeyboardButton("🇺🇸 USA", callback_data=f"reg_{category}_US")
        ],
        [
            InlineKeyboardButton("🇮🇩 Indonesia", callback_data=f"reg_{category}_ID"),
            InlineKeyboardButton("🇲🇲 Myanmar", callback_data=f"reg_{category}_MM")
        ],
        [
            InlineKeyboardButton("🇧🇩 Bangladesh", callback_data=f"reg_{category}_BD"),
            InlineKeyboardButton("🇻🇳 Vietnam", callback_data=f"reg_{category}_VN")
        ],
        [InlineKeyboardButton("🌐 Global", callback_data=f"reg_{category}_GLOBAL")],
        [InlineKeyboardButton("🔍 Search Country Name or Symbol", callback_data="search_country")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^search_country$"))
async def ask_country_search(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    USER_STATES[user_id] = {"state": "awaiting_country_query"}
    
    await callback_query.message.edit_text(
        "🔍 **Search Country**\n\n"
        "Send a **Country Name** or **Symbol**:\n"
        "• **Names:**  `United States`, `India`, `Brazil`, `Germany`, `Russia`\n"
        "• **Symbols:**  `US`, `IN`, `BR`, `DE`, `RU`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Cancel", callback_data="main_menu")]
        ])
    )

@app.on_message(filters.command(["search"]) & filters.private)
async def search_handler(client: Client, message: Message):
    user_id = message.from_user.id
    USER_STATES[user_id] = {"state": "awaiting_country_query"}
    
    await message.reply_text(
        "🔍 **Search Country**\n\n"
        "Send a **Country Name** or **Symbol**:\n"
        "• **Names:**  `United States`, `India`, `Brazil`, `Germany`, `Russia`\n"
        "• **Symbols:**  `US`, `IN`, `BR`, `DE`, `RU`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Cancel", callback_data="main_menu")]
        ])
    )


# 1. Update main menu to include "Old Accounts" button
@app.on_callback_query(filters.regex(r"^(main_menu|cat_usetrow)$"))
async def main_menu_callback(client: Client, callback_query: CallbackQuery):
    text = (
        "📱 **Telegram Accounts Store**\n\n"
        "🔄 Prices are fetched live from the panel.\n"
        "Please select a category below to get started:\n\n"
        
        "⚠️ **<u>CHEAP ACCOUNTS</u>**\n"
        "• Mixed origins, lowest prices.\n"
        "• May include phishing, stealer, or brute-force accounts.\n"
        "• **For temporary use only.** These can be banned or deleted by Telegram at any time.\n\n"
        
        "✅ **<u>GOOD ACCOUNTS</u>**\n"
        "• Safe origins (Autoreg, Personal, or Self-Registered).\n"
        "• **High quality.** Perfect for personal or long-term use.\n\n"
        
        "📧 **Mail:** Email login is available.\n"
        "🚫 **NoMail:** No email login available.\n\n"
        
        "📌 **Important Notes:**\n"
        "1. **Login immediately** after purchasing your account.\n"
        "2. For maximum security, immediately add **Two-Step Verification** in your Telegram Settings -> Privacy and Security.\n"
        "3. All accounts are 100% spam-free and restriction-free.\n\n"
        
        "❌ **Refund Policy:**\n"
        "Strictly **NO REFUNDS** under any circumstances."
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📧 Cheap + Mail", callback_data="cat_cheap_mail"),
            InlineKeyboardButton("🚫 Cheap + NoMail", callback_data="cat_cheap_nomail")
        ],
        [
            InlineKeyboardButton("⭐ Good + Mail 📧", callback_data="cat_good_mail"),
            InlineKeyboardButton("⭐ Good + NoMail 🚫", callback_data="cat_good_nomail")
        ],
      #  [
      #    InlineKeyboardButton("⏳ Old Accounts", callback_data="random_old_accounts")
     #   ],
        [
          InlineKeyboardButton("📊 Cheapest Price Accounts", callback_data="cat_cheapest")
        ],
        [
          InlineKeyboardButton("💎 Telegram Premium Account", callback_data="cat_premium")
        ],
        [
          InlineKeyboardButton("🚫 Spammed Block Account", callback_data="cat_spam")
        ],
        [InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]
    ])
    await callback_query.message.edit_text(text=text, reply_markup=keyboard, disable_web_page_preview=True)


# 2. Trigger Country Search state specifically for Old Accounts
@app.on_callback_query(filters.regex(r"^random_old_accounts$"))
async def ask_old_account_country(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    USER_STATES[user_id] = {"state": "awaiting_old_account_country"}
    
    await callback_query.message.edit_text(
        "⏳ **Old Accounts Search**\n\n"
        "Send a **Country Name** or **Symbol**:\n"
        "• **Names:** `United States`, `India`, `Brazil`, `Germany`, `Russia`\n"
        "• **Symbols:** `US`, `IN`, `BR`, `DE`, `RU`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Cancel", callback_data="main_menu")]
        ])
    )

@app.on_callback_query(filters.regex(r"^oldcountry_"))
async def old_account_country_callback(client: Client, callback_query: CallbackQuery):
    # Extract country code from callback data (e.g., "oldcountry_US" -> "US")
    country_code = callback_query.data.split("_")[-1].upper()
    user_id = callback_query.from_user.id
    
    # Clear any active user state
    USER_STATES.pop(user_id, None)

    flag = get_flag_emoji(country_code) if country_code != "GLOBAL" else "🌐"
    text = (
        f"{flag} **Country Selected: {country_code}**\n\n"
        f"Please select the quality for **{country_code}** Old Accounts:"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📧 Cheap + Mail", callback_data=f"oldqual_cheap_mail_{country_code}"),
            InlineKeyboardButton("🚫 Cheap + NoMail", callback_data=f"oldqual_cheap_nomail_{country_code}")
        ],
        [
            InlineKeyboardButton("⭐ Good + Mail 📧", callback_data=f"oldqual_good_mail_{country_code}"),
            InlineKeyboardButton("⭐ Good + NoMail 🚫", callback_data=f"oldqual_good_nomail_{country_code}")
        ],
        [
            InlineKeyboardButton("📊 Cheapest", callback_data=f"oldqual_cheapest_{country_code}")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="random_old_accounts")]
    ])
    
    await callback_query.message.edit_text(text, reply_markup=keyboard)
    

# 4. Handle Year Selection Callback and route to fetch function
@app.on_callback_query(filters.regex(r"^oldyear_"))
async def old_year_selected(client: Client, callback_query: CallbackQuery):
    parts = callback_query.data.split("_")
    year = int(parts[-1])
    country_code = parts[-2]
    quality = "_".join(parts[1:-2])
    
    await callback_query.answer(f"Searching {year} ({quality.replace('_', ' ')}) stock for {country_code}...")
    await fetch_and_send_stock(client, callback_query, category=f"old_{quality}", country_code=country_code, year=year, page=1)


@app.on_callback_query(filters.regex(r"^oldqual_"))
async def old_account_quality_selected(client: Client, callback_query: CallbackQuery):
    # Data format: oldqual_{quality}_{country_code}
    parts = callback_query.data.split("_")
    quality = "_".join(parts[1:-1])
    country_code = parts[-1]

    current_year = datetime.now().year
    year_buttons = []
    row = []
    
    # Embed quality and country_code into year callbacks
    for year in range(2013, current_year + 1):
        row.append(InlineKeyboardButton(str(year), callback_data=f"oldyear_{quality}_{country_code}_{year}"))
        if len(row) == 3:
            year_buttons.append(row)
            row = []
    if row:
        year_buttons.append(row)

    year_buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"oldcountry_{country_code}")])

    flag = get_flag_emoji(country_code) if country_code != "GLOBAL" else "🌐"
    await callback_query.message.edit_text(
        f"{flag} **Country:** `{country_code}` | **Quality:** `{quality.replace('_', ' ').title()}`\n"
        f"📅 **Select the Creation Year:**",
        reply_markup=InlineKeyboardMarkup(year_buttons)
    )

# 5. Updated Stock Fetching Function supporting Old Accounts and Year calculations
async def fetch_and_send_stock(client, target_ui, category: str, country_code: str, year: int = None, page: int = 1):
    url = "https://api.lzt.market/telegram"

    if "premium" in category:
        params = {
            "order_by": "price_to_up", 
            "premium": "yes",
            "spam": "no", 
            "min_authorizations": 1, 
            "max_authorizations": 1,
            "item_state": "active",
            "seller_quality": 40,
            "page": page
        } 
    elif "spam" in category:
        params = {
            "order_by": "price_to_up", 
            "spam": "yes", 
            "min_authorizations": 1, 
            "max_authorizations": 1,
            "item_state": "active",
            "seller_quality": 40,
            "page": page
        } 
    else:
        params = {
            "order_by": "price_to_up", 
            "spam": "no", 
            "min_authorizations": 1, 
            "max_authorizations": 1,
            "item_state": "active",
            "page": page
        } 
    
    if country_code != "GLOBAL":
        params["country[]"] = country_code.upper()

        # Check if category contains "old"
    if "old" in category and year:
        current_year = datetime.now().year
        age_in_years = max(1, current_year - year)
        params["session_age"] = age_in_years
        params["session_age_period"] = "year"

    # Apply quality filters (works for both standard and old account searches)
    if "mail" in category and "nomail" not in category:
        params["email"] = "yes"
    elif "nomail" in category:
        params["email"] = "no"

    if "good" in category:
        params["origin[]"] = ["autoreg", "personal", "self_registration"]
        params["seller_quality"] = 40
   
   # elif "cheap" in category:
   #     params["origin[]"] = ["phishing", "stealer", "brute"]

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=get_lzt_headers()) as resp:
            if resp.status != 200:
                text = f"❌ Failed to fetch accounts from API.\n\n**Try after 10 minutes**"
                if isinstance(target_ui, CallbackQuery):
                    await target_ui.message.edit_text(text)
                else:
                    await target_ui.reply_text(text)
                return
            data = await resp.json()

    all_items = data.get("items", [])
    items = all_items[:6]

    clean_quality = category.replace("old_", "").replace("_", " ").title()
    raw_qual = category.replace("old_", "")
    if not items:
        if "old" in category and year:
            text = f"❌ In **{year}**, **{country_code}** ({clean_quality}) accounts are not available."
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Categories", callback_data=f"oldqual_{raw_qual}_{country_code}")]])
        else:
            text = f"❌ No stock available for category `{category}` in `{country_code}` (Page {page})."
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Categories", callback_data="main_menu")]])
            
        if isinstance(target_ui, CallbackQuery):
            await target_ui.message.edit_text(text, reply_markup=keyboard)
        else:
            await target_ui.reply_text(text, reply_markup=keyboard)
        return

    items_per_page = 6
    start_index = (page - 1) * items_per_page + 1

    buttons = []
    for i, item in enumerate(items, start=start_index):
        item_id = item.get("item_id")
        account_country = item.get("country") or item.get("country_code") or item.get("telegram_country") or "GLOBAL"
        item_flag = get_flag_emoji(account_country.upper())
        
        raw_price_usd = float(item.get("price", 0))
        display_price_usd = raw_price_usd * PROFIT_MARGIN
        display_price_inr = f"{(display_price_usd * USD_TO_INR):.2f}"
      
        buttons.append([
            InlineKeyboardButton(
                f"{i}. {item_flag} - ₹{display_price_inr} (${display_price_usd:.2f})", 
                callback_data=f"buy_{item_id}_{display_price_inr}_{raw_price_usd}"
            )
        ])


    nav_buttons = []
    if page > 1:
        cb_prev = f"oldpage_{raw_qual}_{country_code}_{year}_{page - 1}" if "old" in category else f"page_{category}_{country_code}_{page - 1}"
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=cb_prev))
    if len(all_items) > 6:
        cb_next = f"oldpage_{raw_qual}_{country_code}_{year}_{page + 1}" if "old" in category else f"page_{category}_{country_code}_{page + 1}"
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=cb_next))

    if nav_buttons:
        buttons.append(nav_buttons)

    refresh_cb = f"oldpage_{raw_qual}_{country_code}_{year}_{page}" if "old" in category else f"page_{category}_{country_code}_{page}"
    back_cb = f"oldqual_{raw_qual}_{country_code}" if "old" in category else f"cat_{category}"

    buttons.append([
        InlineKeyboardButton("🔄 Refresh", callback_data=refresh_cb),
        InlineKeyboardButton("⬅️ Back", callback_data=back_cb)
    ])

    flag = get_flag_emoji(country_code) if country_code != "GLOBAL" else "🌐"
    title_extra = f"Year {year}" if category == "old" else category.title()
    if "spam" in category:
        spam_st = "🚫 Spammed Acc"
    else:
        spam_st = "🆓 Spam-Free"
    text = (
        f"{flag} **Available Accounts: {country_code}** ({title_extra}) - Page {page}\n\n"
        f"⚡ Instant Delivery | {spam_st}\n"
        f"👇 Select an account to purchase:"
    )
    if isinstance(target_ui, CallbackQuery):
        try: await target_ui.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        except: pass
    else:
        try: await target_ui.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        except: pass


# Updated Pagination Callback for Old Accounts
@app.on_callback_query(filters.regex(r"^oldpage_"))
async def paginate_old_accounts_callback(client: Client, callback_query: CallbackQuery):
    # Callback format: oldpage_{quality}_{country_code}_{year}_{page}
    parts = callback_query.data.split("_")
    
    # Extract fixed trailing elements first
    page = int(parts[-1])
    year = int(parts[-2])
    country_code = parts[-3]
    
    # Reassemble any leading terms between 'oldpage' and country_code as quality
    quality = "_".join(parts[1:-3])

    await callback_query.answer(f"Loading page {page}...")
    
    await fetch_and_send_stock(
        client, 
        callback_query, 
        category=f"old_{quality}", 
        country_code=country_code, 
        year=year, 
        page=page
    )



@app.on_callback_query(filters.regex(r"^reg_"))
async def list_accounts_callback(client: Client, callback_query: CallbackQuery):
    parts = callback_query.data.split("_")
    category = "_".join(parts[1:-1])
    country_code = parts[-1]
    await callback_query.answer(f"Fetching {country_code} stock...")
    await fetch_and_send_stock(client, callback_query, category, country_code, page=1)


@app.on_callback_query(filters.regex(r"^page_"))
async def paginate_accounts_callback(client: Client, callback_query: CallbackQuery):
    parts = callback_query.data.split("_")
    page = int(parts[-1])
    country_code = parts[-2]
    category = "_".join(parts[1:-2])
    await callback_query.answer(f"Loading page {page}...")
    await fetch_and_send_stock(client, callback_query, category, country_code, page=page)

# ----------------------------------------------------
# 5. FAST BUY WITH BALANCE DEDUCTION & LOGGING
# ----------------------------------------------------

PROCESSING_ITEMS = set()

from deep_translator import GoogleTranslator

async def safe_translate_or_clean(text: str) -> str:
    """Translates non-English text to English. If translation fails, removes non-English text."""
    if not text:
        return ""

    # Remove LZTBB code tooltips and HTML markup
    text = re.sub(r'\[tooltip=\d+\](.*?)\[/tooltip\]', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text).strip()

    if not text:
        return ""

    # Check if text contains Cyrillic or non-ASCII characters
    if re.search(r'[\u0400-\u04FF]', text):
        try:
            loop = asyncio.get_running_loop()
            translated = await loop.run_in_executor(
                None, 
                lambda: GoogleTranslator(source='auto', target='en').translate(text)
            )
            if translated and not re.search(r'[\u0400-\u04FF]', translated):
                return translated
    
        except Exception as e:
            print(f"Translation failed: {e}. Falling back to text cleanup.")
            # Fallback: Filter out lines containing foreign characters
            clean_lines = [
                line.strip() for line in text.split('\n') 
                if not re.search(r'[\u0400-\u04FF]', line)
            ]
            return " ".join([l for l in clean_lines if l]).strip()

    return text


@app.on_callback_query(filters.regex(r"^buy_"))
async def preview_purchase(client: Client, callback_query: CallbackQuery):
    parts = callback_query.data.split("_")
    item_id = parts[1]
    price_inr = float(parts[2])
    raw_price_usd = parts[3]

    await callback_query.answer("🔎 Extracting account details...")
    headers = get_lzt_headers()

    async with aiohttp.ClientSession() as session:
        info_url = f"https://api.lzt.market/{item_id}"
        async with session.get(info_url, headers=headers) as resp:
            data = await resp.json()

    item_info = data.get("item", {})
    if not item_info or "errors" in data:
        await callback_query.message.edit_text("❌ **Item is no longer available or invalid.**")
        return

    # Process Title & Description concurrently
    raw_title = item_info.get("title_en") or item_info.get("title") or ""
    raw_desc = item_info.get("description_en") or item_info.get("description") or ""

    clean_title, clean_desc = await asyncio.gather(
        safe_translate_or_clean(raw_title),
        safe_translate_or_clean(raw_desc)
    )

    if not clean_title or clean_title == "Telegram Account":
        clean_title = f"Telegram Account #{item_id}"

    # 1. Basic & Network Info
    country = item_info.get("telegram_country", item_info.get("country", "Unknown"))
    dc_id = item_info.get("telegram_dc_id", "Unknown")
    origin = str(item_info.get("item_origin", "Unknown")).capitalize()

    # 2. Timestamps & Session Age
    last_act_ts = (
        item_info.get("item_update_date") 
        or item_info.get("telegram_last_activity") 
        or item_info.get("telegram_last_seen")
    )
    last_active_str = format_last_active(last_act_ts)

    session_created_ts = item_info.get("telegram_session_created_at")
    session_created_str = (
        time.strftime("%Y-%m-%d %H:%M", time.localtime(session_created_ts))
        if session_created_ts else "Unknown"
    )

    # 3. Security & Account Specs
    telegram_id_count = item_info.get("telegram_id_count", 0)
    id_digits_str = f"`{telegram_id_count}` Digits" if telegram_id_count else "Unknown"
    
    # Check Premium & Format Expiry
    is_premium = item_info.get("telegram_premium") == 1
    premium_expires_ts = item_info.get("telegram_premium_expires")

    if is_premium:
        if premium_expires_ts:
            expiry_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(premium_expires_ts))
            has_premium = f"Yes 🌟 (Expires: `{expiry_str}`)"
        else:
            has_premium = "Yes 🌟"
    else:
        has_premium = "No"

    has_password = "Yes (2FA Set) 🔒" if item_info.get("telegram_password") == 1 else "No (2FA Free) 🔓"
    has_email = "Yes 📧" if item_info.get("telegram_email") == 1 else "No"
    is_personal = "Yes" if item_info.get("isPersonalAccount") else "No"
    
    spam_block = item_info.get("telegram_spam_block")
    
    # Check for dedicated timestamp fields if available
    expire_ts = (
        item_info.get("telegram_spam_block_until") 
        or item_info.get("telegram_spam_block_expires")
        or item_info.get("telegram_spam_expires")
    )

    # Convert numeric values safely
    try:
        spam_val = float(spam_block) if spam_block is not None else -1
    except (ValueError, TypeError):
        spam_val = None

    # Helper function to format timestamp into human-readable string
    def format_ts(ts):
        try:
            return time.strftime("%Y-%m-%d %H:%M", time.localtime(float(ts)))
        except (ValueError, TypeError):
            return None

    # 1. Clean / No Restriction
    if spam_block in [None, "none", "no", "false", ""] or spam_val == -1 or spam_val == 0:
        spam_status = "Clean (No Restrictions) ✅"

    # 2. Check if a dedicated expiry timestamp exists
    elif expire_ts and format_ts(expire_ts):
        unblock_time = format_ts(expire_ts)
        spam_status = f"Spambot Restricted ⚠️ (Until: `{unblock_time}`)"

    # 3. Direct Unix Timestamp inside `telegram_spam_block`
    elif spam_val and spam_val > 1000000000:
        unblock_time = format_ts(spam_val)
        spam_status = f"Spambot Restricted ⚠️ (Until: `{unblock_time}`)"

    # 4. Known Negative / Status Codes without timestamp
    elif spam_val == -2:
        spam_status = "Spambot Restricted ⚠️ (Temporary)"
    elif spam_val == -3:
        spam_status = "Spambot Restricted ⚠️"
    elif spam_val == -4 or (isinstance(spam_block, str) and spam_block.lower() == "geo"):
        spam_status = "Spambot Restricted ⚠️ (By GEO)"
    elif spam_val == 1 or (isinstance(spam_block, str) and "perm" in spam_block.lower()):
        spam_status = "Spambot Restricted ⚠️ (Permanent)"
        
    else:
        spam_status = "Spambot Restricted ⚠️"
        
    
    # 4. Activity & Permissions
    authorizations = item_info.get("telegram_authorizations", 1)
    channels_count = item_info.get("telegram_channels_count", 0)
    chats_count = item_info.get("telegram_chats_count", 0)
    conversations_count = item_info.get("telegram_conversations_count", 0)
    admin_count = item_info.get("telegram_admin_count", 0)
    admin_subs = item_info.get("telegram_admin_subs_count", 0)
    contacts_count = item_info.get("telegram_contacts_count", 0)
    bots_count = len(item_info.get("telegramBots", []))

    # 5. Digital Assets & Stars
    stars_count = item_info.get("telegram_stars_count", 0)
    stars_rating = item_info.get("telegram_stars_rating_level", 0)
    gifts_count = item_info.get("telegram_gifts_count", 0)
    nft_gifts_count = item_info.get("telegram_gifts_nft_count", 0)
    rare_gifts_count = item_info.get("telegram_gifts_rare_count", 0)
    convert_stars = item_info.get("telegram_gifts_convert_stars", 0)
    gram_count = item_info.get("telegram_gram_count", 0)

    item_str = f"<code>#{str(item_id)[:3]}****</code>" if item_id else "<i>Unknown</i>"
    # Build Message Output
    preview_text = (
        f"📋 **Account Confirmation Details**\n\n"
        f"📦 **Item ID:** `{item_str}`\n"
        f"📝 **Title:** {clean_title}\n"
        f"🌍 **Country:** `{country}`\n"
        f"📡 **Data Center:** `DC {dc_id}`\n"
        f"🛡 **Origin:** `{origin}`\n"
        f"🕒 **Last Active:** {last_active_str}\n"
        f"📅 **Session Age:** `{session_created_str}`\n\n"
        f"⚙️ **Security & Configuration:**\n"
        f"• **Telegram ID Length:** {id_digits_str}\n"
        f"• **Premium Status:** {has_premium}\n"
        f"• **2FA Password:** {has_password}\n"
        f"• **Linked Email:** {has_email}\n"
        f"• **Personal Account:** {is_personal}\n"
        f"• **Active Sessions:** `{authorizations}`\n"
        f"• **Spam Status:** {spam_status}\n\n"
        f"📊 **Usage & Structural Stats:**\n"
        f"• **Chats / Channels:** {chats_count} / {channels_count}\n"
        f"• **Conversations:** {conversations_count}\n"
        f"• **Admin Channels:** {admin_count} (Subs: {admin_subs})\n"
        f"• **Contacts Count:** {contacts_count}\n"
        f"• **Associated Bots:** {bots_count}\n\n"
        f"🎁 **Assets & Digital Items:**\n"
        f"• **Stars Balance:** `{stars_count}` ⭐ (Rating Lvl: {stars_rating})\n"
        f"• **Total Gifts:** `{gifts_count}` (NFT: {nft_gifts_count} | Rare: {rare_gifts_count})\n"
        f"• **Convertible Stars:** `{convert_stars}`\n"
        f"• **Grams Count:** `{gram_count}`\n\n"
        f"💰 **Total Price:** `₹{price_inr:.2f}`"
    )

  #  if clean_desc and clean_desc != "Telegram Account":
  #      preview_text += f"\n\n📄 **Description:**\n_{clean_desc}_"

    confirm_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm Purchase", callback_data=f"confirmbuy_{item_id}_{price_inr}_{raw_price_usd}"),
            InlineKeyboardButton("❌ Cancel", callback_data="back_to_start")
        ]
    ])

    await callback_query.message.edit_text(preview_text, reply_markup=confirm_keyboard)



@app.on_callback_query(filters.regex(r"^confirmbuy_"))
async def process_purchase(client: Client, callback_query: CallbackQuery):
    parts = callback_query.data.split("_")
    item_id = parts[1]
    price_inr = float(parts[2])
    raw_price_usd = parts[3]
    buyer = callback_query.from_user

    # Concurrency Lock: Prevent multiple users in your bot from clicking the same item
    if item_id in PROCESSING_ITEMS:
        await callback_query.answer("⚠️ Another user is currently purchasing this item!", show_alert=True)
        return

    if buyer.id in PROCESSING_ITEMS:
        await callback_query.answer("⚠️ Another user is currently purchasing this item!", show_alert=True)
        return

    PROCESSING_ITEMS.add(item_id)
    PROCESSING_ITEMS.add(buyer.id)

    try:
        user_data = await get_or_create_user(buyer.id, buyer.username)
        current_balance = user_data.get("balance", 0.0)

        if current_balance < price_inr:
            await callback_query.answer(
                f"❌ Insufficient Balance! Needed: ₹{price_inr:.2f}, You have: ₹{current_balance:.2f}",
                show_alert=True
            )
            return

        try: await callback_query.message.edit_text("🔄 **Reserving item on database...**")
        except: pass
        headers = get_lzt_headers()

        async with aiohttp.ClientSession() as session:
            # 2. Call /fast-buy directly
            # LZT automatically checks account validity before deducting your LZT balance

            user_data = await get_or_create_user(buyer.id, buyer.username)
            current_balance = user_data.get("balance", 0.0)

            if current_balance < price_inr:
                try:
                    await callback_query.answer(
                        f"❌ Insufficient Balance! Needed: ₹{price_inr:.2f}, You have: ₹{current_balance:.2f}",
                        show_alert=True
                    )
                except: return 
                return
            
            buy_url = f"https://api.lzt.market/{item_id}/fast-buy"
            params = {"price": raw_price_usd}

            async with session.post(buy_url, params=params, headers=headers) as resp:
                buy_data = await resp.json()

        # If session is invalid/blocked, or someone on the web bought it, LZT rejects it here
        if "errors" in buy_data or not buy_data.get("item"):
            err_msg = buy_data.get("errors", ["Item already sold or invalid session"])[0]
            await callback_query.message.edit_text(f"❌ **Purchase Failed:** Account Is Invalid Or Already Purchased Try Another Account.")
            if LOG_CHANNEL_ID:
                await client.send_message(LOG_CHANNEL_ID, f"Purchase Failed for Item #{item_id}: {err_msg}")
            return

        # ------------------------------------------------------------------
        # STEP 3: DEDUCT BOT USER BALANCE
        # ------------------------------------------------------------------
        await update_balance(buyer.id, -price_inr)

        item_info = buy_data.get("item", {})
        phone = item_info.get("telegram_phone", "N/A")
        session_hex = item_info.get("telegram_hex_session") or item_info.get("session_raw", "") or item_info.get("login", "")
        dc_id = item_info.get("telegram_dc_id", "4")
        password = None
        last_act_ts = item_info.get("item_update_date") or item_info.get("telegram_last_activity") or item_info.get("telegram_last_seen")
        last_active_str = format_last_active(last_act_ts)

        PURCHASED_SESSIONS[str(item_id)] = {
            "hex_session": session_hex,
            "phone": phone,
            "dc_id": dc_id
        }

        # Save order doc
        order_doc = {
            "user_id": buyer.id,
            "item_id": str(item_id),
            "phone": phone,
            "price_inr": f"{price_inr:.2f}",
            "hex_session": session_hex,
            "dc_id": dc_id,
            "password": password,
            "timestamp": time.time()
        }
        await orders_col.insert_one(order_doc)

        # Log broadcast
        if LOG_CHANNEL_ID:
            try:
                buyer_str = f"<code>{str(buyer.id)[:4]}****</code>" if buyer.id else "<i>Unknown</i>"
                item_str = f"<code>#{str(item_id)[:3]}****</code>" if item_id else "<i>Unknown</i>"
                phone_str = f"<code>{str(phone)[:5]}******</code>" if phone else "<i>Unknown</i>"
                
                log_text = (
                    "🛒 <b>NEW SUCCESSFUL PURCHASE</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 <b>Buyer ID:</b> {buyer_str}\n"
                    f"📦 <b>Item ID:</b> {item_str}\n"
                    f"📱 <b>Phone:</b> {phone_str}\n"
                    f"💰 <b>Amount Paid:</b> <code>₹{price_inr:.2f}</code>\n"
                    f"📡 <b>Data Center:</b> <code>DC {dc_id}</code>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "⚡️ <i>Transaction Processed Successfully</i>"
                )
                await client.send_message(LOG_CHANNEL_ID, log_text, parse_mode=enums.ParseMode.HTML)
            except Exception as e:
                print(f"❌ Failed to send log message: {e}")

        success_text = (
            f"✅ **Purchase Successful!**\n\n"
            f"📦 Item Id #{item_id}\n\n"
            f"📱 **Phone No:** `{phone}`\n\n"
            f"🕒 Last Active: {last_active_str}\n"
            f"📡 DC ID: {dc_id}\n\n"
            f"🔑 **Login Instructions:**\n"
            f"1. Open **Telegram Desktop** / Telegram App / **Graph Messanger** / **Plus Messenger**\n"
            f"2. Use **Get OTP** below to request the login code\n"
            f"3. Use **Devices** below to inspect/terminate other sessions\n\n"
            f"🔒 Security: Full account control after login.\n"
            f"💳 Charged: ₹{price_inr:.2f}\n\n"
            f"🔑 **Hex Session:**\n<blockquote expandable><code>{session_hex}</code></blockquote>\n"
            f"📌 **Note :- Do not Terminate Bot Session Before Login. If You Terminate Bot Session Then You Can Not Do Login.**\n\n"
            f"**⚠️ Important:- Do not share your account phone number, hex session, item id with other, if you do then they can access your account.**\n\n"
            f"**If Below Get OTP button is not working then use** `/otp item_id`"
        )

        action_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 Get OTP", callback_data=f"getotp_{item_id}")],
            [InlineKeyboardButton("📱 Devices", callback_data=f"devices_{item_id}")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_start")]
        ])

        await callback_query.message.edit_text(success_text, reply_markup=action_keyboard)

    finally:
        PROCESSING_ITEMS.discard(item_id)
        PROCESSING_ITEMS.discard(buyer.id)


# ----------------------------------------------------
# 6. OTP & TELETHON SESSION MANAGEMENT
# ----------------------------------------------------
async def parse_lzt_code(data: dict):
    """Helper function to parse the Telegram login code from LZT response."""
    # 1. Primary path: 'codes' list as returned by LZT API log
    codes_list = data.get("codes", [])
    if isinstance(codes_list, list) and len(codes_list) > 0:
        first_entry = codes_list[0]
        if isinstance(first_entry, dict) and "code" in first_entry:
            return first_entry.get("code")

    # 2. Fallback paths for direct key responses
    return (
        data.get("code") 
        or data.get("login_code") 
        or data.get("telegram_code") 
        or data.get("telegram_login_code")
    )


@app.on_message(filters.private & filters.command("otp"))
async def fetch_otp_cmd(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.reply_text("⚠️ **Usage:** `/otp <item_id>`\nExample: `/otp 123456`")
        return

    item_id = args[1].strip()
    status_msg = await message.reply_text("🔄 **Fetching OTP from Account...**")

    otp_url = f"https://api.lzt.market/{item_id}/telegram-login-code"

    async with aiohttp.ClientSession() as session:
        async with session.get(otp_url, headers=get_lzt_headers()) as resp:
            data = await resp.json()

    code = await parse_lzt_code(data)
    
    if code:
        await status_msg.edit_text(f"🔑 **Your Telegram OTP Code for #{item_id} is:** `{code}`")
    else:
        err_detail = data.get("errors", ["Request code in Telegram app first."])[0]
        await status_msg.edit_text(f"⚠️ **OTP not received:** {err_detail}")


@app.on_callback_query(filters.regex(r"^getotp_"))
async def fetch_otp(client: Client, callback_query: CallbackQuery):
    item_id = callback_query.data.split("_")[1]
    
    # 1. Answer callback query ONLY ONCE at the start to clear the loading notification
    await callback_query.answer("🔄 Fetching OTP from Account...", show_alert=False)

    otp_url = f"https://api.lzt.market/{item_id}/telegram-login-code"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(otp_url, headers=get_lzt_headers()) as resp:
                data = await resp.json()

        code = await parse_lzt_code(data)

        if code:
            # 2. Deliver the OTP as a reply message
            await callback_query.message.reply_text(
                f"🔑 **Your Telegram OTP Code for #{item_id} is:** <code>{code}</code>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            # 3. Use message.reply_text instead of callback_query.answer for failure responses
            err_detail = data.get("errors", ["Request code in Telegram app first."])[0]
            await callback_query.message.reply_text(
                f"⚠️ **OTP not received for #{item_id}:** {err_detail}"
            )

    except Exception as e:
        print(f"❌ Exception in fetch_otp callback: {e}")
        await callback_query.message.reply_text(
            f"❌ **Error fetching OTP for #{item_id}.** Please try again using `/otp {item_id}`"
        )


# Device Termination 

def create_telethon_session(hex_str: str, dc_id: int = 2):
    """
    Creates an in-memory Telethon session from LZT Hex Auth Key.
    Ensures AuthKey is exactly 256 bytes to avoid unpacking errors.
    """
    raw_bytes = bytes.fromhex(hex_str)
    
    if len(raw_bytes) >= 256:
        auth_key_bytes = raw_bytes[:256]
    else:
        raise ValueError(f"Invalid AuthKey length: expected 256 bytes, got {len(raw_bytes)}")

    dc_id = int(dc_id)
    dc_ip_map = {
        1: ("149.154.175.50", 443),
        2: ("149.154.167.50", 443),
        3: ("149.154.175.100", 443),
        4: ("149.154.167.91", 443),
        5: ("91.108.56.130", 443),
    }
    
    ip, port = dc_ip_map.get(dc_id, ("149.154.167.50", 443))
    
    session = MemorySession()
    session.set_dc(dc_id, ip, port)
    session._auth_key = AuthKey(auth_key_bytes)
    
    return session


@app.on_callback_query(filters.regex(r"^devices_"))
async def fetch_devices(client: Client, callback_query: CallbackQuery):
    item_id = str(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id

    order = await orders_col.find_one({"item_id": str(item_id), "user_id": user_id})
    if not order or not order.get("hex_session"):
        await callback_query.answer("⚠️ Order or Session not found.", show_alert=True)
        return

    hex_session = order.get("hex_session")
    dc_id = order.get("dc_id", 2)
    
    await callback_query.answer("📱 Connecting via Telethon...", show_alert=False)

    try:
        session = create_telethon_session(hex_session, dc_id=dc_id)
        tc = TelegramClient(session, API_ID, API_HASH)
        await tc.connect()

        # Check if the session is authorized before querying API
        if not await tc.is_user_authorized():
            await tc.disconnect()
            await callback_query.message.edit_text(
                "❌ You already logged out bot session so now bot can't fetch devices."
            )
            return

        authorizations = await tc(GetAuthorizationsRequest())
        await tc.disconnect()

        dev_text = f"📱 **Active Devices for Account #{item_id}:**\n\n"
        buttons = []

        for auth in authorizations.authorizations:
            if auth.current:
                dev_text += f"• **{auth.device_model}** **[🤖 BOT SESSION]**\n"
                # Bot session termination button label
                buttons.append([
                    InlineKeyboardButton(
                        "❌ Log Out This Bot 🤖",
                        callback_data=f"term_{item_id}_self"
                    )
                ])
            else:
                dev_text += f"• **{auth.device_model}**\n"
                # Other sessions show device model name only
                buttons.append([
                    InlineKeyboardButton(
                        f"❌ {auth.device_model}",
                        callback_data=f"term_{item_id}_{auth.hash}"
                    )
                ])

        dev_text += "\n**If device is not terminating then try after 24 hours because telegram doesn't allow new device to terminate old device just after login.**\n\n**📌 Note :- Do not terminate/logout bot session if you want to fetch otp and devices again because without bot session bot can not give you otp or devices information.**"
        buttons.append([InlineKeyboardButton("🔄 Refresh Devices", callback_data=f"devices_{item_id}")])
        buttons.append([InlineKeyboardButton("⬅️ Back Menu", callback_data="back_to_start")])

        try:
            await callback_query.message.edit_text(
                dev_text, 
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception:
            pass  # Suppress MESSAGE_NOT_MODIFIED error

    except Exception as e:
        error_msg = str(e)
        if "AUTH_KEY_UNREGISTERED" in error_msg or "USER_DEACTIVATED" in error_msg:
            await callback_query.message.edit_text(
                "❌ You already logged out bot session so now bot can't fetch devices."
            )
        else:
            await callback_query.message.reply_text(f"❌ Device Fetch Failed: {error_msg}")


@app.on_callback_query(filters.regex(r"^term_"))
async def terminate_session(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split("_")
    item_id = data_parts[1]
    target_hash = data_parts[2]
    user_id = callback_query.from_user.id

    order = await orders_col.find_one({"item_id": str(item_id), "user_id": user_id})
    if not order or not order.get("hex_session"):
        await callback_query.answer("⚠️ Session missing.", show_alert=True)
        return

    hex_session = order.get("hex_session")
    dc_id = order.get("dc_id", 2)
    
    await callback_query.answer("Terminating session...", show_alert=False)

    try:
        session = create_telethon_session(hex_session, dc_id=dc_id)
        tc = TelegramClient(session, API_ID, API_HASH)
        await tc.connect()

        if not await tc.is_user_authorized():
            await tc.disconnect()
            await callback_query.message.edit_text(
                "❌ You already logged out bot session so now bot can't fetch devices."
            )
            return

        # Handle Bot Session Self-Termination vs Other Session Termination
        if target_hash == "self":
            #await tc(LogOutRequest())
            #await tc.disconnect()
            await tc.log_out()
            await callback_query.message.edit_text(
                "❌ You already logged out bot session so now bot can't fetch devices."
            )
            return
        else:
            # Terminate other sessions by hash integer
            session_hash = int(target_hash)
            await tc(ResetAuthorizationRequest(hash=session_hash))
            try: await tc.disconnect()
            except: pass

        await callback_query.answer("✅ Session terminated successfully!", show_alert=True)
        await fetch_devices(client, callback_query)

    except Exception as e:
        error_msg = str(e)
        if "AUTH_KEY_UNREGISTERED" in error_msg or "REVOKED" in error_msg or "SESSION_REVOKED" in error_msg:
            await callback_query.message.edit_text(
                "❌ You already logged out bot session so now bot can't fetch devices."
            )
        elif "FRESH_RESET_AUTHORISATION_FORBIDDEN" in error_msg:
            await callback_query.answer(
                "⚠️ Telegram limits: New sessions cannot terminate other sessions for 24 hours.", 
                show_alert=True
            )
        else:
            await callback_query.answer(f"❌ Termination Failed: {error_msg}", show_alert=True)


# ----------------------------------------------------
# 4. CHEAP & COUNTRY CATALOGUE
# ---------------------------------------------------

async def send_chunked_messages(chat_id: int, lines: list):
    """Helper to send lines in 4000-character chunks inside expandable blockquotes."""
    # Reserve space for <blockquote>...</blockquote> tags (~35 chars)
    MAX_CONTENT_LENGTH = 3900  

    text_response = "\n".join(lines)
    
    if len(text_response) <= MAX_CONTENT_LENGTH:
        formatted_text = f"<blockquote expandable><b>{text_response}</b></blockquote>"
        await app.send_message(chat_id, formatted_text, parse_mode=enums.ParseMode.HTML)
    else:
        chunk = ""
        for line in lines:
            if len(chunk) + len(line) + 1 > MAX_CONTENT_LENGTH:
                formatted_chunk = f"<blockquote expandable><b>{chunk}</b></blockquote>"
                await app.send_message(chat_id, formatted_chunk, parse_mode=enums.ParseMode.HTML)
                chunk = ""
            chunk += line + "\n"
            
        if chunk:
            formatted_chunk = f"<blockquote expandable><b>{chunk}</b></blockquote>"
            await app.send_message(chat_id, formatted_chunk, parse_mode=enums.ParseMode.HTML)


async def fetch_country_price(session, country_code, semaphore):
    url = "https://api.lzt.market/telegram"
    async with semaphore:
        params = {
            "spam": "no",
            "order_by": "price_to_up",
            "min_authorizations": 1,
            "max_authorizations": 1,
            "item_state": "active",
            "country[]": country_code.upper()
        }
        try:
            async with session.get(url, params=params, headers=get_lzt_headers(), timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("items", [])
                    if items:
                        price_usd = float(items[0].get("price", 0))
                        return country_code, price_usd
        except Exception:
            pass
        return country_code, None

async def update_country_prices_job():
    """Background task running every 30 minutes to fetch, store, and broadcast prices."""
    semaphore = asyncio.Semaphore(1)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_country_price(session, c, semaphore) for c in ALL_COUNTRIES]
        results = await asyncio.gather(*tasks)

    country_cheapest = []

    for country_code, price_usd in results:
        if price_usd is not None and price_usd > 0:
            # Apply profit margin to USD price
            final_price_usd = price_usd * PROFIT_MARGIN
            # Calculate INR using the updated USD price
            price_inr = final_price_usd * USD_TO_INR
        
            country_cheapest.append({
                "country_code": country_code,
                "price_inr": price_inr,
                "price_usd": final_price_usd
            })


    if not country_cheapest:
        return

    # Sort by INR price
    country_cheapest.sort(key=lambda x: x["price_inr"])

    # Format text lines with INR and USD ($0.00)
    lines = [f"🔥 **Cheapest Prices Update ({len(country_cheapest)} Countries Found)**\n"]
    for item in country_cheapest:
        flag = get_flag_emoji(item["country_code"])
        formatted_inr = f"{item['price_inr']:.2f}".rstrip('0').rstrip('.')
        formatted_usd = f"{item['price_usd']:.2f}"
        lines.append(f"• {flag} {item['country_code']} - ₹{formatted_inr} (${formatted_usd})")

    # 1. Update MongoDB document
    await prices_collection.update_one(
        {"_id": "latest_prices"},
        {
            "$set": {
                "lines": lines,
                "updated_at": time.time()
            }
        },
        upsert=True
    )

    # 2. Automatically send update message to the designated group
    try:
        await send_chunked_messages(GROUP_ID, lines)
    except Exception as e:
        print(f"Failed to send update message to group: {e}")

@app.on_message((filters.private | filters.group) & filters.command(["cheap"]))
async def cmd_cheap_handler(client: Client, message: Message):
    try:
        user_id = message.from_user.id
    except Exception:
        return

    cached_doc = await prices_collection.find_one({"_id": "latest_prices"})

    if not cached_doc or "lines" not in cached_doc:
        return await message.reply_text("❌ No country price data available yet. Please wait for the next update cycle.")

    lines = cached_doc["lines"]
    await send_chunked_messages(message.chat.id, lines)



async def start_bot_and_scheduler():
    """Starts the bot client and initializes the scheduler on the active event loop."""
    await app.start()
    
    # Start the scheduler on the running loop
    scheduler.add_job(update_country_prices_job, "interval", minutes=120)
    scheduler.start()
    
    # Trigger initial fetch in the background immediately
    #asyncio.create_task(update_country_prices_job())
    
    print("Bot and Scheduler started successfully.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot_and_scheduler())
    
    # Keep the bot running continuously on Heroku
    from pyrogram import idle
    idle()
    
    loop.run_until_complete(app.stop())

