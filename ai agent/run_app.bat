@echo off
chcp 65001 >nul
echo ===============================================================
echo   KHOI DONG HE THONG AI AGENT B2B - CONG TY CONG NGHE MINH AN
echo ===============================================================
start "" "http://localhost:8000"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause

