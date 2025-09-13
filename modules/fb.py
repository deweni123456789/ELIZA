# modules/fb.py
import os
import uuid
import asyncio
import functools
from pathlib import Path
from typing import Optional

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# adjust temporary folder as needed
TMP_DIR = Path("/tmp") if os.name != "nt" else Path.cwd() / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)

# Maximum file size to attempt sending directly (bytes).
# Telegram Bot API supports up to 2GB, but hosting may limit. Default to 1.8GB.
MAX_SEND_SIZE = 1_800_000_000

def _yt_opts(output_path: Path):
    return {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": str(output_path / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # use ffmpeg to merge audio+video when needed
        "postprocessors": [
            {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
        ],
        # retry options
        "retries": 3,
        "continuedl": True,
        # cookie and headers can be added if needed
    }

async def _run_ydl_download(url: str, out_dir: Path):
    """Run yt_dlp download in a thread (blocking call). Returns final filepath (Path)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(_sync_download, url, out_dir))

def _sync_download(url: str, out_dir: Path) -> Path:
    opts = _yt_opts(out_dir)
    ydl = yt_dlp.YoutubeDL(opts)
    info = ydl.extract_info(url, download=False)
    # derive filename yt_dlp will write
    # call download (blocking)
    ydl.download([url])
    # find the produced file in out_dir (the most recent file)
    files = sorted(out_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("No file produced by yt-dlp")
    return files[0]

def is_facebook_url(text: str) -> Optional[str]:
    if not text:
        return None
    text = text.strip()
    # common Facebook link patterns: facebook.com, fb.watch, m.facebook.com, video.php?v=
    lowers = text.lower()
    if "facebook.com" in lowers or "fb.watch" in lowers or "m.facebook.com" in lowers:
        # try to isolate url if message contains other text
        parts = text.split()
        for p in parts:
            if "facebook.com" in p or "fb.watch" in p or "m.facebook.com" in p:
                # strip punctuation
                return p.strip("<>.,;:!?'\"")
    return None

def register(app):
    """
    Call register(app) from your main.py to add the FB auto-downloader routes.
    """

    @app.on_message(filters.command("fb") & filters.private | filters.group & filters.command("fb"))
    async def fb_cmd(_, message: Message):
        """Manual /fb <link> command handler"""
        if len(message.command) < 2:
            return await message.reply_text("Send `/fb <facebook url>` or just paste a Facebook link and I'll auto-detect and download it.")
        url = message.command[1]
        await _handle_download_flow(app, message, url)

    @app.on_message(filters.text & ~filters.edited)
    async def fb_auto_detector(_, message: Message):
        """Auto-detect facebook links posted in chat and download them (only when a plain URL present)."""
        url = is_facebook_url(message.text or "")
        if not url:
            return
        # Optionally, ignore other bot/channel messages or only respond in private/groups as desired
        # To avoid spam, only react when message contains only the link or starts with link:
        # We'll proceed regardless but you can add more checks.
        await _handle_download_flow(app, message, url)

    async def _handle_download_flow(client, message: Message, url: str):
        status = await message.reply_text(f"🔎 Detected Facebook link:\n`{url}`\n\nStarting download... (this may take a bit)")
        unique = uuid.uuid4().hex
        out_dir = TMP_DIR / f"fb_{unique}"
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Run yt-dlp
            try:
                filepath = await _run_ydl_download(url, out_dir)
            except Exception as e:
                await status.edit(f"❌ Download failed: `{e}`")
                return

            size = filepath.stat().st_size
            # If file too large, notify user with link (if you have hosting) or send as document in chunks.
            caption = f"Downloaded from Facebook — `{filepath.name}`\nSize: {size/1024/1024:.2f} MB"

            # Send as video if small enough, else as document
            if size <= MAX_SEND_SIZE:
                # send as video so Telegram plays it inline
                await status.edit("📤 Uploading to Telegram...")
                await client.send_video(
                    chat_id=message.chat.id,
                    video=str(filepath),
                    caption=caption,
                    supports_streaming=True,
                )
                await status.delete()
            else:
                await status.edit("⚠️ File too large to upload via bot. File saved on server (remove it manually).")
        finally:
            # cleanup - remove out_dir and files
            try:
                for f in out_dir.glob("*"):
                    f.unlink(missing_ok=True)
                out_dir.rmdir()
            except Exception:
                pass

    # return app for chaining if desired
    return app
