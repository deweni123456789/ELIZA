import os
import yt_dlp
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

def register(app):
    @app.on_message(filters.command("song"))
    async def song_handler(client, message):
        query = " ".join(message.command[1:])
        if not query:
            return await message.reply_text(
                "⚠️ Please provide a song name.\n\nExample: `/song despacito`"
            )

        status = await message.reply_text("🔎 Searching for song…")

        # Download best audio and convert to mp3 via ffmpeg
        out_tmpl = os.path.join("downloads", "%(title)s [%(id)s].%(ext)s")
        os.makedirs("downloads", exist_ok=True)

        ydl_opts = {
            "format": "bestaudio/best",
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

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                # If it’s a search, 'entries' exists
                if "entries" in info:
                    info = info["entries"][0]

                # The output after postprocessing will be .mp3 with the same template
                base = f"{info.get('title')} [{info.get('id')}]"
                file_path = os.path.join("downloads", base + ".mp3")

        except Exception as e:
            return await status.edit(f"❌ Failed: `{e}`")

        # Build caption with metadata and requester
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
                    [[InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{config.DEVELOPER.replace('@','')}")]]
                )
            )
        finally:
            # Clean up file to keep disk small on Railway
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass

        await status.delete()
