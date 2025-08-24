from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

from modules.tiktok import register as register_tiktok
from modules.instagram import register as register_instagram
from modules.song import register as register_song
from modules.video import register as register_video

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

# ---- Callback handler
@app.on_callback_query()
async def callbacks(bot, query):
    await handle_callbacks(bot, query)

# ---- Register modules
register_song(app)
register_video(app)
register_tiktok(app)

# --- FIXED: make register_instagram synchronous registration
def register_instagram_sync(app):
    import asyncio
    from modules.instagram import register as register_instagram_async
    # run the async register function safely
    asyncio.get_event_loop().run_until_complete(register_instagram_async(app))

register_instagram_sync(app)

# ---- Run bot (Pyrogram v2 style)
app.run()
