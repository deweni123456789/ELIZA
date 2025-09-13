import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

# ---- Enable logging (show INFO, DEBUG logs in Railway console)
logging.basicConfig(level=logging.INFO)

# ---- Import modules
from modules.tiktok import register as register_tiktok, handle_callbacks as tiktok_callbacks
from modules.song import register as register_song
from modules.video import register as register_video
from modules.fb import register as register_fb

app = Client(
    "downloader-bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# ---- Start message
@app.on_message(filters.command("start"))
async def start(_, message):
    print("👉 /start command received")   # DEBUG LOG
    await message.reply_text(
        "👋 Hello! I can download songs & videos from YouTube.\n\n"
        "🎵 Use `/song <name>` to download a song (MP3).\n"
        "🎥 Use `/video <name>` to download a video (MP4).\n"
        "▶️ Use `/play <YouTube link>` to play directly in VC.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{config.DEVELOPER.replace('@','')}")]]
        )
    )

# ---- Callback handler
@app.on_callback_query()
async def callbacks(bot, query):
    print("👉 Callback query received:", query.data)   # DEBUG LOG
    await tiktok_callbacks(bot, query)
    # ⚠️ Comment out YouTube callbacks if not defined
    # await youtube_callbacks(bot, query)

# ---- Register modules
register_song(app)
register_video(app)
register_tiktok(app)
register_fb(app)

print("✅ All modules registered successfully!")   # DEBUG LOG

# ---- Run bot
app.run()
