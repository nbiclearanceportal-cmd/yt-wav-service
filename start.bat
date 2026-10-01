@echo off
REM YT to WAV Service - Windows starter (double-click karein)
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python nahi mila. https://www.python.org/downloads/ se install karein
    echo (install karte waqt "Add python.exe to PATH" zaroor tick karein^)
    pause
    exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
    where deno >nul 2>nul
    if errorlevel 1 (
        echo [WARNING] Node.js nahi mila. YouTube download ke liye zaroori hai:
        echo https://nodejs.org/ se LTS version install karein, phir dobara chalayen.
        pause
    )
)

if not exist venv (
    echo Virtual environment bana raha hoon...
    python -m venv venv
)

echo Packages install ho rahe hain (pehli dafa 2-4 minute lag sakte hain)...
venv\Scripts\pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Packages install nahi ho sake. Internet check karein.
    pause
    exit /b 1
)

if not exist .env (
    echo Secret bana raha hoon...
    venv\Scripts\python -c "import secrets;open('.env','w').write('YTW_SECRET='+secrets.token_hex(24)+'\nYTW_BASE_URL=http://127.0.0.1:8765\nPORT=8765\n')"
)

echo.
echo ============================================================
venv\Scripts\python -c "d={};[d.__setitem__(p[0].strip(),p[1].strip()) for p in (l.split('=',1) for l in open('.env',encoding='utf-8')) if len(p)==2 and not p[0].startswith('#')];print(' Service URL : '+d.get('YTW_BASE_URL','http://127.0.0.1:8765'));print(' SECRET (isay WordPress -^> Settings -^> YT to WAV mein dalen):');print(' '+d.get('YTW_SECRET',''))"
echo ============================================================
echo  Jab tak tool istemal karna ho, ye window KHULI rakhein.
echo  Band karne ke liye Ctrl+C dabayen.
echo.
venv\Scripts\python app.py
pause
