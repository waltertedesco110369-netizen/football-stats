# Caricare Dati su Render

## ⚠️ PROBLEMA CRITICO: Persistenza Database su Render

**Il problema**: Su Render (piano gratuito), il database SQLite **NON persiste** tra i riavvii o i deploy. Quando l'app viene riavviata o c'è un nuovo deploy, i dati vengono persi.

### Perché succede?
- Render (piano gratuito) **non ha storage persistente**
- I file nella directory root vengono persi quando l'app viene riavviata
- Ogni nuovo deploy cancella i file precedenti

### Soluzioni Possibili:

#### ✅ Soluzione 1: Carica Manualmente Dopo Ogni Riavvio
Carica i dati manualmente ogni volta che l'app viene riavviata:

1. Apri l'app WEB su Render
2. Login come **admin** (password: admin123)
3. Vai su **"📁 Gestione Dati"** → **"Import File"**
4. Carica tutti i tuoi file Excel
5. Verifica che i dati siano presenti

**Nota**: Devi rifare questo processo ogni volta che Render riavvia l'app.

#### ✅ Soluzione 2: Usa PostgreSQL (Consigliato)
Render offre PostgreSQL gratuito con storage persistente:

1. Vai su Render Dashboard
2. Crea un nuovo **PostgreSQL Database** (gratuito)
3. Modifica `database.py` per usare PostgreSQL invece di SQLite
4. I dati persisteranno tra i riavvii

#### ✅ Soluzione 3: Usa Storage Esterno
Usa un servizio di storage esterno (AWS S3, Google Cloud Storage, ecc.) per salvare il database.

---

## 📋 Istruzioni Caricamento Manuale

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

## ⚠️ IMPORTANTE
I dati caricati su Render **vengono persi** quando:
- L'app viene riavviata da Render
- C'è un nuovo deploy
- Render fa un restart automatico

**Soluzione temporanea**: Carica i dati manualmente dopo ogni riavvio.
**Soluzione definitiva**: Usa PostgreSQL o storage esterno.

