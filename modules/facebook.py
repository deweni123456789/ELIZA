# modules/facebook.py
import os
import asyncio
import shutil
import tempfile
from typing import Optional

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatAction

import yt_dlp

# --- Configuration
TEMP_DIR_ROOT = "temp_fb"  # will be created if missing
os.makedirs(TEMP_DIR_ROOT, exist_ok=True)


def _run_ydl_in_executor(ydl_opts, url: str, loop: Optional[asyncio.AbstractEventLoop] = None):
    """
    Run yt_dlp download in a thread pool (blocking library).
    Returns the path of the downloaded file (str).
    """
    loop = loop or asyncio.get_event_loop()

    def _download():
        # Ensure per-download temp dir so filename collisions don't happen
        tmpdir = tempfile.mkdtemp(prefix="fb_dl_", dir=TEMP_DIR_ROOT)
        # Force output into tmpdir
        ydl_opts_local = dict(ydl_opts)
        ydl_opts_local["outtmpl"] = os.path.join(tmpdir, "%(title)s.%(ext)s")
        # allow merging into mp4 if needed
        ydl_opts_local.setdefault("merge_output_format", "mp4")

        with yt_dlp.YoutubeDL(ydl_opts_local) as ydl:
            info = ydl.extract_info(url, download=True)
            # When yt-dlp finishes, get the filename returned by prepare_filename
            filename = ydl.prepare_filename(info)
            # If merged format changed extension, adjust
            if ydl_opts_local.get("merge_output_format"):
                base, _ = os.path.splitext(filename)
                filename = base + "." + ydl_opts_local["merge_output_format"]
            return tmpdir, filename

    return loop.run_in_executor(None, _download)


def register(app):
    """
    Call this from your main.py: register(app)
    Provides /fb and /facebook commands. Usage:
      /fb <facebook_url>
    or reply to a message containing a Facebook URL with /fb
    """

    @app.on_message(filters.command(["fb", "facebook"]))
    async def fb_download_handler(client: "Client", message: Message):
        # Accept URL as arg or from replied message
        url = None
        if len(message.command) >= 2:
            url = message.command[1].strip()
        elif message.reply_to_message and message.reply_to_message.text:
            # try to find a URL in replied text
            tokens = message.reply_to_message.text.split()
            for t in tokens:
                if "facebook.com" in t or "fb.watch" in t:
                    url = t
                    break

        if not url:
            await message.reply_text(
                "❗️ Send a Facebook video link like:\n\n"
                "`/fb https://www.facebook.com/...` \n\n"
                "Or reply to a message containing the Facebook link with `/fb`.",
                parse_mode="markdown"
            )
            return

        info_msg = await message.reply_text("🔎 Checking link and preparing download...")
        # Let users know bot is working
        try:
            await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)
        except Exception:
            # chat action is optional; ignore if it fails
            pass

        # yt-dlp options
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            # retries
            "retries": 3,
            # don't print progress to stdout (we run in executor)
            "logger": yt_dlp.utils.get_default_logger(),
            # You may add cookiefile option here if users need to provide cookies for private videos.
        }

        try:
            # download in executor
            tmpdir, filepath = await _run_ydl_in_executor(ydl_opts, url)
        except yt_dlp.utils.DownloadError as e:
            await info_msg.edit_text(f"❌ Failed to download. yt-dlp error:\n`{e}`", parse_mode="markdown")
            return
        except Exception as e:
            await info_msg.edit_text(f"❌ Unexpected error while downloading:\n`{e}`", parse_mode="markdown")
            return

        # Ensure file exists
        if not os.path.exists(filepath):
            # try to find any file inside tmpdir
            files = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir)]
            files = [f for f in files if os.path.isfile(f)]
            if files:
                filepath = files[0]
            else:
                await info_msg.edit_text("❌ Download finished but no file was found.")
                # cleanup
                try:
                    shutil.rmtree(tmpdir, ignore_errors=True)
                except Exception:
                    pass
                return

        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)

        # If file is huge, warn user
        MAX_TELEGRAM_SIZE = 2_000_000_000  # ~2GB; adjust if you know bot's limit
        if filesize >= MAX_TELEGRAM_SIZE:
            await info_msg.edit_text(
                f"⚠️ Downloaded file **{filename}** is {(filesize/1024/1024):.1f} MB which may exceed Telegram's upload limit.\n\n"
                "Try a lower quality or provide cookies if this is a private video.",
                parse_mode="markdown"
            )
            # still attempt to send, but user is warned

        # Send a small update
        await info_msg.edit_text(f"⬆️ Uploading **{filename}** ({filesize/1024/1024:.1f} MB)...", parse_mode="markdown")

        try:
            # Try to send as .mp4 video first (Telegram will auto-detect)
            # Use send_video if it is a video file; fallback to send_document
            try:
                await client.send_video(
                    chat_id=message.chat.id,
                    video=filepath,
                    caption=f"Downloaded from Facebook: {filename}",
                    supports_streaming=True,
                    reply_to_message_id=message.message_id
                )
            except Exception as e_video:
                # fallback to document (some formats or size issues)
                await client.send_document(
                    chat_id=message.chat.id,
                    document=filepath,
                    caption=f"Downloaded from Facebook: {filename}",
                    reply_to_message_id=message.message_id
                )
        except Exception as e:
            await info_msg.edit_text(f"❌ Failed to upload file: `{e}`", parse_mode="markdown")
            try:
                shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception:
                pass
            return

        # Success - replace info message with success
        try:
            await info_msg.edit_text("✅ Done. Video uploaded.")
        except Exception:
            pass

        # Cleanup temp files
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass

    # Optionally provide a help button in start or info commands by returning the register function only.
    return
