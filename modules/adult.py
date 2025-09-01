# modules/adult.py
import os
import asyncio
import datetime as dt
from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from pyrogram.enums import ChatAction
from yt_dlp import YoutubeDL

# ---- Cache for callback tokens
_URL_CACHE = {}

def _get_token(url: str) -> str:
    """Generate short token for callbacks"""
    return str(abs(hash(url)))[:10]

# ---- yt-dlp extract function
async def extract_media(url: str, format_id: str = "best") -> str:
    loop = asyncio.get_event_loop()
    def run():
        ydl_opts = {"format": format_id}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    return await loop.run_in_executor(None, run)

# ---- Main handler
def register(app: Client):
    @app.on_message(filters.command("adult") & filters.private)
    async def adult_handler(_, message: Message):
        if len(message.command) < 2:
            return await message.reply("❌ Please provide a link.\n\nUsage: `/adult <url>`", quote=True)

        url = message.command[1]
        token = _get_token(url)
        _URL_CACHE[token] = url

        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎥 Download Video", callback_data=f"adult_video:{token}"),
                InlineKeyboardButton("🎵 Download Audio", callback_data=f"adult_audio:{token}")
            ]
        ])

        await message.reply(
            f"🔗 URL received:\n`{url}`\n\nChoose format:",
            reply_markup=buttons,
            quote=True
        )

    # ---- Callback handling
    @app.on_callback_query(filters.regex(r"^adult_(video|audio):"))
    async def adult_callback(_, query: CallbackQuery):
        action, token = query.data.split(":")
        url = _URL_CACHE.get(token)

        if not url:
            return await query.answer("❌ Link expired. Send /adult <url> again.", show_alert=True)

        await query.answer("⏳ Processing... Please wait.")
        await query.message.edit_text("📥 Downloading...")

        try:
            fmt = "bestaudio" if action == "adult_audio" else "best"
            info = await extract_media(url, format_id=fmt)

            title = info.get("title", "Unknown Title")
            duration = info.get("duration", 0)
            uploader = info.get("uploader", "Unknown")
            upload_date = info.get("upload_date", "")
            if upload_date:
                upload_date = dt.datetime.strptime(upload_date, "%Y%m%d").strftime("%Y/%m/%d")

            file_url = info["url"]
            caption = (
                f"**Title:** {title}\n"
                f"**Uploader:** {uploader}\n"
                f"**Duration:** {duration}s\n"
                f"**Upload Date:** {upload_date}\n"
            )

            await query.message.delete()
            await _.send_chat_action(query.message.chat.id, ChatAction.UPLOAD_VIDEO)
            await _.send_video(
                chat_id=query.message.chat.id,
                video=file_url,
                caption=caption
            )
        except Exception as e:
            await query.message.edit_text(f"❌ Error: `{e}`")

# Expose for main.py
def handle_callbacks(app: Client):
    pass  # already handled inside register
