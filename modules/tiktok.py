# modules/tiktok.py
from __future__ import annotations
import asyncio
import datetime as dt
import os
import re
import uuid
from typing import Dict, Tuple, Optional

from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from pyrogram.enums import ChatAction

from yt_dlp import YoutubeDL

# ---- Cache for callback tokens
_URL_CACHE: Dict[str, str] = {}

# ---- Regex to match TikTok links
TIKTOK_REGEX = re.compile(
    r"(https?://(?:www\.)?(?:vm\.|vt\.)?tiktok\.com/[^\s]+|https?://(?:(?:www\.)?tiktok\.com)/@[A-Za-z0-9._-]+/video/\d+)",
    re.IGNORECASE
)

DEV_USERNAME = "deweni2"  # <- developer username


# ---------------------- Helper functions ----------------------

def _format_date(ts: Optional[int]) -> str:
    if not ts:
        return "Unknown"
    return dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")

def _human(n: Optional[int]) -> str:
    if n is None:
        return "0"
    for unit in ["", "K", "M", "B", "T"]:
        if abs(n) < 1000:
            return f"{n:.0f}{unit}"
        n /= 1000.0
    return f"{n:.0f}T"

def _build_info_caption(info: dict, requester_mention: str) -> str:
    user = info.get("uploader") or info.get("creator") or info.get("uploader_id") or "Unknown"
    desc = (info.get("description") or info.get("title") or "").strip()
    if not desc:
        desc = "—"
    likes = _human(info.get("like_count"))
    comments = _human(info.get("comment_count"))
    shares = _human(info.get("repost_count") or info.get("share_count"))
    date_str = _format_date(info.get("timestamp"))

    lines = [
        f"🎬 <b>TikTok Video</b>",
        f"👤 <b>User:</b> {user}",
        f"📝 <b>Description:</b> {desc}",
        f"❤️ <b>Likes:</b> {likes}   💬 <b>Comments:</b> {comments}",
        f"🔁 <b>Shares:</b> {shares}   📅 <b>Uploaded:</b> {date_str}",
        "",
        f"👤 <i>Requested by</i> {requester_mention}",
    ]
    return "\n".join(lines)

def _choice_keyboard(token: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("✅ Download (No Watermark)", callback_data=f"tt|nowm|{token}")],
        [InlineKeyboardButton("💧 Download (With Watermark)", callback_data=f"tt|wm|{token}")],
        [InlineKeyboardButton("🎧 Download Audio (MP3)", callback_data=f"tt|aud|{token}")],
        [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEV_USERNAME}")]
    ]
    return InlineKeyboardMarkup(rows)

def _dev_only_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEV_USERNAME}")]]
    )

async def _ydl_extract(url: str) -> dict:
    def run():
        ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True}
        with YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    return await asyncio.to_thread(run)

async def _ydl_download_video(url: str, watermark: bool) -> Tuple[str, Optional[str]]:
    token = uuid.uuid4().hex[:8]
    outtmpl = os.path.join("temp", f"tt_{token}.%(ext)s")
    os.makedirs("temp", exist_ok=True)

    def run():
        ydl_opts = {
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "merge_output_format": "mp4",
            "format": "bv*+ba/b",
        }
        if watermark:
            ydl_opts["extractor_args"] = {"tiktok": {"download_addr": ["1"]}}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base, ext = os.path.splitext(filename)
            if ext.lower() not in [".mp4", ".mkv", ".mov", ".webm"]:
                candidate = base + ".mp4"
                if os.path.exists(candidate):
                    filename = candidate
            return filename, os.path.splitext(filename)[1].lstrip(".")
    return await asyncio.to_thread(run)

async def _ydl_download_audio(url: str) -> Tuple[str, Optional[str]]:
    token = uuid.uuid4().hex[:8]
    outtmpl = os.path.join("temp", f"tt_{token}.%(ext)s")
    os.makedirs("temp", exist_ok=True)

    def run():
        ydl_opts = {
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(filename)
            mp3 = base + ".mp3"
            return (mp3 if os.path.exists(mp3) else filename), "mp3"
    return await asyncio.to_thread(run)

def _first_tiktok_url(text: str) -> Optional[str]:
    m = TIKTOK_REGEX.search(text or "")
    return m.group(1) if m else None


# ---------------------- Public API ----------------------

def register(app: Client):
    @app.on_message(filters.text & (filters.private | filters.group))
    async def tiktok_catcher(_, message: Message):
        url = _first_tiktok_url(message.text or "")
        if not url:
            return

        try:
            info = await _ydl_extract(url)
        except Exception as e:
            await message.reply_text(
                f"❌ Failed to fetch TikTok info.\n<code>{e}</code>",
                quote=True,
                reply_markup=_dev_only_keyboard()
            )
            return

        token = uuid.uuid4().hex[:10]
        _URL_CACHE[token] = url

        caption = _build_info_caption(info, message.from_user.mention if message.from_user else "user")

        thumb = info.get("thumbnail")
        try:
            if thumb:
                await message.reply_photo(
                    photo=thumb,
                    caption=caption,
                    quote=True,
                    reply_markup=_choice_keyboard(token)
                )
            else:
                await message.reply_text(
                    caption,
                    quote=True,
                    reply_markup=_choice_keyboard(token),
                    disable_web_page_preview=True
                )
        except Exception:
            await message.reply_text(
                caption,
                quote=True,
                reply_markup=_choice_keyboard(token),
                disable_web_page_preview=True
            )


# ---------------------- Callback Handler ----------------------

async def handle_callbacks(app: Client, query: CallbackQuery):
    if not query.data or not query.data.startswith("tt|"):
        return

    parts = query.data.split("|", 2)
    if len(parts) != 3:
        await query.answer("Invalid request.", show_alert=True)
        return

    _tag, action, token = parts
    url = _URL_CACHE.get(token)
    if not url:
        await query.answer("Session expired. Send the TikTok link again.", show_alert=True)
        return

    try:
        await query.answer("Processing…")
    except Exception:
        pass

    await query.message.reply_chat_action(
        ChatAction.UPLOAD_VIDEO if action in ("wm", "nowm") else ChatAction.UPLOAD_AUDIO
    )

    try:
        if action == "aud":
            filepath, ext = await _ydl_download_audio(url)
            await query.message.reply_audio(
                audio=filepath,
                reply_markup=_dev_only_keyboard()
            )
        elif action in ("wm", "nowm"):
            want_wm = (action == "wm")
            filepath, ext = await _ydl_download_video(url, watermark=want_wm)
            await query.message.reply_video(
                video=filepath,
                reply_markup=_dev_only_keyboard(),
                supports_streaming=True
            )
        else:
            await query.answer("Unknown action.", show_alert=True)
            return

        # ✅ delete the service/info msg after sending file
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
        try:
            if 'filepath' in locals() and isinstance(filepath, str) and os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

        _URL_CACHE.pop(token, None)
