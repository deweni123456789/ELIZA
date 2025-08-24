# modules/instagram.py
import os
import instaloader
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo

# Instaloader init
L = instaloader.Instaloader(download_videos=True, download_comments=False, save_metadata=False, post_metadata_txt_pattern="")

def register(app: Client):

    @app.on_message(filters.command("ig"))
    async def instagram_download(client, message):
        if len(message.command) < 2:
            await message.reply_text("Send a valid Instagram post URL.\nUsage: /ig <link>")
            return

        url = message.command[1]
        msg = await message.reply_text("⏳ Downloading Instagram post...")

        try:
            shortcode = url.rstrip("/").split("/")[-1]
            post = instaloader.Post.from_shortcode(L.context, shortcode)

            # Only description + requester + developer
            caption = f"""
📄 {post.caption or 'No description'}
👤 Requested by: {message.from_user.mention}
👨‍💻 Developer: @deweni2
            """

            temp_dir = "temp_instagram"
            os.makedirs(temp_dir, exist_ok=True)
            media_files = []

            if post.typename == "GraphImage":
                file_path = os.path.join(temp_dir, f"{shortcode}.jpg")
                L.download_pic(file_path, post.url, post.date_utc)
                media_files.append(file_path)

            elif post.typename == "GraphVideo":
                L.download_post(post, temp_dir)
                for f in os.listdir(temp_dir):
                    if f.endswith(".mp4"):
                        media_files.append(os.path.join(temp_dir, f))

            elif post.typename == "GraphSidecar":
                L.download_post(post, temp_dir)
                for f in os.listdir(temp_dir):
                    if f.endswith((".jpg", ".mp4")):
                        media_files.append(os.path.join(temp_dir, f))

            # Send
            if len(media_files) == 1:
                if media_files[0].endswith(".jpg"):
                    await message.reply_photo(media_files[0], caption=caption)
                else:
                    await message.reply_video(media_files[0], caption=caption)
            else:
                media_group = []
                for f in media_files:
                    if f.endswith(".jpg"):
                        media_group.append(InputMediaPhoto(f))
                    else:
                        media_group.append(InputMediaVideo(f))
                await message.reply_media_group(media_group)
                await message.reply_text(caption)

        except Exception as e:
            await message.reply_text(f"❌ Failed to fetch Instagram post.\nError: {e}")

        finally:
            await msg.delete()
            # cleanup
            if os.path.exists(temp_dir):
                for f in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, f))
                os.rmdir(temp_dir)
