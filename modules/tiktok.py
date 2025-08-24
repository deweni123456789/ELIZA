from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import requests, datetime, os, uuid, asyncio

API_URL = "https://www.tikwm.com/api/"
VIDEO_CACHE = {}  # temp store {uid: {"wm": url, "nowm": url}}

def register(app: Client):

    # --- /tiktok command
    @app.on_message(filters.command("tiktok"))
    async def tiktok_handler(_, message):
        # if no link provided -> show guide (auto delete)
        if len(message.command) < 2:
            guide = await message.reply_text(
                "👋 Hi! To use TikTok downloader:\n\n"
                "👉 Send like this:\n"
                "`/tiktok <TikTok-Video-Link>`\n\n"
                "📌 Example:\n"
                "`/tiktok https://www.tiktok.com/@username/video/1234567890`",
                disable_web_page_preview=True
            )
            # auto delete after 20s
            await asyncio.sleep(20)
            await guide.delete()
            return

        url = message.command[1]

        try:
            resp = requests.get(API_URL, params={"url": url}).json()
            if not resp.get("data"):
                return await message.reply_text("❌ Invalid TikTok link or download failed.")

            data = resp["data"]
            uid = str(uuid.uuid4())[:8]

            # cache urls
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
                f"📅 Uploaded: {create_time}\n\n"
                f"👇 Select download option:"
            )

            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🎥 With Watermark", callback_data=f"tt_wm|{uid}"),
                        InlineKeyboardButton("🎥 Without Watermark", callback_data=f"tt_nowm|{uid}")
                    ]
                ]
            )

            await message.reply_text(caption, reply_markup=buttons)

        except Exception as e:
            await message.reply_text(f"⚠️ Error: {str(e)}")

    # --- Button click handler
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
                caption=f"✅ Here is your TikTok video ({'With Watermark' if action=='tt_wm' else 'Without Watermark'})",
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
