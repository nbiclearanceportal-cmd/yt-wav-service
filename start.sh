#!/bin/bash
# YT to WAV Service - Mac/Linux starter
# Usage: bash start.sh
set -e
cd "$(dirname "$0")"

command -v python3 >/dev/null || { echo "[ERROR] python3 nahi mila."; exit 1; }
if ! command -v node >/dev/null && ! command -v deno >/dev/null; then
    echo "[WARNING] node/deno nahi mila. YouTube ke liye nodejs install karein."
fi

[ -d venv ] || { echo "Virtual environment bana raha hoon..."; python3 -m venv venv; }

echo "Packages install ho rahe hain (pehli dafa 2-4 minute lag sakte hain)..."
./venv/bin/pip install -q -r requirements.txt

if [ ! -f .env ]; then
    echo "Secret bana raha hoon..."
    ./venv/bin/python -c "import secrets;open('.env','w').write('YTW_SECRET='+secrets.token_hex(24)+'\nYTW_BASE_URL=http://127.0.0.1:8765\nPORT=8765\n')"
fi

echo ""
echo "============================================================"
./venv/bin/python -c "
d={}
for l in open('.env',encoding='utf-8'):
    l=l.strip()
    if l and not l.startswith('#') and '=' in l:
        k,v=l.split('=',1); d[k.strip()]=v.strip()
print(' Service URL : '+d.get('YTW_BASE_URL','http://127.0.0.1:8765'))
print(' SECRET (isay WordPress -> Settings -> YT to WAV mein dalen):')
print(' '+d.get('YTW_SECRET',''))
"
echo "============================================================"
echo " Jab tak tool istemal karna ho, ye terminal KHULA rakhein."
echo " Band karne ke liye Ctrl+C dabayen."
echo ""
./venv/bin/python app.py
