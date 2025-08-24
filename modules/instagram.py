# modules/instagram.py
import requests
from pyrogram import Client, filters
from bs4 import BeautifulSoup

API_URL = "https://snapinsta.app/action.php?lang=en"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

def register(app: Client):

    @app.on_message(filters.command("ig"))
    async def instagram_download(client, message):
        if len(message.command) < 2:
            await message.reply_text("Send a valid Instagram post URL.\nUsage: /ig <link>")
            return

        url = message.command[1]
        msg = await message.reply_text("⏳ Downloading Instagram post...")

        try:
            # Call SnapInsta
            resp = requests.post(API_URL, headers=HEADERS, data={"url": url})
            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract first download link
            link_tag = soup.find("a", {"target": "_blank"})
            if not link_tag:
                await message.reply_text("❌ Could not fetch this Instagram post. Maybe private?")
                return

            media_url = link_tag["href"]

            caption = f"""
📄 Instagram Post
👤 Requested by: {message.from_user.mention}
👨‍💻 Developer: @deweni2
"""

            if media_url.endswith(".mp4"):
                await message.reply_video(media_url, caption=caption)
            else:
                await message.reply_photo(media_url, caption=caption)

        except Exception as e:
            await message.reply_text(f"❌ Failed to fetch Instagram post.\nError: {e}")

        finally:
            await msg.delete()
