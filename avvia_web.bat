@echo off
echo Avvio Football Stats App - WEB
echo Cartella: %CD%
echo.

REM Verifica che il file app_web.py esista
if not exist "app_web.py" (
    echo [ERRORE] app_web.py non trovato!
    pause
    exit /b 1
)
echo [OK] app_web.py trovato

REM Termina processi Python e Chrome esistenti
echo Terminazione processi Python e Chrome esistenti...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im chrome.exe >nul 2>&1
echo Attesa 5 secondi per pulizia completa...
timeout /t 5 /nobreak >nul

REM Avvia Streamlit
echo Avvio Streamlit WEB (senza apertura automatica browser)...
python -m streamlit run app_web.py --server.port 8502 --server.headless true

echo.
echo App WEB fermata. Premi un tasto per chiudere...
pause >nul
