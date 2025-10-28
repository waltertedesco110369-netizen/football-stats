# Caricare Dati su Render

## Problema
I database non persistono su Render. Quando carichi con Git, i dati si perdono.

## Soluzione: Carica Manualmente

### Passo 1: Apri l'app WEB su Render
- Vai su: https://football-stats-1-hepb.onrender.com
- Login come **admin** (password: admin123)

### Passo 2: Vai su "📁 Gestione Dati"
- Nella sidebar, clicca **"📁 Gestione Dati"**
- Seleziona il tab **"Import File"**

### Passo 3: Carica i tuoi Excel
- Clicca **"Carica un file Excel o CSV"**
- Seleziona il file Excel (es: B1.xlsx)
- Scegli la **Stagione** (es: 2025-2026)
- Scegli **Tipo File** (es: main)
- Clicca **"Importa File"**
- Ripeti per ogni file che hai

### Passo 4: Verifica
- Torna a **"📊 Dashboard"**
- Dovresti vedere i dati:
  - Stagioni Disponibili > 0
  - Campionati > 0
  - Partite Totali > 0
  - File Importati > 0

## Per MOBILE
- Fai lo stesso su: https://football-stats-mobile.onrender.com
- Login admin e carica gli stessi file

## Nota Importante
I dati caricati su Render **non vengono persi** se non cancelli i dati dal database.
I file Excel che carichi vengono salvati nel database Render e restano lì.

