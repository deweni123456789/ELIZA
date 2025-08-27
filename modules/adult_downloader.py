# modules/adult_downloader.py
import os
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import yt_dlp
import asyncio

_TEMP_DIR = "temp_ad_dl"
os.makedirs(_TEMP_DIR, exist_ok=True)

DEV_USERNAME = "deweni2"

def register(app):

    @app.on_message(filters.command("adult"))
    async def adult_download(_, message: Message):
        if len(message.command) < 2:
            return await message.reply_text("❌ Please provide a link.\nUsage: `/adult <link>`")

        url = message.command[1]
        requester = message.from_user.mention

        status_msg = await message.reply_text("⏳ Downloading video... Please wait!")

        file_path = None
        try:
            # yt-dlp options
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(_TEMP_DIR, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
            }

            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
            file_path = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(info)

            caption = f"🎬 Title: {info.get('title', 'N/A')}\n" \
                      f"👤 Channel: {info.get('uploader', 'N/A')}\n" \
                      f"👁 Views: {info.get('view_count', 'N/A')}\n" \
                      f"👍 Likes: {info.get('like_count', 'N/A')}\n" \
                      f"👎 Dislikes: {info.get('dislike_count', 'N/A')}\n" \
                      f"💬 Comments: {info.get('comment_count', 'N/A')}\n" \
                      f"👤 Requested by: {requester}"

            await message.reply_video(
                video=file_path,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEV_USERNAME}")]]
                )
            )
            await status_msg.delete()

        except Exception as e:
            await status_msg.edit(f"❌ Failed to download.\nError: {e}")
        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
