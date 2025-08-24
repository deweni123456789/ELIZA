import asyncio
import os
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputAudioStream

# ---------- USERBOT (for VC) ----------
userbot = Client("userbot", api_id=YOUR_API_ID, api_hash=YOUR_API_HASH, session_string="YOUR_SESSION_STRING")
pytgcalls = PyTgCalls(userbot)

# ---------- PLAYLIST ----------
playlist = []

# ---------- ADD SONG TO QUEUE ----------
async def add_to_queue(file_path, title, duration, requester, group_id, bot: Client, message):
    playlist.append({
        "file_path": file_path,
        "title": title,
        "duration": duration,
        "requester": requester,
        "group_id": group_id
    })
    if len(playlist) == 1:
        await play_next(bot, message)

# ---------- PLAY NEXT SONG ----------
async def play_next(bot: Client, message):
    if not playlist:
        return
    
    current = playlist[0]
    await pytgcalls.join_group_call(
        current["group_id"],
        InputAudioStream(current["file_path"])
    )

    # Send UI
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸ Pause", callback_data="pause"),
            InlineKeyboardButton("⏹ Stop", callback_data="stop"),
            InlineKeyboardButton("⏭ Skip", callback_data="skip")
        ],
        [InlineKeyboardButton("❌ Close", callback_data="close")]
    ])

    await bot.send_photo(
        chat_id=current["group_id"],
        photo="https://telegra.ph/file/f8e14b60c3f4b5084e3f8.jpg",  # custom thumbnail here
        caption=f"➤ **Started Streaming** 🎶\n\n"
                f"▶️ **Title:** {current['title']}\n"
                f"⏳ **Duration:** {current['duration']}\n"
                f"🙍 **Requested By:** {current['requester']}",
        reply_markup=buttons
    )

# ---------- CALLBACKS ----------
async def handle_callbacks(bot: Client, query):
    data = query.data
    if data == "pause":
        await pytgcalls.pause_stream(query.message.chat.id)
        await query.answer("⏸ Paused", show_alert=True)
    elif data == "stop":
        await pytgcalls.leave_group_call(query.message.chat.id)
        playlist.clear()
        await query.answer("⏹ Stopped", show_alert=True)
    elif data == "skip":
        if playlist:
            playlist.pop(0)
        await pytgcalls.leave_group_call(query.message.chat.id)
        if playlist:
            await play_next(bot, query.message)
        await query.answer("⏭ Skipped", show_alert=True)
    elif data == "close":
        await query.message.delete()
