import os
import asyncio
import secrets
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.enums import ChatAction
import yt_dlp

# ---------- Config ----------
DEV_USERNAME = "deweni2"
_TEMP_DIR = "temp_ad_dl"
os.makedirs(_TEMP_DIR, exist_ok=True)

_URL_CACHE = {}  # token -> url

ADULT_DOMAINS = ["pornhub.com", "xvideos.com", "xnxx.com", "xhamster.com"]
ADULT_REGEX = r"(https?://[^\s]*?(?:pornhub\.com|xvideos\.com|xnxx\.com|xhamster\.com)[^\s]*)"

def _dev_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEV_USERNAME}")]]
    )

# ---------------- Download Video ----------------
async def _ydl_download_video(url: str):
    loop = asyncio.get_running_loop()
    token = secrets.token_hex(6)
    outtmpl = os.path.join(_TEMP_DIR, f"{token}.%(ext)s")

    def run():
        opts = {
            "format": "bv*+ba/best",
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            return filepath, info

    return await loop.run_in_executor(None, run)

# ---------------- Handlers ----------------
async def handle_private(client: Client, message: Message, url: str):
    token = secrets.token_hex(6)
    _URL_CACHE[token] = url

    buttons = [
        [InlineKeyboardButton("⬇️ Download Video", callback_data=f"dl|vid|{token}")],
        [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEV_USERNAME}")]
    ]

    await message.reply_text(
        "🔞 Adult video detected!\nChoose an option to download:",
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )

async def handle_callback(client: Client, query: CallbackQuery):
    if not query.data or not query.data.startswith("dl|"):
        return

    parts = query.data.split("|", 2)
    if len(parts) != 3:
        await query.answer("Invalid request", show_alert=True)
        return

    _tag, action, token = parts
    url = _URL_CACHE.get(token)
    if not url:
        await query.answer("Session expired. Send the link again.", show_alert=True)
        return

    await query.answer("Processing…")
    await query.message.reply_chat_action(ChatAction.UPLOAD_VIDEO)

    filepath = None
    try:
        if action == "vid":
            filepath, info = await _ydl_download_video(url)
            await query.message.reply_video(
                video=filepath,
                reply_markup=_dev_keyboard(),
                supports_streaming=True
            )

            # delete service/info message
            try:
                await query.message.delete()
            except:
                pass

    except Exception as e:
        await query.message.reply_text(
            f"❌ Download failed.\n<code>{e}</code>",
            reply_markup=_dev_keyboard()
        )
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        _URL_CACHE.pop(token, None)

# ---------------- Register ----------------
def register(app: Client):

    # Private chat: actual download
    @app.on_message(filters.private & filters.regex(ADULT_REGEX))
    async def private_handler(client, message: Message):
        url = message.text.strip()
        await handle_private(client, message, url)

    # Group chat: redirect to private
    @app.on_message(filters.group & filters.regex(ADULT_REGEX))
    async def group_handler(client, message: Message):
        bot_username = client.me.username

        buttons = [
            [InlineKeyboardButton("🔞 Get in Private Chat", url=f"https://t.me/{bot_username}?start=adult")],
            [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEV_USERNAME}")]
        ]

        await message.reply_text(
            "⚠️ Adult link detected! For safety, please use my private chat to download videos.",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )

    # Callback handler
    @app.on_callback_query()
    async def callback_router(client, query: CallbackQuery):
        await handle_callback(client, query)
