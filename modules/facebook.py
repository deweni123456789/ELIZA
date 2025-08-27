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
    @app.on_message(filters.command("fb", prefixes=["/"]))
    async def fb_handler(client, message: Message):
        # --- Get URL
        if len(message.command) > 1:
            url = message.text.split(maxsplit=1)[1]
        elif message.reply_to_message and message.reply_to_message.text:
            txt = message.reply_to_message.text
            if "facebook.com" in txt or "fb.watch" in txt:
                url = txt.strip()
            else:
                url = None
        else:
            url = None

        if not url:
            await message.reply_text(
                "⚠️ Please send a Facebook video link.\n\nUsage:\n`/fb <link>`",
                quote=True
            )
            return

        # --- Status message
        status = await message.reply_text("🔎 Downloading Facebook video...", quote=True)
        await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)

        # --- Temp dir + yt-dlp
        tmpdir = tempfile.mkdtemp(prefix="fb_", dir=TEMP_DIR)
        outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")
        ydl_opts = {
            "outtmpl
