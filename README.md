# Football Stats App

## Descrizione
Applicazione Streamlit completa per visualizzare statistiche avanzate di calcio con database SQLite e funzionalità di analisi sofisticate.

## ✨ Funzionalità Implementate

### ✅ Database e Import Dati
- **Gestione File**: Supporto Excel/CSV con colonne standardizzate
- **Import Automatico**: Controllo duplicati e gestione stagioni
- **Tracciamento**: Log completo dei file importati con possibilità di eliminazione selettiva
- **Gestione Stagioni**: Eliminazione automatica delle stagioni più vecchie con conferma

### ✅ Classifiche Complete
1. **Classifica Totale** - Statistiche complete con percentuali e traguardi automatici
2. **Classifica Primo Tempo** - Analisi prestazioni primo tempo
3. **Classifica Secondo Tempo** - Analisi prestazioni secondo tempo  
4. **Classifica Under/Over** - Per soglie 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5
5. **Classifica con Parametri** - Esclusione prime/ultime squadre configurabile (0-6)
6. **Classifica BEST** - Migliori squadre per percentuale vittorie/pareggi/sconfitte
7. **Classifica BEST con Parametri** - Migliori squadre con esclusioni applicate
8. **Classifica BEST Under/Over** - Migliori per soglie gol specifiche

### ✅ Interfaccia Avanzata
- **Dashboard**: Statistiche generali e grafici interattivi
- **Filtri Dinamici**: Menu a tendina per stagioni e campionati multipli
- **Gestione Dati**: Upload, eliminazione e pulizia database
- **Riconoscimento Traguardi**: Campione, Champions League, Europa League, Retrocessioni

### 🚧 In Sviluppo
- **Giocata Proposta**: Sistema bonus/malus per motivazioni squadre
- **Import PDF**: Estrazione partite future da file scommesse
- **Analisi Testa a Testa**: Ultime 5 partite e scontri diretti

## 🚀 Installazione e Avvio

### Prerequisiti
- Python 3.8+
- pip (gestore pacchetti Python)

### Installazione
```bash
# Clona il repository
git clone <repository-url>
cd Fottball_Stats_New

# Installa le dipendenze
pip install -r requirements.txt
```

### Avvio Rapido
```bash
# Avvio standard
streamlit run app.py

# Avvio con porta specifica
streamlit run app.py --server.port 8501
```

### Deploy Automatico
```bash
# Linux/Mac
chmod +x deploy.sh
./deploy.sh

# Windows
deploy.bat
```

## 📊 Struttura Database

### Colonne Standard Supportate
- **Base**: Div, Date, Time, HomeTeam, AwayTeam, FTHG, FTAG, FTR
- **Primo Tempo**: HTHG, HTAG, HTR
- **Statistiche**: HS, AS, HST, AST, HF, AF, HC, AC, HY, AY, HR, AR
- **Quote**: B365H, B365D, B365A, BWH, BWD, BWA, IWH, IWD, IWA, PSH, PSD, PSA
- **Under/Over**: B365>2.5, B365<2.5, P>2.5, P<2.5, Max>2.5, Max<2.5
- **Asian Handicap**: AHh, B365AHH, B365AHA, PAHH, PAHA
- **Corner**: B365CH, B365CD, B365CA, BWCH, BWCD, BWCA

### File Supportati
- **all-euro-data-XXXX-XXXX.xlsx**: File standard con tutte le colonne
- **new_leagues_data.xlsx**: File con struttura personalizzata
- **File CSV**: Con colonne standard

## 🎯 Utilizzo

### 1. Import Dati
1. Vai su "📁 Gestione Dati" → "Import File"
2. Carica il file Excel/CSV
3. Seleziona stagione e tipo file
4. Clicca "Importa File"

### 2. Visualizzazione Classifiche
1. Vai su "🏆 Classifiche"
2. Seleziona stagioni e campionati
3. Scegli il tipo di classifica
4. Configura parametri se necessario

### 3. Statistiche Avanzate
1. Vai su "📈 Statistiche Avanzate"
2. Seleziona filtri
3. Esplora le diverse classifiche BEST

## 📁 Struttura Progetto

```
Fottball_Stats_New/
├── app.py                 # Applicazione Streamlit principale
├── database.py            # Gestione database SQLite
├── stats_calculator.py    # Calcoli statistiche e classifiche
├── config.py             # Configurazioni e mapping
├── import_data.py        # Script import automatico
├── requirements.txt      # Dipendenze Python
├── deploy.sh            # Script deploy Linux/Mac
├── deploy.bat           # Script deploy Windows
├── README.md            # Questa documentazione
├── USER_GUIDE.md        # Guida utente dettagliata
└── Import/
    └── Database/
        └── File/        # File Excel/CSV da importare
```

## 🔧 Configurazione

### Gestione Stagioni
- **Stagione Corrente**: Sempre mostrata per prima nei filtri
- **Stagioni Multiple**: Selezione multipla disponibile
- **Eliminazione Automatica**: Rimozione stagioni vecchie con conferma

### Parametri Classifiche
- **Esclusione Prime**: 0-6 squadre dalla cima
- **Esclusione Ultime**: 0-6 squadre dal fondo
- **Soglie Under/Over**: 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5

### Traguardi Automatici
- **Campione**: 1° posto
- **Champions League**: Posizioni 1-4
- **Europa League**: Posizioni 5-6
- **Conference League**: Posizione 7
- **Retrocessioni**: Ultime 3 posizioni

## 🐛 Risoluzione Problemi

### Errori Comuni
1. **File non trovato**: Verifica il percorso dei file in `Import/Database/File/`
2. **Colonne mancanti**: Controlla che il file abbia le colonne standard
3. **Errore database**: Elimina `football_stats.db` per ricominciare
4. **Porta occupata**: Usa `--server.port 8502` per cambiare porta

### Log e Debug
- Controlla i messaggi nella console Streamlit
- Verifica il file `DEPLOY_LOG.txt` per cronologia modifiche
- Usa il backup automatico del database

## 📈 Performance

### Ottimizzazioni
- **Cache**: Streamlit cache per operazioni costose
- **Database**: SQLite ottimizzato per query veloci
- **Import**: Controllo duplicati per evitare rallentamenti

### Limiti
- **File Grandi**: Import può richiedere tempo per file >10MB
- **Memoria**: Consigliato 4GB+ RAM per database grandi
- **Concorrenza**: Un utente alla volta per evitare conflitti

## 🤝 Contributi

### Sviluppo
1. Fork del repository
2. Crea branch per nuova funzionalità
3. Implementa modifiche
4. Testa completamente
5. Crea Pull Request

### Segnalazione Bug
1. Descrivi il problema dettagliatamente
2. Includi file di log se disponibili
3. Specifica versione Python e OS
4. Fornisci passi per riprodurre

## 📄 Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi il file LICENSE per dettagli.

## 📞 Supporto

- **Documentazione**: Leggi `USER_GUIDE.md` per guida dettagliata
- **Issues**: Usa GitHub Issues per problemi
- **Wiki**: Consulta la wiki del progetto per esempi avanzati

---

**Football Stats App** - Analisi statistiche avanzate per il calcio ⚽