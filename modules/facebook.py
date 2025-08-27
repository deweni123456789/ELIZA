# modules/facebook.py
import os
import asyncio
import shutil
import tempfile

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
import yt_dlp

TEMP_DIR = "temp_fb"
os.makedirs(TEMP_DIR, exist_ok=True)


def register(app):
    @app.on_message(filters.command(["fb", "facebook"], prefixes=["/"]))
    async def fb_handler(client, message: Message):
        # --- URL ගන්න
        url = None
        if len(message.command) > 1:
            url = message.text.split(maxsplit=1)[1]
        elif message.reply_to_message and message.reply_to_message.text:
            txt = message.reply_to_message.text
            if "facebook.com" in txt or "fb.watch" in txt:
                url = txt.strip()

        if not url:
            await message.reply_text(
                "⚠️ Please send a valid Facebook video link.\n\nUsage:\n`/fb <link>`",
                quote=True
            )
            return

        status = await message.reply_text("🔎 Downloading Facebook video...", quote=True)
        await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)

        # temp dir + yt-dlp options
        tmpdir = tempfile.mkdtemp(prefix="fb_", dir=TEMP_DIR)
        outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")
        ydl_opts = {
            "outtmpl": outtmpl,
            "format": "best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "quiet": True,
        }

        try:
            loop = asyncio.get_event_loop()

            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    return ydl.prepare_filename(info)

            filepath = await loop.run_in_executor(None, _download)

        except Exception as e:
            await status.edit_text(f"❌ Download failed:\n`{e}`")
            shutil.rmtree(tmpdir, ignore_errors=True)
            return

        if not os.path.exists(filepath):
            await status.edit_text("❌ File not found after download.")
            shutil.rmtree(tmpdir, ignore_errors=True)
            return

        try:
            await client.send_video(
                chat_id=message.chat.id,
                video=filepath,
                caption="📘 Downloaded from Facebook",
                supports_streaming=True,
                reply_to_message_id=message.id
            )
            await status.delete()
        except Exception as e:
            await status.edit_text(f"❌ Upload failed:\n`{e}`")

        shutil.rmtree(tmpdir, ignore_errors=True)
