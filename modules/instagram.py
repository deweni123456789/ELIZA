# modules/instagram.py
import requests
from pyrogram import Client, filters

API_URL = "https://api.saveig.app/api/v1"

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
            r = requests.get(API_URL, params={"url": url})
            data = r.json()

            if "data" not in data or not data["data"]:
                await message.reply_text("❌ Could not fetch this Instagram post. Maybe private?")
                return

            # First media URL
            media_url = data["data"][0]["url"]

            caption = f"""
📄 Instagram Post
👤 Requested by: {message.from_user.mention}
👨‍💻 Developer: @deweni2
"""

            # Send
            if media_url.endswith(".mp4"):
                await message.reply_video(media_url, caption=caption)
            else:
                await message.reply_photo(media_url, caption=caption)

        except Exception as e:
            await message.reply_text(f"❌ Failed to fetch Instagram post.\nError: {e}")

        finally:
            await msg.delete()
