# modules/adult_downloader.py
import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

TEMP_DIR = "temp_adult"
os.makedirs(TEMP_DIR, exist_ok=True)

def register_adult_downloader(app: Client):

    @app.on_message(filters.private & filters.regex(r"https?://(www\.)?xhamster\.com/.*"))
    async def download_adult_video(client: Client, message: Message):
        url = message.text
        await message.reply("Downloading adult video, please wait... ⏳")

        ydl_opts = {
            'outtmpl': os.path.join(TEMP_DIR, '%(title)s.%(ext)s'),
            'format': 'mp4',
            'noplaylist': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            await message.reply_video(
                video=filename,
                caption=f"Downloaded from: {url}"
            )
            os.remove(filename)

        except Exception as e:
            await message.reply(f"❌ Failed to download video.\nError: {e}")
