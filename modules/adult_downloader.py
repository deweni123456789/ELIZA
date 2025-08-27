import os
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import yt_dlp
from datetime import datetime

# Temporary download folder
_TEMP_DIR = "temp_ad_dl"
os.makedirs(_TEMP_DIR, exist_ok=True)

# Supported adult sites
ADULT_SITE_REGEX = re.compile(
    r"(pornhub\.com|xvideos\.com|xnxx\.com|xhamster\.com)", re.IGNORECASE
)

# Inline keyboard
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

# Format numbers like 1,234,567
def format_number(n):
    try:
        return f"{int(n):,}"
    except:
        return n

def register_adult_downloader(app: Client):
    @app.on_message(filters.private & filters.text)
    async def adult_downloader_handler(client: Client, message: Message):
        url = message.text.strip()
        
        # Check if message contains a supported adult link
        if not ADULT_SITE_REGEX.search(url):
            return  # Ignore non-adult links

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

                # Download video
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
