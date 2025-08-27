import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from datetime import datetime

_TEMP_DIR = "temp_ad_dl"
os.makedirs(_TEMP_DIR, exist_ok=True)

# Supported adult site patterns (regex)
ADULT_SITE_REGEX = re.compile(
    r"(pornhub\.com|xvideos\.com|xnxx\.com|redtube\.com|tube8\.com|youporn\.com)", re.IGNORECASE
)

# Inline keyboard template
def get_inline_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👤 Developer", url="https://t.me/deweni2"),
                InlineKeyboardButton("💬 Support Chat", url="https://t.me/slmusicmania")
            ],
            [
                InlineKeyboardButton("Private Chat Only 🔒", callback_data="private_only")
            ]
        ]
    )

# Utility to format numbers with commas
def format_number(n):
    try:
        return f"{int(n):,}"
    except:
        return n

# Main handler for adult video URLs
async def adult_downloader_handler(client, message):
    if message.chat.type != "private":
        await message.reply_text(
            "❌ This service is available only in private chat.",
            quote=True
        )
        return

    url = message.text.strip()
    if not ADULT_SITE_REGEX.search(url):
        await message.reply_text(
            "❌ This link is not from a supported adult site.",
            quote=True
        )
        return

    msg = await message.reply_text("⏳ Processing your link, please wait...")

    ydl_opts = {
        "outtmpl": os.path.join(_TEMP_DIR, "%(title)s.%(ext)s"),
        "format": "bestvideo+bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "nocheckcertificate": True,
    }

    filepath = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "Unknown")
            uploader = info.get("uploader", "Unknown")
            upload_date = info.get("upload_date", "")
            if upload_date:
                dt = datetime.strptime(upload_date, "%Y%m%d")
                upload_date = dt.strftime("%Y-%m-%d")
            views = format_number(info.get("view_count", "Unknown"))
            comments = format_number(info.get("comment_count", "0"))

            # Download the video
            filepath = ydl.prepare_filename(info)
            ydl.download([url])

        caption = (
            f"📌 **Title:** {title}\n"
            f"📺 **Channel:** {uploader}\n"
            f"📅 **Uploaded Date:** {upload_date}\n"
            f"👁 **Views:** {views}\n"
            f"💬 **Comments:** {comments}\n"
            f"\nRequested by: {message.from_user.mention}"
        )

        await message.reply_video(
            video=filepath,
            caption=caption,
            reply_markup=get_inline_keyboard()
        )

    except Exception as e:
        await msg.edit(f"❌ Failed to process your link.\nError: {e}")
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        await msg.delete()

# Register function for main.py
def register_adult_downloader(app: Client):
    app.add_handler(filters.text & filters.private, adult_downloader_handler)
