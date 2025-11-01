# Changelog

## 2025-11-01
- **Import File**: Rimozione filtro stagione manuale - ora la stagione viene sempre rilevata automaticamente dal file.
- **Import File**: Rimozione selectbox "Tipo File" (parametro non utilizzato nel codice).
- **Database**: Aggiunta protezione nomi campionati - i campionati esistenti sono protetti e non modificabili senza richiesta esplicita.
- **Database**: Aggiunta mappatura completa nomi campionati per codici (B1, D1, E0, E1, F1, F2, I1, I2, N1, P1, SC0-3, SP1-2, T1) con nomi descrittivi.
- **Sicurezza**: Chat nascosta agli utenti guest su ambienti WEB e MOBILE - visibile solo agli amministratori.
- **UI**: Miglioramento interfaccia import file con messaggio informativo automatico.

## 2025-10-31
- Under/Over: aggiunta colonna "ULTIME 5" con simboli colorati (+ verde per Over, - rosso per Under) in tutte le classifiche Under/Over (Under/Over, Classifica BEST Under/Over, Classifica U/O Totale).
- UI: fix layout colonna "ULTIME 5" per visualizzazione orizzontale dei badge anche su schermi stretti/mobile (flexbox + white-space: nowrap).
- Deploy: aggiornati WEB e MOBILE locali.

## 2025-10-29
- Log Accessi: aggiunti contatori cumulativi (Accessi Totali, Visualizzazioni Totali) persistenti.
- Log Accessi: pulsante per pulizia log pi  vecchi di N giorni (default 60) senza toccare i contatori.
- UI Log Accessi: visualizzazione semplificata con expander per evitare problemi CSS.
- Deploy: backup completo con retention = 2, aggiornati WEB e MOBILE.
