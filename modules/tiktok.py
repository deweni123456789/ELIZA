from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaVideo
import requests
import datetime

# TikTok API (free unofficial endpoint)
API_URL = "https://www.tikwm.com/api/"

def register(app: Client):
    # --- /tiktok <url>
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
            video_id = data.get("id")
            wm_url = data.get("wmplay")   # With Watermark
            no_wm_url = data.get("play")  # Without Watermark
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

            # Send choice buttons
            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🎥 With Watermark", callback_data=f"tt_wm|{wm_url}|{video_id}"),
                        InlineKeyboardButton("🎥 Without Watermark", callback_data=f"tt_nowm|{no_wm_url}|{video_id}")
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

    # --- Handle Inline Button Click
    @app.on_callback_query(filters.regex("^tt_"))
    async def callback_tiktok(_, query: CallbackQuery):
        action, video_url, vid_id = query.data.split("|")

        try:
            # Download video bytes
            file = requests.get(video_url).content
            filename = f"tiktok_{vid_id}.mp4"

            with open(filename, "wb") as f:
                f.write(file)

            await query.message.reply_video(
                video=filename,
                caption=f"✅ Here is your TikTok video ({'With WM' if action=='tt_wm' else 'No WM'})",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2"),
                            InlineKeyboardButton("🎵 Support Group", url="https://t.me/slmusicmania")
                        ]
                    ]
                )
            )

        except Exception as e:
            await query.message.reply_text(f"⚠️ Failed to fetch video.\n{str(e)}")

        finally:
            query.answer()  # Close "loading..." state
