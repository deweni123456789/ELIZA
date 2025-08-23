import os
import yt_dlp
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

def register(app):
    @app.on_message(filters.command("video"))
    async def video_handler(client, message):
        query = " ".join(message.command[1:])
        if not query:
            return await message.reply_text(
                "⚠️ Please provide a video name.\n\nExample: `/video despacito`"
            )

        status = await message.reply_text("🔎 Searching for video…")

        os.makedirs("downloads", exist_ok=True)
        out_tmpl = os.path.join("downloads", "%(title)s [%(id)s].%(ext)s")

        # Check if cookies.txt exists
        cookie_file = "cookies.txt" if os.path.exists("cookies.txt") else None

        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
            "merge_output_format": "mp4",
            "noplaylist": True,
            "outtmpl": out_tmpl,
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
                base = f"{info.get('title')} [{info.get('id')}]"
                file_path = os.path.join("downloads", base + ".mp4")

        except Exception as e:
            return await status.edit(f"❌ Failed: `{e}`")

        caption = (
            f"🎥 **Title:** {info.get('title')}\n"
            f"📺 **Channel:** {info.get('uploader')}\n"
            f"📅 **Upload Date:** {info.get('upload_date')}\n"
            f"⏱ **Duration:** {info.get('duration')} sec\n"
            f"👁 **Views:** {info.get('view_count')}\n"
            f"👍 **Likes:** {info.get('like_count','N/A')}\n"
            f"💬 **Comments:** {info.get('comment_count','N/A')}\n\n"
            f"🙋‍♂️ **Requested by:** {message.from_user.mention}"
        )

        try:
            await client.send_video(
                chat_id=message.chat.id,
                video=file_path,
                caption=caption,
                supports_streaming=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{config.DEVELOPER.replace('@','')}")]]
                )
            )
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

        await status.delete()
