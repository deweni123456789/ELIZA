# modules/youtube.py
import os
import asyncio
import datetime as dt
from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from pyrogram.enums import ChatAction
from yt_dlp import YoutubeDL

# -------- Temp Dir --------
_TEMP_DIR = "temp_ytdl"
os.makedirs(_TEMP_DIR, exist_ok=True)

# Cache for callbacks
_URL_CACHE = {}


def register(app: Client):
    @app.on_message(filters.regex(r"^https?://(www\.)?(youtube\.com|youtu\.be)/"))
    async def youtube_handler(_, message: Message):
        url = message.text.strip()

        # cache id
        token = str(abs(hash(url)))
        _URL_CACHE[token] = url

        btns = [
            [
                InlineKeyboardButton("🎵 Download Audio", callback_data=f"yt_audio:{token}"),
                InlineKeyboardButton("🎥 Download Video", callback_data=f"yt_video:{token}")
            ]
        ]
        await message.reply_text(
            f"🔗 **YouTube Link Detected!**\n\nChoose an option to download 👇",
            reply_markup=InlineKeyboardMarkup(btns)
        )


async def handle_callbacks(bot: Client, query: CallbackQuery):
    data = query.data

    if data.startswith("yt_audio:") or data.startswith("yt_video:"):
        token = data.split(":")[1]
        url = _URL_CACHE.get(token)

        if not url:
            await query.answer("❌ Link expired, send again!", show_alert=True)
            return

        await query.answer()
        await query.message.edit_text("⏳ Downloading, please wait...")

        # Show typing
        await bot.send_chat_action(query.message.chat.id, ChatAction.UPLOAD_DOCUMENT)

        # yt-dlp options
        if data.startswith("yt_audio:"):
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(_TEMP_DIR, "%(id)s.%(ext)s"),
                "noplaylist": True,
                "quiet": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        else:
            ydl_opts = {
                "format": "best[ext=mp4]/best",
                "outtmpl": os.path.join(_TEMP_DIR, "%(id)s.%(ext)s"),
                "noplaylist": True,
                "quiet": True,
            }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                if data.startswith("yt_audio:"):
                    file_path = os.path.splitext(file_path)[0] + ".mp3"

            # Collect details
            title = info.get("title", "Unknown")
            channel = info.get("uploader", "Unknown")
            views = info.get("view_count", 0)
            likes = info.get("like_count", 0)
            dislikes = info.get("dislike_count", "N/A")
            comments = info.get("comment_count", 0)
            duration = str(dt.timedelta(seconds=info.get("duration", 0)))
            upload_date = info.get("upload_date", "")
            if upload_date:
                upload_date = f"{upload_date[:4]}/{upload_date[4:6]}/{upload_date[6:]}"

            caption = (
                f"📌 **{title}**\n"
                f"👤 Channel: `{channel}`\n"
                f"📅 Uploaded: `{upload_date}`\n"
                f"⏱ Duration: `{duration}`\n"
                f"👁 Views: `{views}`\n"
                f"👍 Likes: `{likes}` | 👎 Dislikes: `{dislikes}`\n"
                f"💬 Comments: `{comments}`\n\n"
                f"👨‍💻 Developer: @deweni2"
            )

            if data.startswith("yt_audio:"):
                await query.message.reply_audio(
                    audio=file_path,
                    caption=caption,
                    title=title,
                    performer=channel,
                )
            else:
                await query.message.reply_video(
                    video=file_path,
                    caption=caption,
                    supports_streaming=True
                )

        except Exception as e:
            await query.message.edit_text(f"❌ Error: `{e}`")

        finally:
            # cleanup
            try:
                os.remove(file_path)
            except:
                pass
