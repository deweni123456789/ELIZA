import os
import re
import yt_dlp
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
from datetime import datetime

def register(app):
    def sanitize_filename(name):
        """Remove illegal characters from filename"""
        return re.sub(r'[\\/*?:"<>|]', "", name)

    def safe_int(val):
        """Convert value to int safely"""
        try:
            return int(val)
        except:
            return 0

    @app.on_message(filters.command("song"))
    async def song_handler(client, message):
        query = " ".join(message.command[1:])
        if not query:
            return await message.reply_text(
                "⚠️ Please provide a song name.\n\nExample: `/song despacito`"
            )

        status = await message.reply_text("🔎 Searching for song…")
        os.makedirs("downloads", exist_ok=True)

        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "default_search": "ytsearch",
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "noprogress": True,
            "buffersize": "64K",
            "fragment_retries": 3,
            "concurrent_fragment_downloads": 4,
        }

        if os.path.exists("cookies.txt"):
            ydl_opts["cookiefile"] = "cookies.txt"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                if "entries" in info:
                    info = info["entries"][0]

                base = sanitize_filename(f"{info.get('title')} [{info.get('id')}]")
                file_path = os.path.join("downloads", base + ".mp3")
                if not os.path.exists(file_path):
                    return await status.edit(f"❌ File not found: {file_path}")

        except Exception as e:
            return await status.edit(f"❌ Failed: `{e}`")

        # Format upload date YYYY/MM/DD
        upload_date_raw = info.get('upload_date')
        try:
            upload_date = datetime.strptime(str(upload_date_raw), "%Y%m%d").strftime("%Y/%m/%d")
        except:
            upload_date = upload_date_raw

        # Numeric fields safely
        duration = safe_int(info.get('duration'))
        views = safe_int(info.get('view_count'))
        likes = safe_int(info.get('like_count'))
        comments = safe_int(info.get('comment_count'))

        caption = (
            f"🎵 **Title:** {info.get('title')}\n"
            f"📺 **Channel:** {info.get('uploader')}\n"
            f"📅 **Upload Date:** {upload_date}\n"
            f"⏱ **Duration:** {duration} sec\n"
            f"👁 **Views:** {views}\n"
            f"👍 **Likes:** {likes}\n"
            f"💬 **Comments:** {comments}\n\n"
            f"🙋‍♂️ **Requested by:** {message.from_user.mention}"
        )

        try:
            await client.send_audio(
                chat_id=message.chat.id,
                audio=file_path,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton(
                            "👨‍💻 Developer",
                            url=f"https://t.me/{config.DEVELOPER.replace('@','')}"
                        )
                    ]]
                ),
                streaming=True
            )
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

        await status.delete()
