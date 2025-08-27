import os
import requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

DEV_USERNAME = "deweni2"
_TEMP_DIR = "temp_ad_dl"
os.makedirs(_TEMP_DIR, exist_ok=True)

# Replace this with your API endpoint
API_ENDPOINT = "https://example-adult-api.com/download"

def register(app):

    @app.on_message(filters.command("adult"))
    async def adult_download(_, message: Message):
        if len(message.command) < 2:
            return await message.reply_text("❌ Please provide a link.\nUsage: `/adult <link>`")

        url = message.command[1]
        requester = message.from_user.mention

        status_msg = await message.reply_text("⏳ Fetching video... Please wait!")

        try:
            # Call API
            resp = requests.get(API_ENDPOINT, params={"url": url})
            if resp.status_code != 200:
                return await status_msg.edit("❌ Failed to fetch video from API.")

            data = resp.json()
            video_url = data.get("video_url")
            title = data.get("title", "Video")
            uploader = data.get("uploader", "Unknown")
            views = data.get("views", "N/A")
            likes = data.get("likes", "N/A")
            comments = data.get("comments", "N/A")

            if not video_url:
                return await status_msg.edit("❌ Video URL not found in API response.")

            # Download video to temp dir
            file_path = os.path.join(_TEMP_DIR, f"{title}.mp4")
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                with open(file_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            caption = (
                f"🎬 Title: {title}\n"
                f"👤 Uploader: {uploader}\n"
                f"👁 Views: {views}\n"
                f"👍 Likes: {likes}\n"
                f"💬 Comments: {comments}\n"
                f"👤 Requested by: {requester}"
            )

            await message.reply_video(
                video=file_path,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEV_USERNAME}")]]
                )
            )
            await status_msg.delete()

        except Exception as e:
            await status_msg.edit(f"❌ Failed to download video.\nError: {e}")
        finally:
            if "file_path" in locals() and os.path.exists(file_path):
                os.remove(file_path)
