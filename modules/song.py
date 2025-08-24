import os
import re
import yt_dlp
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

def register(app):
    def sanitize_filename(name):
        """Remove illegal characters from filename"""
        return re.sub(r'[\\/*?:"<>|]', "", name)

    @app.on_message(filters.command("song"))
    async def song_handler(client, message):
        query = " ".join(message.command[1:])
        if not query:
            return await message.reply_text(
                "⚠️ Please provide a song name.\n\nExample: `/song despacito`"
            )

        status = await message.reply_text("🔎 Searching for song…")

        os.makedirs("downloads", exist_ok=True)
        out_tmpl = os.path.join("downloads", "%(title)s [%(id)s].%(ext)s")

        # Check if cookies.txt exists
        cookie_file = "cookies.txt" if os.path.exists("cookies.txt") else None

        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "noplaylist": True,
            "outtmpl": out_tmpl,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "quiet": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "default_search": "ytsearch",
        }

        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                if "entries" in info:
                    info = info["entries"][0]

                # Sanitize filename
                base = sanitize_filename(f"{info.get('title')} [{info.get('id')}]")
                file_path = os.path.join("downloads", base + ".mp3")

                if not os.path.exists(file_path):
                    return await status.edit(f"❌ File not found: {file_path}")

        except Exception as e:
            return await status.edit(f"❌ Failed: `{e}`")

        caption = (
            f"🎵 **Title:** {info.get('title')}\n"
            f"📺 **Channel:** {info.get('uploader')}\n"
            f"📅 **Upload Date:** {info.get('upload_date')}\n"
            f"⏱ **Duration:** {info.get('duration')} sec\n"
            f"👁 **Views:** {info.get('view_count')}\n"
            f"👍 **Likes:** {info.get('like_count','N/A')}\n"
            f"💬 **Comments:** {info.get('comment_count','N/A')}\n\n"
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
                )
            )
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

        await status.delete()
