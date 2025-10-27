@echo off
title Football Stats - Deploy Automatico
echo.
echo ========================================
echo    FOOTBALL STATS - DEPLOY AUTOMATICO
echo ========================================
echo.

REM Verifica che siamo nella directory corretta
if not exist "app_simple.py" (
    echo [ERRORE] app_simple.py non trovato!
    echo Assicurati di essere nella directory del progetto.
    pause
    exit /b 1
)

echo [INFO] Directory progetto: %CD%
echo [INFO] Avvio deploy automatico...
echo.

REM Esegui il deploy
python deploy_system.py

echo.
echo ========================================
echo Deploy completato!
echo ========================================
pause
