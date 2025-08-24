# Lightweight + fast startup
FROM python:3.11-slim

# System deps (ffmpeg) and performance basics
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg curl ca-certificates git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (better cache usage)
COPY requirements.txt ./

# Install python deps (yt-dlp always latest)
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir -U yt-dlp

# Copy the rest of the bot
COPY . .

# Helpful envs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Run bot
CMD ["python", "main.py"]
