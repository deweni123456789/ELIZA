# modules/fb.py
import os
import uuid
import asyncio
import functools
from pathlib import Path
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
import yt_dlp
import logging

logging.basicConfig(level=logging.INFO)

# ----------------------------
# Temporary folder
# ----------------------------
TMP_DIR = Path("/tmp") if os.name != "nt" else Path.cwd() / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)

MAX_SEND_SIZE = 1_800_000_000  # ~1.8GB

# ----------------------------
# YT-DLP download helper
# ----------------------------
def _yt_opts(output_path: Path):
    return {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": str(output_path / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
        "retries": 3,
        "continuedl": True,
    }

async def _run_ydl_download(url: str, out_dir: Path):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(_sync_download, url, out_dir))

def _sync_download(url: str, out_dir: Path) -> Path:
    opts = _yt_opts(out_dir)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception as e:
        logging.error(f"YT-DLP download failed: {e}")
        raise
    files = sorted(out_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("No file produced by yt-dlp")
    return files[0]

# ----------------------------
# FB URL detection
# ----------------------------
def is_facebook_url(text: str) -> Optional[str]:
    if not text:
        return None
    text_lower = text.lower()
    for word in text.split():
        if "facebook.com" in word or "fb.watch" in word or "m.facebook.com" in word:
            return word.strip("<>.,;:!?'\"")
    return None

# ----------------------------
# Core download logic
# ----------------------------
async def _handle_download_flow(client: Client, message: Message, url: str):
    try:
        status = await message.reply_text(f"🔎 Detected Facebook link:\n`{url}`\n⏳ Downloading...")
    except Exception:
        return

    unique = uuid.uuid4().hex
    out_dir = TMP_DIR / f"fb_{unique}"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        try:
            filepath = await _run_ydl_download(url, out_dir)
        except Exception as e:
            logging.exception("FB download error")
            return await status.edit(f"❌ Download failed: `{e}`")

        size = filepath.stat().st_size
        caption = f"📥 Facebook Video\n`{filepath.name}`\nSize: {size/1024/1024:.2f} MB"

        if size <= MAX_SEND_SIZE:
            try:
                await status.edit("📤 Uploading to Telegram...")
                await client.send_video(
                    chat_id=message.chat.id,
                    video=str(filepath),
                    caption=caption,
                    supports_streaming=True
                )
                await status.delete()
            except Exception as e:
                logging.error(f"Upload failed: {e}")
                await status.edit(f"❌ Upload failed: {e}")
        else:
            await status.edit("⚠️ File too large (Telegram limit ~2GB).")

    finally:
        # Cleanup temp files
        for f in out_dir.glob("*"):
            try: f.unlink()
            except: pass
        try: out_dir.rmdir()
        except: pass

# ----------------------------
# Register FB module
# ----------------------------
def register(app: Client):
    # /fb command
    @app.on_message(filters.command("fb") & (filters.private | filters.group))
    async def fb_cmd(_, message: Message):
        if len(message.command) < 2:
            return await message.reply_text("⚠️ Usage: `/fb <facebook url>`")
        url = message.command[1]
        await _handle_download_flow(_, message, url)

    # Auto detect FB links
    @app.on_message(filters.text & (filters.private | filters.group))
    async def fb_auto_detector(_, message: Message):
        url = is_facebook_url(message.text)
        if not url:
            return
        await _handle_download_flow(_, message, url)

    return app
