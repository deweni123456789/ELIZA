# modules/instagram.py
import requests
from pyrogram import Client, filters

API_URL = "https://api.sssgram.com/ig"  # Instagram downloader API

def register(app: Client):

    @app.on_message(filters.command("ig"))
    async def instagram_download(client, message):
        if len(message.command) < 2:
            await message.reply_text("Send a valid Instagram post URL.\nUsage: /ig <link>")
            return

        url = message.command[1]
        msg = await message.reply_text("⏳ Downloading Instagram post...")

        try:
            # Call API
            r = requests.post(API_URL, json={"url": url})
            data = r.json()

            if "download" not in data or not data["download"]:
                await message.reply_text("❌ Could not fetch this post. Maybe private or unsupported.")
                return

            # Take first media link
            media_url = data["download"][0]["url"]

            # Caption (simple: description + requester + dev)
            caption = f"""
📄 Instagram Post
👤 Requested by: {message.from_user.mention}
👨‍💻 Developer: @deweni2
"""

            # Decide media type
            if media_url.endswith(".mp4"):
                await message.reply_video(media_url, caption=caption)
            else:
                await message.reply_photo(media_url, caption=caption)

        except Exception as e:
            await message.reply_text(f"❌ Failed to fetch Instagram post.\nError: {e}")

        finally:
            await msg.delete()
