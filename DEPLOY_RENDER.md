# 🚀 Deploy Football Stats su Render

## Passaggi per pubblicare l'app su Render:

### 1. Crea repository GitHub
```bash
# Inizializza Git (se non già fatto)
git init

# Aggiungi tutti i file
git add .

# Crea commit
git commit -m "Football Stats App - versione pubblicabile"

# Crea repository su GitHub (github.com)
# Poi esegui:
git remote add origin https://github.com/TUO-USERNAME/football-stats.git
git branch -M main
git push -u origin main
```

### 2. Deploy su Render
1. Vai su **[render.com](https://render.com)**
2. **Registrati** (con GitHub)
3. **New** → **Web Service**
4. **Connetti** il tuo repository GitHub
5. **Impostazioni**:
   - **Name**: `football-stats`
   - **Region**: `Frankfurt` (più vicino Italia)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app_mobile.py --server.port $PORT --server.address 0.0.0.0`
   - **Plan**: `Free`

6. **Deploy**
7. Attendi 2-3 minuti
8. Ottieni URL: `https://football-stats.onrender.com`

### 3. Accesso pubblico
- **URL pubblico**: `https://football-stats.onrender.com`
- **Chiunque** può accedere
- **Login obbligatorio**: Ospite `guest` / Admin `admin123`

### 4. Aggiornamenti
Ogni push su GitHub aggiorna automaticamente l'app su Render

## 🔒 Sicurezza
- ✅ Autenticazione attiva
- ✅ Database separato per MOBILE
- ✅ Backups automatici su Render

