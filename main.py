from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
from modules.tiktok import register as register_tiktok
from vc_player import add_to_queue, handle_callbacks

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
        "🎥 Use `/video <name>` to download a video (MP4).\n"
        "▶️ Use `/play <YouTube link>` to play directly in VC.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{config.DEVELOPER.replace('@','')}")]]
        )
    )

# ---- Play Command (directly add to queue)
@app.on_message(filters.command("play"))
async def play_handler(bot, message):
    if len(message.command) < 2:
        return await message.reply("❌ Please provide a YouTube link or file name!")

    yt_link = message.text.split(None, 1)[1]
    title = "YouTube Song"   # Replace with yt-dlp metadata
    duration = "4:30"        # Replace with metadata
    file_path = "downloads/sample.mp3"  # Replace with downloaded file
    
    await add_to_queue(file_path, title, duration, message.from_user.mention, message.chat.id, bot, message)

# ---- Register other modules
from modules.song import register as register_song
from modules.video import register as register_video
register_song(app)
register_video(app)
register_tiktok(app)

# ---- Callback handler
@app.on_callback_query()
async def callbacks(bot, query):
    await handle_callbacks(bot, query)

if __name__ == "__main__":
    app.run()
