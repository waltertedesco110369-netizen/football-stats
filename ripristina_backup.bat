@echo off
title Football Stats - Ripristino Backup
echo.
echo ========================================
echo   FOOTBALL STATS - RIPRISTINO BACKUP
echo ========================================
echo.

REM Verifica che siamo nella directory corretta
if not exist "restore_backup.py" (
    echo [ERRORE] restore_backup.py non trovato!
    echo Assicurati di essere nella directory del progetto.
    pause
    exit /b 1
)

echo [INFO] Directory progetto: %CD%
echo [INFO] Avvio ripristino backup...
echo.

REM Esegui il ripristino
python restore_backup.py

echo.
echo ========================================
echo Ripristino completato!
echo ========================================
pause
