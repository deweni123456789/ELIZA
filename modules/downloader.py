# modules/downloader.py
from __future__ import annotations
import os
import asyncio
import secrets
from typing import Dict, Optional, Tuple

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.enums import ChatAction

import yt_dlp

# ---------- Config ----------
DEV_USERNAME = "deweni2"   # change to your t.me username without @
_TEMP_DIR = "temp_ad_dl"
os.makedirs(_TEMP_DIR, exist_ok=True)

# token -> url cache (in-memory)
_URL_CACHE: Dict[str, str] = {}

# ---------- Helpers ----------

def _dev_only_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEV_USERNAME}")]]
    )

# download video using yt-dlp in a thread
async def _ydl_download_video(url: str) -> Tuple[str, Optional[dict]]:
    loop = asyncio.get_running_loop()
    token = secrets.token_hex(6)
    outtmpl = os.path.join(_TEMP_DIR, f"{token}.%(ext)s")

    def run():
        opts = {
            "format": "bv*+ba/best",
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            # add cookies or extractor args if needed
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            # if merged output becomes mp4, ensure filepath exists
            base, ext = os.path.splitext(filepath)
            if not os.path.exists(filepath):
                cand = base + ".mp4"
                if os.path.exists(cand):
                    filepath = cand
            return filepath, info

    return await loop.run_in_executor(None, run)

# ---------- Handlers ----------

async def handle_downloader(client: Client, message: Message, url: str):
    """
    Called when a private message containing a supported adult-site URL is received.
    Sends buttons (Download Video + Developer).
    """
    token = secrets.token_hex(6)
    _URL_CACHE[token] = url

    buttons = [
        [InlineKeyboardButton("⬇️ Download Video", callback_data=f"dl|vid|{token}")],
        [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEV_USERNAME}")]
    ]

    await message.reply_text(
        "🔞 Adult video detected.\n\nChoose an option to download:",
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )

async def handle_callbacks(app: Client, query: CallbackQuery):
    """
    Callback dispatcher for this module.
    Only processes callbacks with prefix 'dl|'.
    """
    if not query.data or not query.data.startswith("dl|"):
        return

    parts = query.data.split("|", 2)
    if len(parts) != 3:
        await query.answer("Invalid request.", show_alert=True)
        return

    _tag, action, token = parts
    url = _URL_CACHE.get(token)
    if not url:
        await query.answer("Session expired. Send the link again.", show_alert=True)
        return

    try:
        await query.answer("Processing…")
    except Exception:
        pass

    # show typing/upload action
    try:
        await query.message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
    except Exception:
        pass

    filepath = None
    try:
        if action == "vid":
            filepath, info = await _ydl_download_video(url)
            # send as video (no caption)
            await query.message.reply_video(
                video=filepath,
                reply_markup=_dev_only_keyboard(),
                supports_streaming=True
            )
        else:
            await query.answer("Unknown action.", show_alert=True)
            return

        # delete the service/info message to keep chat clean (silent fail if not allowed)
        try:
            await query.message.delete()
        except Exception:
            pass

    except Exception as e:
        await query.message.reply_text(
            f"❌ Download failed.\n<code>{e}</code>",
            reply_markup=_dev_only_keyboard()
        )
    finally:
        # cleanup downloaded file
        try:
            if filepath and isinstance(filepath, str) and os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass
        _URL_CACHE.pop(token, None)

# ---------- Register function (private only) ----------

def register(app: Client):
    """
    Call register(app) from main.py to enable this module.
    This handler ONLY listens to private chats.
    """

    # detect adult-site URLs in private chats only
    @app.on_message(filters.private & filters.regex(r"(pornhub\.com|xvideos\.com|xnxx\.com|xhamster\.com)"))
    async def _private_downloader_handler(client: Client, message: Message):
        # extract first URL-like substring (simple approach: use the full message text)
        text = (message.text or "") + " " + " ".join([m.url for m in (message.entities or []) if getattr(m, 'url', None)])
        url = (message.text or "").strip()
        # For robustness, simply pass the full message text as URL if it contains domain
        await handle_downloader(client, message, url)

    # callback handler (registered here) — only processes our callback prefix
    @app.on_callback_query()
    async def _callback_router(client: Client, query: CallbackQuery):
        await handle_callbacks(client, query)
