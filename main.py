from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

app = Client(
    "downloader-bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# Import modules
from modules import song, video

@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text(
        "👋 Hello! I can download songs & videos from YouTube.\n\n"
        "🎵 Use `/song <name>` to download a song.\n"
        "🎥 Use `/video <name>` to download a video.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{config.DEVELOPER.replace('@','')}")]]
        )
    )

if __name__ == "__main__":
    app.run()
