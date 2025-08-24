# modules/instagram.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import instaloader
import os

async def register(app: Client):

    @app.on_message(filters.command("insta"))
    async def insta_download(client, message):
        if len(message.command) < 2:
            await message.reply_text("Usage: /insta <Instagram Post URL>")
            return

        url = message.command[1]
        requester = message.from_user.mention

        info_msg = await message.reply_text("Downloading from Instagram... ⏳")

        try:
            L = instaloader.Instaloader()
            shortcode = url.rstrip("/").split("/")[-1]
            post = instaloader.Post.from_shortcode(L.context, shortcode)

            caption = f"""
📌 Profile: {post.owner_username}
🗓️ Date: {post.date.strftime('%Y-%m-%d')}
⏰ Time: {post.date.strftime('%H:%M:%S')}
❤️ Likes: {post.likes}
💬 Comments: {post.comments}
👤 Requested by: {requester}
            """

            target_dir = f"temp_{post.shortcode}"
            os.makedirs(target_dir, exist_ok=True)

            # Download post
            L.download_post(post, target=target_dir)

            # Detect downloaded file
            files = os.listdir(target_dir)
            if not files:
                await info_msg.edit_text("❌ Error: No file was downloaded.")
                return

            file_path = os.path.join(target_dir, files[0])

            # Send video or photo
            if post.is_video:
                await client.send_video(
                    chat_id=message.chat.id,
                    video=file_path,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]]
                    )
                )
            else:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=file_path,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]]
                    )
                )

            # Cleanup temp folder
            for f in os.listdir(target_dir):
                os.remove(os.path.join(target_dir, f))
            os.rmdir(target_dir)

            await info_msg.delete()

        except Exception as e:
            await info_msg.edit_text(f"❌ Error: {e}")
