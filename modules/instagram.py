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
        requester = message.from_user.mention  # mention of the user who requested

        info_msg = await message.reply_text("Downloading from Instagram... ⏳")

        try:
            L = instaloader.Instaloader()
            post = instaloader.Post.from_shortcode(L.context, url.split("/")[-2])

            caption = f"""
📌 Profile: {post.owner_username}
🗓️ Date: {post.date.strftime('%Y-%m-%d')}
⏰ Time: {post.date.strftime('%H:%M:%S')}
❤️ Likes: {post.likes}
💬 Comments: {post.comments}
🔁 Shares: N/A
👤 Requested by: {requester}
            """

            target_dir = f"temp_{post.shortcode}"
            os.makedirs(target_dir, exist_ok=True)

            # Download video or image
            if post.is_video:
                L.download_post(post, target=target_dir)
                video_path = os.path.join(target_dir, post.shortcode + ".mp4")
                await client.send_video(
                    chat_id=message.chat.id,
                    video=video_path,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]]
                    )
                )
            else:
                L.download_post(post, target=target_dir)
                photo_path = os.path.join(target_dir, post.shortcode + ".jpg")
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=photo_path,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]]
                    )
                )

            # Clean up temp folder
            for file in os.listdir(target_dir):
                os.remove(os.path.join(target_dir, file))
            os.rmdir(target_dir)

            await info_msg.delete()

        except Exception as e:
            await info_msg.edit_text(f"❌ Error: {e}")
