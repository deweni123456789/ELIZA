from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import requests, datetime, os, uuid

API_URL = "https://www.tikwm.com/api/"
VIDEO_CACHE = {}  # store URLs temporarily {uuid: {"wm": url, "nowm": url}}

def register(app: Client):
    @app.on_message(filters.command("tiktok"))
    async def tiktok_handler(_, message):
        if len(message.command) < 2:
            return await message.reply_text("❌ Please provide a TikTok link!\n\nUsage: `/tiktok <link>`")

        url = message.command[1]
        try:
            resp = requests.get(API_URL, params={"url": url}).json()
            if not resp.get("data"):
                return await message.reply_text("❌ Invalid TikTok link or download failed.")

            data = resp["data"]
            uid = str(uuid.uuid4())[:8]  # short random key

            VIDEO_CACHE[uid] = {
                "wm": data["wmplay"],
                "nowm": data["play"]
            }

            author = data["author"]["unique_id"]
            nickname = data["author"]["nickname"]
            likes = data.get("digg_count", 0)
            comments = data.get("comment_count", 0)
            views = data.get("play_count", 0)
            shares = data.get("share_count", 0)
            create_time = datetime.datetime.fromtimestamp(data["create_time"]).strftime("%Y-%m-%d %H:%M:%S")

            caption = (
                f"🎬 **TikTok Video**\n\n"
                f"👤 Uploader: `{nickname}` (@{author})\n"
                f"❤️ Likes: {likes}\n💬 Comments: {comments}\n👁 Views: {views}\n🔁 Shares: {shares}\n"
                f"📅 Uploaded: {create_time}\n"
            )

            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🎥 With Watermark", callback_data=f"tt_wm|{uid}"),
                        InlineKeyboardButton("🎥 Without Watermark", callback_data=f"tt_nowm|{uid}")
                    ],
                    [
                        InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2"),
                        InlineKeyboardButton("🎵 Support Group", url="https://t.me/slmusicmania")
                    ]
                ]
            )

            await message.reply_text(caption, reply_markup=buttons)

        except Exception as e:
            await message.reply_text(f"⚠️ Error: {str(e)}")

    @app.on_callback_query(filters.regex("^tt_"))
    async def callback_tiktok(_, query: CallbackQuery):
        try:
            action, uid = query.data.split("|")
            video_url = VIDEO_CACHE.get(uid, {}).get("wm" if action=="tt_wm" else "nowm")

            if not video_url:
                return await query.answer("❌ Expired or invalid link!", show_alert=True)

            file_data = requests.get(video_url).content
            filename = f"tiktok_{uid}.mp4"
            with open(filename, "wb") as f:
                f.write(file_data)

            await query.message.reply_video(
                video=filename,
                caption=f"✅ Here is your TikTok video ({'With Watermark' if action=='tt_wm' else 'No Watermark'})",
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2"),
                        InlineKeyboardButton("🎵 Support Group", url="https://t.me/slmusicmania")
                    ]]
                )
            )
            os.remove(filename)

        except Exception as e:
            await query.message.reply_text(f"⚠️ Failed: {str(e)}")

        finally:
            query.answer()
