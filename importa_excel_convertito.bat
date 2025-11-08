@echo off
echo ========================================================================
echo IMPORTAZIONE AUTOMATICA EXCEL CONVERTITO
echo ========================================================================
echo.
echo Trascina qui il file Excel convertito e premi INVIO
echo (oppure digita il percorso completo del file)
echo.
set /p EXCEL_FILE="File Excel: "

if "%EXCEL_FILE%"=="" (
    echo ERRORE: Nessun file specificato
    pause
    exit /b 1
)

echo.
echo Esegui importazione nel database? (S/N)
set /p IMPORT_DB="Importa DB (S/N): "

if /i "%IMPORT_DB%"=="S" (
    python importa_excel_convertito.py "%EXCEL_FILE%" -import
) else (
    python importa_excel_convertito.py "%EXCEL_FILE%"
)

echo.
pause

