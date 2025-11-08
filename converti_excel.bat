@echo off
echo ========================================================================
echo CONVERSIONE EXCEL CONVERTITO IN FORMATO COMPATIBILE
echo ========================================================================
echo.
echo Trascina qui il file Excel convertito e premi INVIO
echo.
set /p EXCEL_FILE="File Excel: "

if "%EXCEL_FILE%"=="" (
    echo ERRORE: Nessun file specificato
    pause
    exit /b 1
)

python converti_excel_compatibile.py "%EXCEL_FILE%"

echo.
pause

