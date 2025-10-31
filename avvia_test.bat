@echo off
title Football Stats App - TEST
echo Avvio Football Stats App - TEST (Sviluppo)
echo.
cd /d "C:\Users\Utente\Dropbox\Il mio PC (DESKTOP-0NJJED5)\Desktop\Cursor\Progetti\In Produzione\Fottball_Stats_New"
echo Cartella: %CD%
echo.
echo Verifica file app_simple.py...
if exist app_simple.py (
    echo [OK] app_simple.py trovato
) else (
    echo [ERRORE] app_simple.py non trovato
    pause
    exit
)
echo.
echo Terminazione processi Python e Chrome esistenti...
taskkill /f /im python.exe 2>nul
taskkill /f /im chrome.exe 2>nul
echo Attesa 5 secondi per pulizia completa...
timeout /t 5 /nobreak >nul
echo.
echo Avvio Streamlit TEST (senza apertura automatica browser)...
set APP_ENV=test
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
set STREAMLIT_SERVER_HEADLESS=true
python -m streamlit run app_simple.py --server.port 8501
echo.
echo App TEST fermata. Premi un tasto per chiudere...
pause
