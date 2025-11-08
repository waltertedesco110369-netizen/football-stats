# ISTRUZIONI: Come usare copy_excel_to_template.py

## Passo 1: Converti il PDF in Excel
- Usa il convertitore scelto (es. PDF24, SmallPDF, Adobe Acrobat)
- Salva il file Excel convertito (es. `calcio base per data (2).xlsx`)
- Ricorda il percorso del file

## Passo 2: Apri il terminale/PowerShell
- Vai nella cartella del progetto:
  ```
  C:\Users\Utente\Dropbox\Il mio PC (DESKTOP-0NJJED5)\Desktop\Cursor\Progetti\In Produzione\Fottball_Stats_New
  ```

## Passo 3: Esegui lo script copy_excel_to_template.py
- Comando base:
  ```
  python copy_excel_to_template.py "percorso_completo_del_file_excel"
  ```

- Esempio con percorso relativo:
  ```
  python copy_excel_to_template.py "Import/Database/File/calcio base per data (2).xlsx"
  ```

- Esempio con percorso assoluto (se il file è in un'altra cartella):
  ```
  python copy_excel_to_template.py "C:\Users\Utente\Desktop\calcio base per data (2).xlsx"
  ```

## Passo 4: Verifica che sia andato tutto bene
Lo script mostrerà:
- ✓ File copiato con successo!
- File convertito: [nome file]
- Template aggiornato: Import/Database/File/template_calcio_base.xlsx
- Foglio IMPORT_TEMP sostituito
- Foglio DATI protetto mantenuto ✓

## Passo 5: Esegui la mappatura
- Esegui:
  ```
  python map_excel_to_template.py
  ```
- Questo script legge i dati dal foglio IMPORT_TEMP e li mappa nel foglio DATI protetto

## Passo 6: Importa nel database
- Apri l'applicazione Streamlit
- Vai alla sezione Import
- Seleziona il file: `Import/Database/File/template_calcio_base.xlsx`
- Assicurati di selezionare il foglio "DATI"
- Clicca Import

## IMPORTANTE:
- NON fare "Salva con nome" sul template
- Usa SEMPRE lo script copy_excel_to_template.py per copiare i dati
- Il foglio DATI protetto rimarrà sempre intatto

