import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

@Client.on_message(filters.command("video"))
async def video_handler(client, message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply_text("⚠️ Please provide a video name.\n\nExample: `/video despacito`")

    msg = await message.reply_text("🔎 Searching for video...")

    ydl_opts = {"format": "best", "noplaylist": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)["entries"][0]
        except Exception as e:
            return await msg.edit(f"❌ Error: {str(e)}")

    file_path = ydl.prepare_filename(info)

    caption = (
        f"🎥 **Title:** {info['title']}\n"
        f"📺 **Channel:** {info.get('uploader')}\n"
        f"📅 **Upload Date:** {info.get('upload_date')}\n"
        f"⏱ **Duration:** {info.get('duration')} sec\n"
        f"👁 **Views:** {info.get('view_count')}\n"
        f"👍 **Likes:** {info.get('like_count','N/A')}\n"
        f"💬 **Comments:** {info.get('comment_count','N/A')}\n\n"
        f"🙋‍♂️ **Requested by:** {message.from_user.mention}"
    )

    await client.send_video(
        message.chat.id,
        video=file_path,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{config.DEVELOPER.replace('@','')}")]]
        )
    )
    await msg.delete()
