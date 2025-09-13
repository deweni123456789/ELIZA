# modules/fb.py
import os
import uuid
import asyncio
import functools
from pathlib import Path
from typing import Optional

from pyrogram import filters
from pyrogram.types import Message
import yt_dlp

# adjust temporary folder as needed
TMP_DIR = Path("/tmp") if os.name != "nt" else Path.cwd() / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)

# Maximum file size to attempt sending directly (bytes).
MAX_SEND_SIZE = 1_800_000_000  # ~1.8GB

def _yt_opts(output_path: Path):
    return {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": str(output_path / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
        ],
        "retries": 3,
        "continuedl": True,
    }

async def _run_ydl_download(url: str, out_dir: Path):
    """Run yt_dlp download in a thread. Returns final filepath (Path)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(_sync_download, url, out_dir))

def _sync_download(url: str, out_dir: Path) -> Path:
    opts = _yt_opts(out_dir)
    ydl = yt_dlp.YoutubeDL(opts)
    ydl.download([url])
    files = sorted(out_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("No file produced by yt-dlp")
    return files[0]

def is_facebook_url(text: str) -> Optional[str]:
    if not text:
        return None
    lowers = text.lower()
    if "facebook.com" in lowers or "fb.watch" in lowers or "m.facebook.com" in lowers:
        for p in text.split():
            if "facebook.com" in p or "fb.watch" in p or "m.facebook.com" in p:
                return p.strip("<>.,;:!?'\"")
    return None

def register(app):
    """
    Call register(app) from your main.py to add the FB auto-downloader.
    """

    @app.on_message(filters.command("fb"))
    async def fb_cmd(_, message: Message):
        """Manual /fb <link> command"""
        if len(message.command) < 2:
            return await message.reply_text(
                "⚠️ Send `/fb <facebook url>` or just paste a Facebook link."
            )
        url = message.command[1]
        await _handle_download_flow(app, message, url)

    @app.on_message(filters.text)
    async def fb_auto_detector(_, message: Message):
        """Auto-detect Facebook links in any text message"""
        url = is_facebook_url(message.text or "")
        if not url:
            return
        await _handle_download_flow(app, message, url)

    async def _handle_download_flow(client, message: Message, url: str):
        status = await message.reply_text(
            f"🔎 Detected Facebook link:\n`{url}`\n\n⏳ Downloading..."
        )
        unique = uuid.uuid4().hex
        out_dir = TMP_DIR / f"fb_{unique}"
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            try:
                filepath = await _run_ydl_download(url, out_dir)
            except Exception as e:
                await status.edit(f"❌ Download failed: `{e}`")
                return

            size = filepath.stat().st_size
            caption = f"📥 Facebook Video\n`{filepath.name}`\nSize: {size/1024/1024:.2f} MB"

            if size <= MAX_SEND_SIZE:
                await status.edit("📤 Uploading to Telegram...")
                await client.send_video(
                    chat_id=message.chat.id,
                    video=str(filepath),
                    caption=caption,
                    supports_streaming=True,
                )
                await status.delete()
            else:
                await status.edit(
                    "⚠️ File too large to upload via bot (Telegram limit ~2GB)."
                )
        finally:
            try:
                for f in out_dir.glob("*"):
                    f.unlink(missing_ok=True)
                out_dir.rmdir()
            except Exception:
                pass

    return app
