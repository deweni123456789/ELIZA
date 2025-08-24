from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
import asyncio

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

# ---- Async startup to register modules
async def startup():
    register_song(app)            # normal functions
    register_video(app)           # normal functions
    register_tiktok(app)          # normal functions
    await register_instagram(app) # async function needs await

# ---- Run bot
async def main():
    await startup()        # register modules
    await app.start()      # start bot
    print("Bot is running...")
    # keep bot running forever
    await asyncio.Event().wait()  # ✅ replaces app.idle()

if __name__ == "__main__":
    asyncio.run(main())
