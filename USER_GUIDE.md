# Football Stats App - Guida Utente

## 🚀 Avvio dell'Applicazione

### Installazione
```bash
pip install -r requirements.txt
```

### Avvio
```bash
streamlit run app.py
```

L'applicazione sarà disponibile su: `http://localhost:8501`

## 📊 Funzionalità Principali

### 1. Dashboard
- **Statistiche Generali**: Visualizza il numero di stagioni, campionati, partite e file importati
- **Grafici**: Distribuzione delle partite per stagione
- **File Importati**: Lista degli ultimi file caricati nel database

### 2. Gestione Dati

#### Import File
- **Upload**: Carica file Excel (.xlsx, .xls) o CSV
- **Selezione Stagione**: Scegli la stagione corrispondente al file
- **Tipo File**: Specifica il tipo di file (main, new_leagues, future_matches)
- **Controllo Duplicati**: Il sistema evita automaticamente l'import di partite già presenti

#### Gestione File
- **Visualizzazione**: Lista di tutti i file importati con dettagli
- **Eliminazione**: Possibilità di eliminare singoli file dal database
- **Tracciamento**: Ogni file è tracciato con data di import e numero di record

#### Pulizia Database
- **Eliminazione Stagioni**: Rimuovi stagioni complete dal database
- **Avvisi di Sicurezza**: Conferma richiesta prima delle operazioni distruttive

### 3. Classifiche

#### Filtri Disponibili
- **Stagioni**: Seleziona una o più stagioni da analizzare
- **Campionati**: Scegli uno o più campionati (es. E0, I1, SP1, etc.)
- **Tipo Classifica**: Diversi tipi di classifiche disponibili

#### Tipi di Classifiche

##### Classifica Totale
- Partite giocate, vinte, pareggiate, perse
- Goal fatti e subiti
- Percentuali di vittorie, pareggi e sconfitte
- Riconoscimento automatico dei traguardi (Campione, Champions League, etc.)

##### Classifica Primo Tempo
- Statistiche basate sui risultati del primo tempo
- Utile per analisi delle prestazioni iniziali

##### Classifica Secondo Tempo
- Statistiche basate sui risultati del secondo tempo
- Mostra la capacità di recupero o mantenimento del vantaggio

##### Classifica Under/Over
- Soglie disponibili: 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5
- Percentuali di partite Under e Over per ogni squadra
- Ordinamento per percentuale Under (migliori squadre Under)

##### Classifica con Parametri
- **Esclusione Prime N Squadre**: Esclude gli scontri diretti tra le prime N squadre
- **Esclusione Ultime N Squadre**: Esclude gli scontri diretti tra le ultime N squadre
- **Configurabile**: Puoi scegliere quante squadre escludere (0-6)
- **Traguardi**: Riconoscimento automatico dei traguardi raggiunti

### 4. Statistiche Avanzate

#### Classifica BEST
- **Percentuale Vittorie**: Migliori squadre per % di vittorie
- **Percentuale Pareggi**: Squadre con più pareggi
- **Percentuale Sconfitte**: Squadre con meno sconfitte
- **Tutti i Campionati**: Analisi combinata di tutti i campionati disponibili

#### Classifica BEST con Parametri
- Stesse percentuali della BEST normale
- Applica le esclusioni per prime/ultime squadre
- Analisi più precisa delle prestazioni "pure"

#### Classifica BEST Under/Over
- Migliori squadre per percentuale Under/Over
- Soglia configurabile (0.5 - 8.5)
- Analisi combinata di tutti i campionati

### 5. Giocata Proposta (In Sviluppo)
- Sistema di bonus/malus per motivazioni squadre
- Analisi delle ultime 5 partite per squadra
- Testa a testa storici
- Proposte di giocata basate su statistiche avanzate

### 6. Import PDF (In Sviluppo)
- Estrazione automatica di partite future da PDF
- Integrazione con database principale
- Gestione di campionati non standard

## 📁 Struttura File Supportati

### File Standard (all-euro-data-XXXX-XXXX.xlsx)
- **Colonne Richieste**: Div, Date, Time, HomeTeam, AwayTeam, FTHG, FTAG, FTR, HTHG, HTAG, HTR
- **Colonne Opzionali**: HS, AS, HST, AST, HF, AF, HC, AC, HY, AY, HR, AR, B365H, B365D, B365A
- **Formato Data**: YYYY-MM-DD
- **Formato Ora**: HH:MM:SS

### File Personalizzati (new_leagues_data.xlsx)
- Struttura personalizzata supportata
- Mapping automatico delle colonne
- Gestione stagioni speciali (2020, 2021, etc. → 2020-2021, 2021-2022)

## ⚙️ Configurazione

### Gestione Stagioni
- **Stagione Corrente**: Sempre mostrata per prima
- **Stagioni Multiple**: Possibilità di selezionare più stagioni
- **Eliminazione Automatica**: Rimozione delle stagioni più vecchie quando necessario
- **Avvisi**: Conferma richiesta prima dell'eliminazione

### Database
- **SQLite**: Database locale per persistenza dati
- **Backup Automatico**: Salvataggio automatico delle modifiche
- **Controllo Integrità**: Verifica dei dati durante l'import

## 🔧 Risoluzione Problemi

### Errori di Import
- **Colonne Mancanti**: Verifica che il file abbia le colonne standard
- **Formato Data**: Assicurati che le date siano nel formato corretto
- **Duplicati**: Il sistema gestisce automaticamente i duplicati

### Performance
- **File Grandi**: L'import può richiedere tempo per file molto grandi
- **Memoria**: Chiudi altre applicazioni se riscontri problemi di memoria

### Database
- **Reset Database**: Elimina il file `football_stats.db` per ricominciare
- **Backup**: Copia il file `football_stats.db` per creare backup

## 📞 Supporto

Per problemi o domande:
1. Controlla questa documentazione
2. Verifica i log dell'applicazione
3. Controlla che tutti i file siano nel formato corretto

## 🚀 Prossimi Sviluppi

- Sistema Giocata Proposta completo
- Import PDF automatico
- Analisi avanzate con machine learning
- Esportazione dati in vari formati
- Dashboard personalizzabili
- Notifiche per aggiornamenti
