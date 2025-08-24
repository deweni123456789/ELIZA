import os
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def register_tiktok(app: Client):
    # User guide for first time users
    @app.on_message(filters.command("tiktok"))
    async def tiktok_downloader(client, message):
        if len(message.command) < 2:
            await message.reply_text(
                "👋 Welcome to TikTok Downloader!\n\n"
                "👉 To use me, just send:\n"
                "`/tiktok <link>`",
                quote=True
            )
            return

        url = message.command[1]
        m = await message.reply_text("⬇️ Processing TikTok video...")

        try:
            # ---- Replace these with your TikTok scraper/api results ----
            video_url_no_wm = "https://example.com/video_no_wm.mp4"
            video_url_wm = "https://example.com/video_wm.mp4"
            uploader = "Demo Uploader"
            uploaded_date = "2025-08-23"
            likes = "12.5K"
            comments = "650"
            views = "145K"
            # ------------------------------------------------------------

            # Download temp file (no wm version as default upload)
            filename = "tiktok_temp.mp4"
            r = requests.get(video_url_no_wm, stream=True)
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

            # Send uploaded video
            await message.reply_video(
                video=filename,
                caption=(
                    f"🎬 TikTok Video\n\n"
                    f"👤 Uploader: {uploader}\n"
                    f"📅 Uploaded: {uploaded_date}\n"
                    f"❤️ Likes: {likes}\n"
                    f"💬 Comments: {comments}\n"
                    f"👁️ Views: {views}"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("▶️ Without Watermark", url=video_url_no_wm),
                        InlineKeyboardButton("▶️ With Watermark", url=video_url_wm)
                    ],
                    [
                        InlineKeyboardButton("💻 Developer", url="https://t.me/deweni2"),
                        InlineKeyboardButton("👥 Support Group", url="https://t.me/slmusicmania")
                    ]
                ])
            )

            await m.delete()
            os.remove(filename)

        except Exception as e:
            await m.edit(f"⚠️ Error: {e}")
