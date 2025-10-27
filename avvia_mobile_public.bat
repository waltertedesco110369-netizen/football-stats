@echo off
echo ========================================
echo Football Stats - MOBILE PUBBLICO (NGrok)
echo ========================================
echo.
echo 1. Avvio app MOBILE su porta 8505...
start /B python -m streamlit run app_mobile.py --server.port 8505 --server.headless true --server.address 0.0.0.0

echo.
echo 2. Attendi 5 secondi...
timeout /t 5 /nobreak

echo.
echo 3. Avvio NGrok tunnel...
echo.
echo ✅ App pubblica su: (vedi URL sopra)
echo.
echo ⚠️  Ferma con CTRL+C quando finisci
echo.

ngrok http 8505

pause

