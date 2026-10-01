# YT to WAV service - Render (Docker)
FROM python:3.12-slim

# node (yt-dlp ke JS challenges ke liye) + ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl xz-utils \
 && curl -fsSL https://nodejs.org/dist/v22.14.0/node-v22.14.0-linux-x64.tar.xz -o /tmp/node.tar.xz \
 && tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 \
 && rm /tmp/node.tar.xz \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/* \
 && node --version && ffmpeg -version | head -1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

# Render PORT env deta hai (default 10000); app.py usay khud parhta hai
EXPOSE 10000
CMD ["sh", "-c", "waitress-serve --listen=0.0.0.0:$PORT app:app"]
