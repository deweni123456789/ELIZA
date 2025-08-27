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

# ---- You need yt-dlp
# requirements.txt -> yt-dlp>=2024.07.07
from yt_dlp import YoutubeDL

# ---- Simple in-memory cache (token -> url)
_URL_CACHE: Dict[str, str] = {}

# ---- Regex to catch TikTok links (includes short links)
TIKTOK_REGEX = re.compile(
    r"(https?://(?:www\.)?(?:vm\.|vt\.)?tiktok\.com/[^\s]+|https?://(?:(?:www\.)?tiktok\.com)/@[A-Za-z0-9._-]+/video/\d+)",
    re.IGNORECASE
)

DEV_USERNAME = "deweni2"  # <- change if needed


# ---------------------- Helper functions ----------------------

def _format_date(ts: Optional[int]) -> str:
    if not ts:
        return "Unknown"
    # Convert unix timestamp to yyyy-mm-dd
    return dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")

def _human(n: Optional[int]) -> str:
    if n is None:
        return "0"
    # compact number (e.g., 1.2K, 3.4M)
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
    # callback_data must be short; we keep a token->url map
    rows = [
        [
            InlineKeyboardButton("✅ Download (No Watermark)", callback_data=f"tt|nowm|{token}"),
        ],
        [
            InlineKeyboardButton("💧 Download (With Watermark)", callback_data=f"tt|wm|{token}"),
        ],
        [
            InlineKeyboardButton("🎧 Download Audio (MP3)", callback_data=f"tt|aud|{token}"),
        ],
        [
            InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEV_USERNAME}")
        ]
    ]
    return InlineKeyboardMarkup(rows)

def _dev_only_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEV_USERNAME}")]]
    )

async def _ydl_extract(url: str) -> dict:
    def run():
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    return await asyncio.to_thread(run)

async def _ydl_download_video(url: str, watermark: bool) -> Tuple[str, Optional[str]]:
    """
    Returns: (filepath, ext) for the video file.
    We try to toggle watermark via extractor_args. If unsupported, yt-dlp still gets the best video.
    """
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
            "format": "bv*+ba/b",  # best video+audio or best
        }
        # Attempt to prefer watermarked URL (download_addr) when requested.
        # If yt-dlp ignores this, you still get a valid file.
        if watermark:
            ydl_opts["extractor_args"] = {"tiktok": {"download_addr": ["1"]}}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # ensure final extension is mp4 if merged
            base, ext = os.path.splitext(filename)
            if ext.lower() not in [".mp4", ".mkv", ".mov", ".webm"]:
                # Try to locate best candidate with mp4
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
            # After postprocess, extension becomes .mp3
            base, _ = os.path.splitext(filename)
            mp3 = base + ".mp3"
            return (mp3 if os.path.exists(mp3) else filename), "mp3"
    return await asyncio.to_thread(run)

def _first_tiktok_url(text: str) -> Optional[str]:
    m = TIKTOK_REGEX.search(text or "")
    return m.group(1) if m else None


# ---------------------- Public API ----------------------

def register(app: Client):
    """
    Call this in main.py to register the TikTok handlers.
    """

    @app.on_message(filters.text & (filters.private | filters.group))
    async def tiktok_catcher(_, message: Message):
        url = _first_tiktok_url(message.text or "")
        if not url:
            return  # ignore non-tiktok messages

        # Extract info (no download yet)
        try:
            info = await _ydl_extract(url)
        except Exception as e:
            await message.reply_text(
                f"❌ Failed to fetch TikTok info.\n<code>{e}</code>",
                quote=True,
                reply_markup=_dev_only_keyboard()
            )
            return

        # Save token -> url for callbacks
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
            # Fallback without thumb if remote thumb fails
            await message.reply_text(
                caption,
                quote=True,
                reply_markup=_choice_keyboard(token),
                disable_web_page_preview=True
            )

# Exported so main.py can delegate callback queries here
async def handle_callbacks(app: Client, query: CallbackQuery):
    """
    Main callback dispatcher for tiktok buttons.
    In main.py's on_callback_query, call: await handle_callbacks(app, query)
    """
    if not query.data or not query.data.startswith("tt|"):
        return  # not ours

    parts = query.data.split("|", 2)  # tt|action|token
    if len(parts) != 3:
        await query.answer("Invalid request.", show_alert=True)
        return

    _tag, action, token = parts
    url = _URL_CACHE.get(token)
    if not url:
        await query.answer("Session expired. Send the TikTok link again.", show_alert=True)
        return

    # Acknowledge quickly
    try:
        await query.answer("Processing…")
    except Exception:
        pass

    await query.message.reply_chat_action("upload_video" if action in ("wm", "nowm") else "upload_audio")

    try:
        if action == "aud":
            filepath, ext = await _ydl_download_audio(url)
            caption = f"🎧 TikTok Audio\n\nRequested by {query.from_user.mention if query.from_user else 'user'}"
            await query.message.reply_audio(
                audio=filepath,
                caption=caption,
                reply_markup=_dev_only_keyboard()
            )
        elif action in ("wm", "nowm"):
            want_wm = (action == "wm")
            filepath, ext = await _ydl_download_video(url, watermark=want_wm)
            caption = f"🎬 TikTok Video ({'With' if want_wm else 'No'} Watermark)\n\nRequested by {query.from_user.mention if query.from_user else 'user'}"
            await query.message.reply_video(
                video=filepath,
                caption=caption,
                reply_markup=_dev_only_keyboard(),
                supports_streaming=True
            )
        else:
            await query.answer("Unknown action.", show_alert=True)
            return
    except Exception as e:
        await query.message.reply_text(
            f"❌ Download failed.\n<code>{e}</code>",
            reply_markup=_dev_only_keyboard()
        )
    finally:
        # Cleanup file and forget token if possible
        try:
            if 'filepath' in locals() and isinstance(filepath, str) and os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

        # clear token to avoid growth
        _URL_CACHE.pop(token, None)
