import os
import re
import yt_dlp
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
from datetime import datetime, timedelta

def register(app):
    def sanitize_filename(name):
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

        ydl_opts = {
            "format": "bestaudio/best",
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
        }

        if os.path.exists("cookies.txt"):
            ydl_opts["cookiefile"] = "cookies.txt"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                if "entries" in info:
                    info = info["entries"][0]

                filename = ydl.prepare_filename(info)
                file_path = os.path.splitext(filename)[0] + ".mp3"

                if not os.path.exists(file_path):
                    return await status.edit(f"❌ File not found: {file_path}")

        except Exception as e:
            return await status.edit(f"❌ Failed: `{e}`")

        # --- Date conversion to YYYY/MM/DD ---
        upload_date_raw = info.get('upload_date')  # usually YYYYMMDD
        try:
            upload_date = datetime.strptime(str(upload_date_raw), "%Y%m%d").strftime("%Y/%m/%d")
        except:
            upload_date = upload_date_raw

        # --- Uploaded time ---
        upload_time = info.get("release_date") or "N/A"

        # --- Length formatting ---
        duration_sec = info.get("duration")
        if duration_sec:
            length_str = str(timedelta(seconds=duration_sec))
        else:
            length_str = "N/A"

        # --- File size ---
        filesize = info.get("filesize_approx") or info.get("filesize") or 0
        if filesize:
            size_mb = round(filesize / (1024 * 1024), 2)
            file_size_str = f"{size_mb} MB"
        else:
            file_size_str = "N/A"

        # --- Caption ---
        caption = (
            f"🎵 **Title:** {info.get('title')}\n"
            f"📺 **Channel:** {info.get('uploader')}\n"
            f"📂 **Category:** {info.get('categories', ['N/A'])[0]}\n"
            f"📅 **Upload Date:** {upload_date}\n"
            f"🕒 **Uploaded Time:** {upload_time}\n"
            f"⏱ **Duration:** {length_str}\n"
            f"👁 **Views:** {info.get('view_count')}\n"
            f"👍 **Likes:** {info.get('like_count','N/A')}\n"
            f"👎 **Dislikes:** N/A\n"
            f"💬 **Comments:** {info.get('comment_count','N/A')}\n"
            f"📦 **File Size:** {file_size_str}\n\n"
            f"🔗 [Watch on YouTube]({info.get('webpage_url')})\n\n"
            f"🙋‍♂️ **Requested by:** {message.from_user.mention}\n"
            f"🤖 **Uploaded by:** {config.BOT_NAME}"
        )

        try:
            await client.send_audio(
                chat_id=message.chat.id,
                audio=file_path,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "👨‍💻 Developer",
                                url=f"https://t.me/{config.DEVELOPER.replace('@','')}"
                            ),
                            InlineKeyboardButton(
                                "🎵 Support Group",
                                url="https://t.me/slmusicmania"
                            )
                        ]
                    ]
                )
            )
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

        await status.delete()
