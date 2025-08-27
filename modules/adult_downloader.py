# modules/adult_downloader.py
import os
import re
import requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

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

        status_msg = await message.reply_text("⏳ Fetching video... Please wait!")

        file_path = None
        try:
            # Detect site and extract direct video URL
            if "xvideos.com" in url:
                resp = requests.get(url)
                match = re.search(r'html5player.setVideoUrlHigh\(\'(.*?)\'\)', resp.text)
                video_url = match.group(1) if match else None
                title_match = re.search(r'<title>(.*?) - Xvideos', resp.text)
                title = title_match.group(1) if title_match else "Video"

            elif "pornhub.com" in url:
                resp = requests.get(url)
                match = re.search(r'"videoUrl":"(.*?)"', resp.text)
                video_url = match.group(1).replace("\\u0026","&") if match else None
                title_match = re.search(r'<title>(.*?) - Pornhub', resp.text)
                title = title_match.group(1) if title_match else "Video"

            else:
                await status_msg.edit("❌ Site not supported yet.")
                return

            if not video_url:
                await status_msg.edit("❌ Could not extract video URL.")
                return

            # Download video
            file_path = os.path.join(_TEMP_DIR, f"{title}.mp4")
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                with open(file_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            caption = f"🎬 Title: {title}\n👤 Requested by: {requester}"

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
