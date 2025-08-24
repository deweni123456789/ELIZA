# Lightweight + fast startup
FROM python:3.11-slim

# System deps (ffmpeg) and performance basics
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir -U yt-dlp   # << always update yt-dlp to latest

# Copy the rest of the project
COPY . .

# Helpful envs (Pyrogram session name; tweak if you like)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Start the bot
CMD ["python", "main.py"]
