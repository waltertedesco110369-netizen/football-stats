@echo off
echo Avvio Football Stats App - MOBILE
echo Cartella: %CD%
echo.

REM Verifica che il file app_mobile.py esista
if not exist "app_mobile.py" (
    echo [ERRORE] app_mobile.py non trovato!
    pause
    exit /b 1
)
echo [OK] app_mobile.py trovato

REM Termina processi Python e Chrome esistenti
echo Terminazione processi Python e Chrome esistenti...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im chrome.exe >nul 2>&1
echo Attesa 5 secondi per pulizia completa...
timeout /t 5 /nobreak >nul

REM Avvia Streamlit con accesso da rete locale
echo Avvio Streamlit MOBILE (accessibile da telefono)...
echo Indirizzo sul telefono: http://192.168.1.12:8505
set APP_ENV=mobile
python -m streamlit run app_mobile.py --server.port 8505 --server.headless true --server.address 0.0.0.0

echo.
echo App MOBILE fermata. Premi un tasto per chiudere...
pause >nul
