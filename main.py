from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
from modules.tiktok import register as register_tiktok

app = Client(
    "downloader-bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# ---- Start message
@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text(
        "👋 Hello! I can download songs & videos from YouTube.\n\n"
        "🎵 Use `/song <name>` to download a song (MP3).\n"
        "🎥 Use `/video <name>` to download a video (MP4).",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{config.DEVELOPER.replace('@','')}")]]
        )
    )

# ---- Register module handlers
from modules.song import register as register_song
from modules.video import register as register_video
register_song(app)
register_video(app)
register_tiktok(app)

if __name__ == "__main__":
    app.run()
