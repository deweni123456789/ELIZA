import secrets
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import re

DEV_USERNAME = "deweni2"

# supported adult domains
ADULT_DOMAINS = ["pornhub.com", "xvideos.com", "xnxx.com", "xhamster.com"]
ADULT_REGEX = re.compile(r"(https?://[^\s]*?(?:" + "|".join(ADULT_DOMAINS) + r")[^\s]*)", re.IGNORECASE)

def register(app: Client):

    # 1️⃣ Private chat handler - download normally (same as previous)
    @app.on_message(filters.private & filters.regex(ADULT_REGEX))
    async def private_handler(client, message: Message):
        url = message.text.strip()
        # call your download function here (video only)
        await message.reply_text(f"🔞 Adult video detected! Downloading video…", quote=True)
        # call your existing video download logic

    # 2️⃣ Group chat handler - just send private chat redirect button
    @app.on_message(filters.group & filters.regex(ADULT_REGEX))
    async def group_handler(client, message: Message):
        url = message.text.strip()
        token = secrets.token_hex(6)

        buttons = [
            [InlineKeyboardButton("🔞 Get in Private Chat", url=f"https://t.me/{client.me.username}?start={token}")],
            [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEV_USERNAME}")]
        ]

        await message.reply_text(
            "⚠️ Adult link detected! For safety, please use my private chat to download videos.",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
