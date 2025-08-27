# modules/facebook.py
import os
import asyncio
import shutil
import tempfile

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction

import yt_dlp


# Create temp dir
TEMP_DIR_ROOT = "temp_fb"
os.makedirs(TEMP_DIR_ROOT, exist_ok=True)


def register(app):
    @app.on_message(filters.command(["fb", "facebook"]))
    async def fb_handler(client, message: Message):
        # Get URL from command or reply
        url = None
        if len(message.command) > 1:
            url = message.command[1].strip()
        elif message.reply_to_message and message.reply_to_message.text:
            text = message.reply_to_message.text
            if "facebook.com" in text or "fb.watch" in text:
                url = text.strip()

        if not url:
            await message.reply_text("❗️ Please send a Facebook video link.\nUsage:\n`/fb <link>`", quote=True)
            return

        info_msg = await message.reply_text("🔎 Preparing download...", quote=True)
        await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)

        # yt-dlp options
        tmpdir = tempfile.mkdtemp(prefix="fb_", dir=TEMP_DIR_ROOT)
        outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")
        ydl_opts = {
            "outtmpl": outtmpl,
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "quiet": True,
            "nocheckcertificate": True,
        }

        try:
            loop = asyncio.get_event_loop()

            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    base, _ = os.path.splitext(filename)
                    return base + ".mp4"

            filepath = await loop.run_in_executor(None, _download)

        except Exception as e:
            await info_msg.edit_text(f"❌ Download failed:\n`{e}`")
            shutil.rmtree(tmpdir, ignore_errors=True)
            return

        if not os.path.exists(filepath):
            await info_msg.edit_text("❌ File not found after download.")
            shutil.rmtree(tmpdir, ignore_errors=True)
            return

        filename = os.path.basename(filepath)
        size_mb = os.path.getsize(filepath) / 1024 / 1024

        await info_msg.edit_text(f"⬆️ Uploading **{filename}** ({size_mb:.1f} MB)...")

        try:
            await client.send_video(
                chat_id=message.chat.id,
                video=filepath,
                caption=f"📘 Facebook video\n`{filename}`",
                supports_streaming=True,
                reply_to_message_id=message.id,
            )
            await info_msg.delete()
        except Exception as e:
            await info_msg.edit_text(f"❌ Upload failed:\n`{e}`")

        # cleanup
        shutil.rmtree(tmpdir, ignore_errors=True)
