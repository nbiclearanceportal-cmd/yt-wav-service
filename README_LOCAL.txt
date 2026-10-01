YT to WAV - Local Service (apne PC ke liye)
==========================================

Ye aapke apne computer par chalne wala WAV service hai.
Is ke sath WordPress plugin v3 judta hai aur YouTube se WAV banata hai.

ZAROOORI CHEEZEIN (ek dafa install karein)
------------------------------------------
1. Python: https://www.python.org/downloads/
   - Windows par install karte waqt "Add python.exe to PATH" zaroor tick karein.
2. Node.js (LTS): https://nodejs.org/
   - YouTube se download ke liye zaroori hai.

CHALANE KA TARIKA
-----------------
1. Is zip ko kisi folder mein extract karein, misal: C:\yt-wav\
2. Windows:  start.bat par double-click karein
   Mac/Linux: terminal mein   bash start.sh
3. Pehli dafa 2-4 minute lagega (packages download honge).
4. Kaali window mein ye do cheezein nazar aayengi:
     Service URL : http://127.0.0.1:8765
     SECRET      : (lambi si key)
   SECRET ko copy kar lein.

WORDPRESS SE JORNA (mohsinkhan.local)
-------------------------------------
1. yt-to-wav-downloader-v3.zip ko WordPress mein install + activate karein
   (Plugins -> Add New -> Upload Plugin).
   Agar purana v2 laga hai to pehle usay deactivate karke delete kar dein.
2. Koi page banayein (misal "YT to WAV") aur us mein likhein:  [yt_to_wav]
3. Settings -> YT to WAV kholein:
     Service URL : http://127.0.0.1:8765
     Service Secret : (uper wali SECRET paste karein)
   Save karein.
4. Page kholein, YouTube link dalein, "WAV banayen" dabayein.

AHEM BAATEIN
------------
- Jab tak tool istemal karna ho, start.bat wali kaali window KHULI rakhein.
  Band karne ke liye Ctrl+C.
- Ye setup SIRF aapke apne PC par kaam karega (local use).
  Internet par live website ke liye VPS/Render wala setup chahiye.
- Masla aaye to window mein jo error likha ho wo bhej dein.
