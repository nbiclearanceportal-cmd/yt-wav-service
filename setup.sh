#!/bin/bash
# YT to WAV service installer — Ubuntu/Debian VPS par root ya sudo se chalayen:
#   sudo bash setup.sh
set -e

echo "== packages =="
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip ffmpeg curl openssl nodejs > /dev/null

echo "== user & dirs =="
id -u ytwav >/dev/null 2>&1 || useradd -r -m -s /bin/false ytwav
mkdir -p /opt/yt-wav
cp app.py requirements.txt /opt/yt-wav/
chown -R ytwav:ytwav /opt/yt-wav
mkdir -p /tmp/yt-wav && chown ytwav:ytwav /tmp/yt-wav

echo "== python env =="
python3 -m venv /opt/yt-wav/venv
/opt/yt-wav/venv/bin/pip install -q --upgrade pip
/opt/yt-wav/venv/bin/pip install -q -r /opt/yt-wav/requirements.txt

echo "== config =="
SECRET=$(openssl rand -hex 24)
IP=$(curl -s -m 10 ifconfig.me || hostname -I | awk '{print $1}')
cat > /etc/yt-wav.env <<EOF
YTW_SECRET=$SECRET
YTW_BASE_URL=http://$IP:8765
PORT=8765
EOF
chmod 600 /etc/yt-wav.env

echo "== systemd =="
cp yt-wav.service /etc/systemd/system/yt-wav.service
systemctl daemon-reload
systemctl enable -q yt-wav
systemctl restart yt-wav
sleep 3

if command -v ufw >/dev/null 2>&1; then
  ufw allow 8765/tcp >/dev/null 2>&1 || true
fi

echo ""
echo "== DONE =="
systemctl is-active -q yt-wav && echo "Service: RUNNING" || echo "Service: FAILED - check 'journalctl -u yt-wav'"
echo "Service URL : http://$IP:8765"
echo "Health check: curl http://$IP:8765/health"
echo ""
echo "SECRET (isay WordPress plugin ki Settings -> YT to WAV mein dalen):"
echo "$SECRET"
