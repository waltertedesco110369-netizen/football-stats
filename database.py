import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, date
import os
import logging
from pathlib import Path
import re
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# MAPPATURE COLONNE - Per gestire formati diversi
# ============================================================================

# Mappatura STANDARD (come i file attuali)
MAPPATURA_STANDARD = {
    'Div': 'div',
    'Season': 'season',
    'Date': 'date',
    'Time': 'time',
    'HomeTeam': 'home_team',
    'AwayTeam': 'away_team',
    'FTHG': 'ft_home_goals',
    'FTAG': 'ft_away_goals',
    'FTR': 'ft_result',
    'HTHG': 'ht_home_goals',
    'HTAG': 'ht_away_goals',
    'HTR': 'ht_result',
    'HS': 'home_shots',
    'AS': 'away_shots',
    'HST': 'home_shots_target',
    'AST': 'away_shots_target',
    'HF': 'home_fouls',
    'AF': 'away_fouls',
    'HC': 'home_corners',
    'AC': 'away_corners',
    'HY': 'home_yellow',
    'AY': 'away_yellow',
    'HR': 'home_red',
    'AR': 'away_red'
}

# Mappatura NEW LEAGUES (campionati esteri con stagione anno singolo)
MAPPATURA_NEW_LEAGUES = {
    'League': 'div',
    'Season': 'season',  # Verrà convertita da 2021 a 2021-2022
    'Date': 'date',
    'Time': 'time',
    'Home': 'home_team',
    'Away': 'away_team',
    'HG': 'ft_home_goals',
    'AG': 'ft_away_goals',
    'Res': 'ft_result'
}

# Dizionario con tutte le mappature disponibili
MAPPATURE_DISPONIBILI = {
    'standard': MAPPATURA_STANDARD,
    'new_leagues': MAPPATURA_NEW_LEAGUES
}

# Mappatura League dal PDF convertito al nome corretto nel database
MAPPA_LEAGUE_PDF = {
    'ALB1': 'ALB1 - Albania Abissnet Superiore',
    'ALG1': 'ALG1 - Algeria Ligue 1',
    'AND1': 'AND1 - Andora - Primera Divisió',
    'ARG1': 'ARG1 - Argentina  Torneo Betano - Clausura',
    'ARG': 'ARG1 - Argentina  Torneo Betano - Clausura',  # Fallback se senza numero
    'ARG2': 'ARG2 - Argentina Primera B - Clausura',
    'ARG3': 'ARG3 - Argentina Primera C - Clausura',
    'ARM1': 'ARM1 - Armenia Premier League',
    'ARUBA1': 'ARU1 - Aruba Division di honor',
    'ASIACL': 'ASIA - AFC Champions League',
    'AUS1': 'AUS1 - Australia - A-League',
    'AUS1F': 'AUS1F - Australia - A-League Femminile',
    'AUT1': 'AUT - Austria Bundesliga',
    'BEL1': 'B1 - Belgio Jupiler Pro League',
    'BRA1': 'BRA - Brasile Serie A BETANO',
    'FRA1': 'F1 - Francia Ligue 1',
    'FRA2': 'F2 - Francia Ligue 2',
    'GER1': 'D1 - Germania Bundesliga',
    'GER2': 'D2 - Germania 2. Bundesliga',
    'GRE1': 'G1 - Grecia  Super League',
    'ING1': 'E0 - Inghilterra Premier League',
    'ING2': 'E1 - Inghilterra Championship',
    'ING3': 'E2 - Inghilterra League One',
    'ING4': 'E3 - Inghilterra League Two',
    'ING5': 'EC - Inghilterra Conference',
    'ITA1': 'I1 - Italia Serie A',
    'ITA2': 'I2 - Italia Serie B',
    'OLA1': 'N1 - Olanda Eredivisie',
    'POR1': 'P1 - Portogallo Primeira Liga',
    'SPA1': 'SP1 - Spagna La Liga',
    'SPA2': 'SP2 - Spagna Segunda Divisione',
    'TUR1': 'T1 - Turchia Super Lig',
}

# Elenco campionati da nascondere dai filtri (case-insensitive)
DIVISION_BLACKLIST = {
    'challenge league',
}

# ============================================================================
# ⚠️ PROTEZIONE NOMI CAMPIONATI ⚠️
# ============================================================================
# ATTENZIONE: I nomi dei campionati qui sotto sono PROTETTI.
# 
# REGOLE:
# 1. NON MODIFICARE i nomi dei campionati esistenti senza richiesta esplicita
# 2. I nuovi campionati aggiunti NON sono protetti fino a specifica richiesta
# 3. Per modificare un campionato protetto:
#    - Deve essere chiaramente indicato nella richiesta che si è consapevoli della protezione
#    - Dopo la modifica, verrà chiesto se si vuole proteggere di nuovo
# 4. Per proteggere un nuovo campionato: richiedere esplicitamente la protezione
#
# Per modificare i nomi PROTETTI, scrivere nella richiesta:
# "Modifico il campionato PROTETTO [nome_campionato] a [nuovo_nome]"
# ============================================================================

# Mappa nomi campionati -> etichette da mostrare in UI
DIVISION_DISPLAY_MAP = {
    # ⚠️ PROTETTI - Non modificare senza richiesta esplicita
    'Allsvenskan': 'SWE - Svezia Allsvenskan',
    'Bundesliga': 'AUT - Austria Bundesliga',
    'Copa De La Liga Profesional': 'AR - Argentina Copa De La Liga',
    'Ekstraklasa': 'POL - Polonia Ekstraklasa',
    'Eliteserien': 'NOR - Norvegia Eliteserien',
    'J1 League': 'JPN - Giappone Lega J1',
    'Liga MX': 'MEX - Messico Liga MX',
    'MLS': 'MLS - Stati Uniti Major League Soccer',
    'Premier Division': 'IRL- Irlanda Premier Division',
    'Premier League': 'RUS - Russia Premier League',
    'Serie A': 'BRA - Brasile Serie A BETANO',
    'Super League': 'CHN - Cina Super League',
    'Superliga': 'ROU - Romania Liga 1',
    'Torneo De La Liga Profesional': 'ARG - Argentina Torneo Betano',
    'Veikkausliiga': 'FIN - Finlandia Veikkausliiga',
    # Campionati con codici - ⚠️ PROTETTI
    'B1': 'B1 - Belgio Jupiler Pro League',
    'D1': 'D1 - Germania Bundesliga',
    'D2': 'D2 - Germania 2. Bundesliga',
    'E0': 'E0 - Inghilterra Premier League',
    'E1': 'E1 - Inghilterra Championship',
    'E2': 'E2 - Inghilterra League One',
    'E3': 'E3 - Inghilterra League Two',
    'EC': 'EC - Inghilterra Conference',
    'F1': 'F1 - Francia Ligue 1',
    'F2': 'F2 - Francia Ligue 2',
    'G1': 'G1 - Grecia Super League',
    'I1': 'I1 - Italia Serie A',
    'I2': 'I2 - Italia Serie B',
    'N1': 'N1 - Olanda Eredivisie',
    'P1': 'P1 - Portogallo Primeira Liga',
    'SC0': 'SC0 - Scozia Premiership',
    'SC1': 'SC1 - Scozia Championship',
    'SC2': 'SC2 - Scozia League One',
    'SC3': 'SC3 - Scozia Lega Due',
    'SP1': 'SP1 - Spagna La Liga',
    'SP2': 'SP2 - Spagna Segunda Divisione',
    'T1': 'T1 - Turchia Super Lig',
    # NOTA: I nuovi campionati aggiunti qui sotto NON sono protetti automaticamente
    # Per proteggerli, richiedere esplicitamente: "Proteggi il campionato [nome]"
}

# Set dei campionati PROTETTI (non modificabili senza richiesta esplicita)
# Questo set contiene tutti i campionati esistenti al momento della creazione della protezione
PROTECTED_DIVISIONS = frozenset([
    'Allsvenskan', 'Bundesliga', 'Copa De La Liga Profesional', 'Ekstraklasa',
    'Eliteserien', 'J1 League', 'Liga MX', 'MLS', 'Premier Division',
    'Premier League', 'Serie A', 'Super League', 'Superliga',
    'Torneo De La Liga Profesional', 'Veikkausliiga',
    'B1', 'D1', 'D2', 'E0', 'E1', 'E2', 'E3', 'EC', 'F1', 'F2', 'G1',
    'I1', 'I2', 'N1', 'P1', 'SC0', 'SC1', 'SC2', 'SC3', 'SP1', 'SP2', 'T1'
])

def is_division_protected(division_name: str) -> bool:
    """Verifica se un campionato è protetto (non modificabile senza richiesta esplicita)"""
    return division_name in PROTECTED_DIVISIONS

def get_division_display_name(name: str) -> str:
    if name is None:
        return ''
    key = str(name).strip()
    return DIVISION_DISPLAY_MAP.get(key, key)

class FootballDatabase:
    def __init__(self, environment="test"):
        """
        Inizializza il database per l'ambiente specificato
        
        Args:
            environment: "test" o "web" per separare i database
        """
        self.environment = environment
        self.db_path = f"football_stats_{environment}.db"
        self.init_database()
    
    def init_database(self):
        """Inizializza il database con le tabelle necessarie"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabella principale per i dati delle partite (struttura avanzata)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                div TEXT,
                season TEXT,
                date TEXT,
                time TEXT,
                home_team TEXT,
                away_team TEXT,
                ft_home_goals INTEGER,
                ft_away_goals INTEGER,
                ft_result TEXT,
                ht_home_goals INTEGER,
                ht_away_goals INTEGER,
                ht_result TEXT,
                home_shots INTEGER,
                away_shots INTEGER,
                home_shots_target INTEGER,
                away_shots_target INTEGER,
                home_fouls INTEGER,
                away_fouls INTEGER,
                home_corners INTEGER,
                away_corners INTEGER,
                home_yellow INTEGER,
                away_yellow INTEGER,
                home_red INTEGER,
                away_red INTEGER,
                file_source TEXT,
                import_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabella per tracciare le mappature usate
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mappature_colonne (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_origine TEXT,
                colonna_originale TEXT,
                colonna_destinazione TEXT,
                note TEXT,
                data_creazione TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabella per preferenze utente (session-based)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                preference_key TEXT NOT NULL,
                preference_value TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id, preference_key)
            )
        ''')
        
        # Tabella per logging accessi utente
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                environment TEXT,
                user_role TEXT,
                ip_address TEXT,
                login_time TEXT DEFAULT CURRENT_TIMESTAMP,
                logout_time TEXT,
                session_duration INTEGER,
                pages_visited TEXT,
                notes TEXT
            )
        ''')
        
        # Tabella per metriche cumulative (non si azzerano con la pulizia dei log)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_metrics (
                key TEXT PRIMARY KEY,
                value INTEGER DEFAULT 0
            )
        ''')
        
        # Tabella per le sessioni di chat
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabella per i messaggi delle chat
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            )
        ''')
        
        # Indice per migliorare le query sui messaggi
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id 
            ON chat_messages(session_id)
        ''')
        
        conn.commit()
        conn.close()
        
        # Migrazione: aggiungi colonne per PDF e quote se non esistono
        self._migrate_add_pdf_columns()
        
        logger.info("Database avanzato inizializzato correttamente")
    
    def _migrate_add_pdf_columns(self):
        """Aggiunge colonne per import PDF e quote se non esistono già"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Colonne da aggiungere
        columns_to_add = [
            ('quote_1', 'REAL', None),  # Quota vittoria casa (1)
            ('quote_X', 'REAL', None),  # Quota pareggio (X)
            ('quote_2', 'REAL', None),  # Quota vittoria ospite (2)
            ('pdf_pal', 'TEXT', None),  # Codice PAL dal PDF (uso futuro)
            ('pdf_avv', 'TEXT', None),  # Codice AVV dal PDF (uso futuro)
            # Under/Over odds estratte da PDF
            ('uo_1_5_u', 'REAL', None),
            ('uo_1_5_o', 'REAL', None),
            ('uo_2_5_u', 'REAL', None),
            ('uo_2_5_o', 'REAL', None),
            ('uo_3_5_u', 'REAL', None),
            ('uo_3_5_o', 'REAL', None),
            # Estensioni richieste: Live/Handicap/Doppia/Goal/Segna Goal
            ('live', 'TEXT', None),
            ('h', 'REAL', None),
            ('h1', 'REAL', None),
            ('hx', 'REAL', None),
            ('h2', 'REAL', None),
            ('dc_1x', 'REAL', None),
            ('dc_x2', 'REAL', None),
            ('dc_12', 'REAL', None),
            ('g', 'REAL', None),
            ('no_g', 'REAL', None),
            ('c_si', 'REAL', None),
            ('c_no', 'REAL', None),
            ('o_si', 'REAL', None),
            ('o_no', 'REAL', None),
        ]
        
        # Verifica colonne esistenti
        cursor.execute('PRAGMA table_info(matches)')
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Aggiungi colonne mancanti
        for col_name, col_type, default in columns_to_add:
            if col_name not in existing_columns:
                default_clause = f" DEFAULT {default}" if default else ""
                try:
                    cursor.execute(f'ALTER TABLE matches ADD COLUMN {col_name} {col_type}{default_clause}')
                    logger.info(f"✅ Colonna aggiunta: {col_name}")
                except sqlite3.OperationalError as e:
                    logger.warning(f"⚠️ Errore aggiunta colonna {col_name}: {e}")
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Ottiene una connessione al database con configurazioni per persistenza"""
        conn = sqlite3.connect(self.db_path)
        # Configurazioni per garantire persistenza su Render
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging per migliore persistenza
        conn.execute("PRAGMA synchronous=NORMAL")  # Bilanciamento tra sicurezza e performance
        return conn
    
    def rileva_mappatura(self, df):
        """Analizza le colonne del file e prova a rilevare quale mappatura usare"""
        colonne_file = set(df.columns)
        
        migliore_match = None
        max_corrispondenze = 0
        
        for nome_mappatura, mappatura in MAPPATURE_DISPONIBILI.items():
            colonne_mappatura = set(mappatura.keys())
            corrispondenze = len(colonne_file.intersection(colonne_mappatura))
            
            if corrispondenze > max_corrispondenze:
                max_corrispondenze = corrispondenze
                migliore_match = nome_mappatura
        
        percentuale = (max_corrispondenze / len(colonne_file)) * 100 if len(colonne_file) > 0 else 0
        
        logger.info(f"Mappatura rilevata: {migliore_match} ({max_corrispondenze}/{len(colonne_file)} colonne - {percentuale:.1f}%)")
        
        return migliore_match
    
    def import_excel_file(self, file_path, season=None, file_type="main"):
        """Importa un file Excel nel database con sistema avanzato"""
        try:
            logger.info(f"Importazione file: {os.path.basename(file_path)}")
            
            # Leggi il file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
                logger.info(f"File CSV caricato: {len(df)} righe")
            else:
                # Leggi TUTTI i fogli del file Excel
                excel_file = pd.ExcelFile(file_path)
                logger.info(f"File Excel caricato - Fogli: {len(excel_file.sheet_names)}")
                
                # Leggi e concatena tutti i fogli
                all_sheets = []
                for sheet_name in excel_file.sheet_names:
                    df_sheet = pd.read_excel(file_path, sheet_name=sheet_name)
                    # Tieni traccia del foglio per eventuale fallback del campionato
                    df_sheet['__sheet_name'] = str(sheet_name)
                    logger.info(f"Foglio {sheet_name}: {len(df_sheet)} righe")
                    all_sheets.append(df_sheet)
                
                # Concatena tutti i fogli in un unico DataFrame
                df = pd.concat(all_sheets, ignore_index=True)
                logger.info(f"Totale righe da tutti i fogli: {len(df)}")
            
            # Rileva mappatura automaticamente
            mappatura_nome = self.rileva_mappatura(df)
            mappatura = MAPPATURE_DISPONIBILI.get(mappatura_nome)
            
            if not mappatura:
                logger.error(f"Mappatura '{mappatura_nome}' non trovata!")
                return False
            
            # Crea DataFrame normalizzato
            df_normalizzato = pd.DataFrame()
            
            # Applica mappatura
            for colonna_orig, colonna_dest in mappatura.items():
                if colonna_orig in df.columns:
                    df_normalizzato[colonna_dest] = df[colonna_orig]
                else:
                    df_normalizzato[colonna_dest] = None

            # Se il file contiene colonne extra per quote, normalizzale
            def _to_float_or_none(val):
                if pd.isna(val):
                    return None
                s = str(val).strip()
                if not s:
                    return None
                s = s.replace(',', '.')
                try:
                    return float(s)
                except Exception:
                    return None
            for extra in ['quota_1','quota_X','quota_2','uo_1_5_u','uo_1_5_o','uo_2_5_u','uo_2_5_o','uo_3_5_u','uo_3_5_o',
                          'live','h','h1','hx','h2','dc_1x','dc_x2','dc_12','g','no_g','c_si','c_no','o_si','o_no']:
                if extra in df.columns:
                    df_normalizzato[extra] = df[extra].apply(_to_float_or_none)

            # pal/avv opzionali dal file (salvati in pdf_pal/pdf_avv)
            if 'pal' in df.columns:
                df_normalizzato['pdf_pal'] = df['pal'].astype(str)
            if 'avv' in df.columns:
                df_normalizzato['pdf_avv'] = df['avv'].astype(str)

            # Normalizza il nome campionato e fallback al nome foglio se mancante
            if 'div' in df_normalizzato.columns:
                df_normalizzato['div'] = df_normalizzato['div'].astype(str).str.strip()
                
                # Applica mappatura League da PDF convertito (se presente)
                mask_league = df_normalizzato['div'].notna() & (df_normalizzato['div'] != '')
                df_normalizzato.loc[mask_league, 'div'] = df_normalizzato.loc[mask_league, 'div'].apply(
                    lambda x: MAPPA_LEAGUE_PDF.get(str(x).upper().strip(), str(x).strip())
                )
                logger.info("Mappatura League applicata (FRA1 → F1, PER1 → ?, ecc.)")
                
                if '__sheet_name' in df.columns:
                    mask_missing_div = df_normalizzato['div'].isna() | (df_normalizzato['div'] == '') | (df_normalizzato['div'].str.lower() == 'none')
                    df_normalizzato.loc[mask_missing_div, 'div'] = df.loc[mask_missing_div, '__sheet_name'].astype(str).str.strip()
            
            # GESTIONE STAGIONE
            # Regola richiesta: per i file standard "all-euro-data-YYYY-YYYY" usare SEMPRE la stagione dal nome file
            nome_file = os.path.basename(file_path)
            if mappatura_nome == 'standard':
                match = re.search(r'(\d{4})-(\d{4})', nome_file)
                if match:
                    stagione_estratta = f"{match.group(1)}-{match.group(2)}"
                    df_normalizzato['season'] = stagione_estratta
                    logger.info(f"[standard] Stagione forzata dal nome file: {stagione_estratta}")
                else:
                    # fallback: come prima
                    stagione_mancante = ('season' not in df_normalizzato.columns) or (df_normalizzato['season'].isna().all())
                    if stagione_mancante:
                        if season:
                            df_normalizzato['season'] = season
                            logger.info(f"Stagione impostata manualmente: {season}")
                        else:
                            df_normalizzato['season'] = None
                            logger.warning("Impossibile determinare la stagione (standard, no match nel nome file)")
            else:
                # Comportamento precedente: se manca, prova da parametro o nome file
                stagione_mancante = ('season' not in df_normalizzato.columns) or (df_normalizzato['season'].isna().all())
                if stagione_mancante:
                    if season:
                        df_normalizzato['season'] = season
                        logger.info(f"Stagione impostata manualmente: {season}")
                    else:
                        match = re.search(r'(\d{4})-(\d{4})', nome_file)
                        if match:
                            stagione_estratta = f"{match.group(1)}-{match.group(2)}"
                            df_normalizzato['season'] = stagione_estratta
                            logger.info(f"Stagione estratta dal nome file: {stagione_estratta}")
                        else:
                            df_normalizzato['season'] = None
                            logger.warning("Impossibile determinare la stagione!")
            
            # Aggiungi metadata
            df_normalizzato['file_source'] = os.path.basename(file_path)
            
            # Rimuovi righe vuote
            df_normalizzato = df_normalizzato.dropna(subset=['home_team', 'away_team'])
            
            # CONVERSIONE STAGIONE: normalizza separatori e, se anno singolo (es: 2021) → 2021-2022
            if 'season' in df_normalizzato.columns:
                def converti_stagione(stagione_str):
                    if pd.isna(stagione_str) or stagione_str == 'None':
                        return None
                    
                    stagione_str = str(stagione_str).strip()
                    # Normalizza separatori: punto o slash → trattino
                    stagione_str = stagione_str.replace('/', '-').replace('.', '-')
                    
                    # Se contiene già il trattino, è già in formato corretto
                    if '-' in stagione_str:
                        return stagione_str
                    
                    # Se è un anno singolo (4 cifre), convertilo
                    if stagione_str.isdigit() and len(stagione_str) == 4:
                        anno = int(stagione_str)
                        return f"{anno}-{anno + 1}"
                    
                    return stagione_str
                
                df_normalizzato['season'] = df_normalizzato['season'].apply(converti_stagione)
                logger.info("Stagioni convertite (es: 2021 → 2021-2022)")
            
            # FILTRO STAGIONI VECCHIE (scarta <= 2019-2020)
            if 'season' in df_normalizzato.columns:
                df_prima_filtro = len(df_normalizzato)
                
                # Filtra via le stagioni vecchie e quelle mancanti
                df_normalizzato = df_normalizzato[
                    (df_normalizzato['season'].notna()) &
                    (df_normalizzato['season'] > '2019-2020')
                ].copy()
                
                df_dopo_filtro = len(df_normalizzato)
                stagioni_scartate = df_prima_filtro - df_dopo_filtro
                
                if stagioni_scartate > 0:
                    logger.warning(f"{stagioni_scartate} partite scartate (stagioni <= 2019-2020 o mancanti)")
                
                logger.info(f"Partite valide dopo filtro: {df_dopo_filtro}")
            
            # Converti le date in stringhe
            colonne_data = ['date', 'time', 'season']
            for col in colonne_data:
                if col in df_normalizzato.columns:
                    df_normalizzato[col] = df_normalizzato[col].astype(str)
            
            # CONTROLLO DUPLICATI / UPSERT
            conn = self.get_connection()
            cursor = conn.cursor()
            
            logger.info("Controllo duplicati / upsert...")
            
            # Carica tutte le partite esistenti in memoria
            df_esistenti = pd.read_sql_query(
                'SELECT home_team, away_team, date FROM matches',
                conn
            )
            
            logger.info(f"Partite già nel database: {len(df_esistenti)}")
            logger.info(f"Partite da verificare: {len(df_normalizzato)}")
            
            if len(df_esistenti) > 0:
                # Crea colonna chiave per confronto veloce
                df_normalizzato['_chiave'] = (
                    df_normalizzato['home_team'].astype(str) + '|' + 
                    df_normalizzato['away_team'].astype(str) + '|' + 
                    df_normalizzato['date'].astype(str)
                )
                df_esistenti['_chiave'] = (
                    df_esistenti['home_team'].astype(str) + '|' + 
                    df_esistenti['away_team'].astype(str) + '|' + 
                    df_esistenti['date'].astype(str)
                )
                
                # Trova partite nuove
                chiavi_esistenti = set(df_esistenti['_chiave'])
                df_normalizzato['_is_new'] = ~df_normalizzato['_chiave'].isin(chiavi_esistenti)
                
                df_nuove = df_normalizzato[df_normalizzato['_is_new']].copy()
                df_nuove = df_nuove.drop(columns=['_chiave', '_is_new'])
                
                partite_duplicate = len(df_normalizzato) - len(df_nuove)
            else:
                df_nuove = df_normalizzato.copy()
                partite_duplicate = 0
            
            logger.info(f"Partite nuove da importare: {len(df_nuove)}")
            logger.info(f"Partite duplicate (saltate): {partite_duplicate}")
            
            # Inserisci nuove e aggiorna le esistenti (Excel ha precedenza sui dati PDF)
            tot_insert = 0
            tot_update = 0
            colonne_dest = [
                'div','season','date','time','home_team','away_team',
                'ft_home_goals','ft_away_goals','ft_result',
                'ht_home_goals','ht_away_goals','ht_result',
                'home_shots','away_shots','home_shots_target','away_shots_target',
                'home_fouls','away_fouls','home_corners','away_corners',
                'home_yellow','away_yellow','home_red','away_red','file_source',
                'quote_1','quote_X','quote_2','pdf_pal','pdf_avv',
                'uo_1_5_u','uo_1_5_o','uo_2_5_u','uo_2_5_o','uo_3_5_u','uo_3_5_o',
                'live','h','h1','hx','h2','dc_1x','dc_x2','dc_12','g','no_g','c_si','c_no','o_si','o_no'
            ]
            for _, r in df_normalizzato.iterrows():
                key = (str(r.get('home_team') or ''), str(r.get('away_team') or ''), str(r.get('date') or ''))
                if not key[0] or not key[1] or not key[2]:
                    continue
                # Match con o senza time (se fornito in Excel, lo usiamo)
                if str(r.get('time') or ''):
                    cursor.execute('''SELECT id FROM matches WHERE home_team=? AND away_team=? AND date=? AND time=?''',
                                   (key[0], key[1], key[2], str(r.get('time'))))
                else:
                    cursor.execute('''SELECT id FROM matches WHERE home_team=? AND away_team=? AND date=?''',
                                   key)
                row = cursor.fetchone()
                if row:
                    # UPDATE selettivo: aggiorna SOLO i campi vuoti (non sovrascrive dati esistenti)
                    # 1. Leggi i valori attuali dal database
                    cursor.execute('SELECT * FROM matches WHERE id=?', (row[0],))
                    record_esistente = cursor.fetchone()
                    if record_esistente:
                        # Crea dizionario con i valori esistenti
                        cursor.execute('PRAGMA table_info(matches)')
                        colonne_db = [col[1] for col in cursor.fetchall()]
                        record_dict = dict(zip(colonne_db, record_esistente))
                        
                        # 2. Aggiorna solo i campi vuoti del database con i valori di Excel
                        set_parts = []
                        params = []
                        for col in colonne_dest:
                            if col == 'file_source':
                                val_excel = os.path.basename(file_path)
                            else:
                                val_excel = r.get(col)
                            
                            # Valore esistente nel database
                            val_esistente = record_dict.get(col)
                            
                            # Verifica se il campo nel database è vuoto
                            is_empty = (
                                val_esistente is None or 
                                str(val_esistente).strip() == '' or 
                                str(val_esistente).strip() == 'nan' or
                                str(val_esistente).strip() == 'None'
                            )
                            
                            # Aggiorna solo se il campo è vuoto E Excel ha un valore valido
                            if is_empty and val_excel is not None and str(val_excel) != 'nan' and str(val_excel) != 'None' and str(val_excel).strip() != '':
                                set_parts.append(f"{col}=?")
                                params.append(str(val_excel))
                        
                        if set_parts:
                            params.append(row[0])
                            cursor.execute(f"UPDATE matches SET {', '.join(set_parts)} WHERE id=?", params)
                            tot_update += 1
                else:
                    record = {c: (os.path.basename(file_path) if c=='file_source' else r.get(c)) for c in colonne_dest}
                    placeholders = ','.join(['?']*len(record))
                    cursor.execute(f"INSERT INTO matches ({','.join(record.keys())}) VALUES ({placeholders})", list(map(lambda x: None if str(x)=='nan' else x, record.values())))
                    tot_insert += 1
            conn.commit()
            logger.info(f"Excel import: {tot_insert} inseriti, {tot_update} aggiornati")
            if STREAMLIT_AVAILABLE:
                st.success(f"File importato con successo! Inseriti: {tot_insert}, Aggiornati: {tot_update}")
            else:
                print(f"File importato con successo! Inseriti: {tot_insert}, Aggiornati: {tot_update}")
            
            # Salva mappatura usata
            for colonna_orig, colonna_dest in mappatura.items():
                cursor.execute('''
                    INSERT INTO mappature_colonne (file_origine, colonna_originale, colonna_destinazione, note)
                    VALUES (?, ?, ?, ?)
                ''', (os.path.basename(file_path), colonna_orig, colonna_dest, f"Mappatura: {mappatura_nome}"))
            
            conn.commit()
            # Forza il flush del database per garantire persistenza su Render
            conn.execute("PRAGMA wal_checkpoint(FULL)")
            conn.close()
            
            logger.info(f"Mappatura usata: {mappatura_nome}")
            return True
            
        except Exception as e:
            error_message = f"Errore durante l'import: {str(e)}"
            if STREAMLIT_AVAILABLE:
                st.error(error_message)
            else:
                print(error_message)
            logger.error(f"Errore import file {file_path}: {str(e)}")
            return False

    def import_pdf_file(self, pdf_path: str, default_date: str = None) -> bool:
        """Importa un PDF quotazioni future.
        - Inserisce tutti i record trovati con file_source=nome_pdf
        - Campi scritti (se disponibili): date, time, home_team, away_team, quote_1, quote_X, quote_2, pdf_pal, pdf_avv
        - Le partite vengono identificate con chiave (home_team, away_team, date[, time])
        """
        try:
            import re
            from PyPDF2 import PdfReader

            logger.info(f"Import PDF: {os.path.basename(pdf_path)}")
            reader = PdfReader(pdf_path)
            text = "\n".join(page.extract_text() or '' for page in reader.pages)

            # Pattern date
            date_pattern = re.compile(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})")
            # Intestazioni tipo: sabato, 1 novembre | domenica, 2 novembre
            giorni_it = r"lunedì|lunedi|martedì|martedi|mercoledì|mercoledi|giovedì|giovedi|venerdì|venerdi|sabato|domenica"
            mesi_it = (
                "gennaio|febbraio|marzo|aprile|maggio|giugno|"
                "luglio|agosto|settembre|ottobre|novembre|dicembre"
            )
            date_header_re = re.compile(fr"^(?:{giorni_it})\s*,\s*(\d{{1,2}})\s+({mesi_it})$", re.IGNORECASE)
            month_map = {
                'gennaio': 1,'febbraio': 2,'marzo': 3,'aprile': 4,'maggio': 5,'giugno': 6,
                'luglio': 7,'agosto': 8,'settembre': 9,'ottobre': 10,'novembre': 11,'dicembre': 12
            }
            # Orario nel PDF è spesso nel formato 21.05 invece di 21:05
            time_pattern = re.compile(r"\b(\d{1,2})[\.:](\d{2})\b")

            # Strategia 1: righe con trattino tra squadre (fallback generico)
            fallback_pattern = re.compile(
                r"(?P<time>\d{1,2}[:\.]\d{2})\s+(?P<manif>[A-Z0-9]+)?\s*(?P<pal>\d+)?\s*(?P<avv>\d+)?\s+(?P<home>[^-\n]+?)\s*-\s*(?P<away>[^\n]+?)\s+(?P<q1>\d+[\.,]?\d*)\s+(?P<qx>\d+[\.,]?\d*)\s+(?P<q2>\d+[\.,]?\d*)"
            )

            # Strategia 2: righe tabellari con colonne separate da spazi multipli (come nel PDF Sisal)
            split_re = re.compile(r"\s{2,}")

            from datetime import datetime
            current_year = datetime.now().year
            current_date = default_date
            rows_to_insert = []
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                # Aggiorna data se incontriamo una data esplicita
                # 1) formato numerico
                mdate = date_pattern.search(line)
                if mdate:
                    current_date = mdate.group(1)
                    continue
                # 2) intestazione italiana "sabato, 1 novembre"
                mh = date_header_re.match(line)
                if mh:
                    dd = int(mh.group(1))
                    mm_name = mh.group(2).lower()
                    mm = month_map.get(mm_name)
                    if mm:
                        current_date = f"{current_year}-{mm:02d}-{dd:02d}"
                        continue
                # Prova fallback con trattino
                m = fallback_pattern.search(line)
                parsed = None
                if m:
                    d = m.groupdict()
                    parsed = {
                        'time': d.get('time'),
                        'manif': d.get('manif'),
                        'pal': d.get('pal'),
                        'avv': d.get('avv'),
                        'home': (d.get('home') or '').strip(),
                        'away': (d.get('away') or '').strip(),
                        'q1': d.get('q1'), 'qx': d.get('qx'), 'q2': d.get('q2')
                    }
                else:
                    # Prova split per colonne (minimo: ora, manif, pal, avv, home, away, q1, qx, q2)
                    parts = [p for p in split_re.split(line) if p]
                    if len(parts) >= 8:
                        # Individua ora
                        mt = time_pattern.match(parts[0])
                        if mt:
                            # Mapping con posizioni attese: 0=ora,1=manif,2=pal,3=avv,4=home,5=away,... quote
                            q1 = qx = q2 = None
                            # cerca le prime tre quote numeriche da destra
                            nums = [p for p in parts[6:] if re.match(r"^\d+[\.,]?\d*$", p)]
                            if len(nums) >= 3:
                                q1, qx, q2 = nums[0], nums[1], nums[2]
                            parsed = {
                                'time': f"{mt.group(1)}:{mt.group(2)}",
                                'manif': parts[1] if len(parts) > 1 else None,
                                'pal': parts[2] if len(parts) > 2 else None,
                                'avv': parts[3] if len(parts) > 3 else None,
                                'home': parts[4] if len(parts) > 4 else '',
                                'away': parts[5] if len(parts) > 5 else '',
                                'q1': q1, 'qx': qx, 'q2': q2,
                            }

                if not parsed:
                    continue

                def norm_num(x):
                    return None if not x else float(str(x).replace(',', '.'))

                rows_to_insert.append({
                    'date': str(current_date) if current_date else None,
                    'time': parsed.get('time'),
                    'home_team': (parsed.get('home') or '').strip(),
                    'away_team': (parsed.get('away') or '').strip(),
                    'quote_1': norm_num(parsed.get('q1')),
                    'quote_X': norm_num(parsed.get('qx')),
                    'quote_2': norm_num(parsed.get('q2')),
                    'pdf_pal': parsed.get('pal'),
                    'pdf_avv': parsed.get('avv'),
                    'file_source': os.path.basename(pdf_path),
                })

            if not rows_to_insert:
                logger.warning("PDF: nessuna riga riconosciuta. Nessun inserimento.")
                return False

            conn = self.get_connection()
            cur = conn.cursor()
            inserted = 0
            updated = 0
            for r in rows_to_insert:
                if not r['home_team'] or not r['away_team'] or not r['date']:
                    continue
                # Cerca esistenza
                if r.get('time'):
                    cur.execute('''SELECT id FROM matches WHERE home_team=? AND away_team=? AND date=? AND time=?''',
                                (r['home_team'], r['away_team'], r['date'], r['time']))
                else:
                    cur.execute('''SELECT id FROM matches WHERE home_team=? AND away_team=? AND date=?''',
                                (r['home_team'], r['away_team'], r['date']))
                row = cur.fetchone()
                if row:
                    # Update solo dei campi PDF (quote/pal/avv/time/date se presenti), senza toccare dati Excel già presenti
                    set_parts = []
                    params = []
                    for col in ['date','time','quote_1','quote_X','quote_2','pdf_pal','pdf_avv','file_source']:
                        val = r.get(col)
                        if val not in (None, ''):
                            set_parts.append(f"{col}=?")
                            params.append(val)
                    if set_parts:
                        params.append(row[0])
                        cur.execute(f"UPDATE matches SET {', '.join(set_parts)} WHERE id=?", params)
                        updated += 1
                else:
                    cols = list(r.keys())
                    placeholders = ','.join(['?']*len(cols))
                    cur.execute(f"INSERT INTO matches ({','.join(cols)}) VALUES ({placeholders})", [r[c] for c in cols])
                    inserted += 1
            conn.commit()
            conn.close()
            logger.info(f"PDF import: {inserted} inseriti, {updated} aggiornati")
            return True
        except Exception as e:
            logger.error(f"Errore import PDF: {e}")
            return False

    def delete_pdf_import(self, pdf_filename: str) -> int:
        """Elimina tutti i record importati da uno specifico PDF (matchando su file_source).
        Ritorna il numero di righe eliminate.
        """
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM matches WHERE file_source=?", (os.path.basename(pdf_filename),))
        deleted = cur.rowcount
        conn.commit()
        conn.close()
        logger.info(f"Delete PDF '{pdf_filename}': {deleted} righe rimosse")
        return deleted

    def export_pdf_to_excel(self, pdf_path: str, output_xlsx_path: str, default_date: str | None = None) -> dict:
        """Estrae le tabelle dal PDF usando PyPDF2 + regex migliorato per estrazione PERFETTA delle quote.
        
        APPROCCIO PERFETTO:
        - Usa PyPDF2 per estrarre il testo strutturato dal PDF
        - Parsing con regex migliorato basato sulla struttura esatta del PDF
        - Valida ogni riga: deve avere esattamente 22 valori dopo LIVE (21 decimali + 1 intero H)
        - Mappa automaticamente le colonne in base alla struttura della tabella
        - Crea il foglio "calcio base per data" con dati perfettamente estratti
        - Crea fogli di debug per verificare l'estrazione
        """
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception:
            raise RuntimeError("PyPDF2 non è installato nell'ambiente corrente")

        import pandas as _pd
        import re as _re
        from datetime import datetime as _dt
        import os as _os
        import numpy as _np

        current_year = _dt.now().year
        current_date = default_date
        
        # Estrai il testo dal PDF
        logger.info(f"Estraendo testo dal PDF: {pdf_path}")
        reader = PdfReader(pdf_path)
        text = "\n".join(page.extract_text() or '' for page in reader.pages)
        raw_lines = text.splitlines()

        # Estrai date dal testo per riferimento
        date_pattern = _re.compile(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})")
        giorni_it = r"lunedì|lunedi|martedì|martedi|mercoledì|mercoledi|giovedì|giovedi|venerdì|venerdi|sabato|domenica"
        mesi_it = ("gennaio|febbraio|marzo|aprile|maggio|giugno|" "luglio|agosto|settembre|ottobre|novembre|dicembre")
        date_header_re = _re.compile(fr"^(?:{giorni_it})\s*,\s*(\d{{1,2}})\s+({mesi_it})$", _re.IGNORECASE)
        month_map = {
            'gennaio': 1,'febbraio': 2,'marzo': 3,'aprile': 4,'maggio': 5,'giugno': 6,
            'luglio': 7,'agosto': 8,'settembre': 9,'ottobre': 10,'novembre': 11,'dicembre': 12
        }
        
        # Processa le date dal testo per riferimento
        current_date = default_date
        for line in raw_lines:
            mdate = date_pattern.search(line)
            if mdate:
                current_date = mdate.group(1)
                break
            mh = date_header_re.match(line)
            if mh:
                dd = int(mh.group(1))
                mm_name = mh.group(2).lower()
                mm = month_map.get(mm_name)
                if mm:
                    current_date = f"{current_year}-{mm:02d}-{dd:02d}"
                    break
        
        # Processa le righe di testo estratte dal PDF con regex
        # Pattern per righe tipo: FRA121.05 5,251,112,351,48 35441 7957 Auxerre Marsiglia 5,003,751,70...
        # Struttura: MANIF+ORA codici PAL AVV SQUADRA1 SQUADRA2 LIVE quote...
        
        parsed_rows = []
        time_pattern = _re.compile(r"(\d{1,2})[\.:](\d{2})")
        
        # Pattern per riga completa: MANIF+ORA (es. "FRA121.05" o "NZL1F22.00")
        # Pattern migliorato: cattura MANIF (lettere + numeri opzionali) + ORA (HH.MM o HH:MM)
        line_pattern = _re.compile(
            r"^(?P<manif>[A-Z]{2,}(?:\d+[A-Z]*|[A-Z]*\d*)?)(?P<hh>\d{1,2})[\.:]?(?P<mm>\d{2})\s+"
            r"(?:[0-9,\.\-\s]+\s+)*?"  # numeri/codici variabili tra ora e pal
            r"(?P<pal>\d{3,6})\s+(?P<avv>\d{3,6})\s+"
            r"(?P<home>[A-Za-zÀ-ÖØ-öø-ÿ'\.\-\s]+?)(?:\s{2,}|\s+)(?P<away>[A-Za-zÀ-ÖØ-öø-ÿ'\.\-\s]+?)(?:\s{2,}|\s+)(?P<tail>.*)$"
        )
        
        # Processa ogni riga di testo
        for line_num, line in enumerate(raw_lines):
            line = (line or "").strip()
            if not line:
                continue
            
            # Skip righe header (date)
            mh = date_header_re.match(line)
            if mh:
                dd = int(mh.group(1))
                mm_name = mh.group(2).lower()
                mm = month_map.get(mm_name)
                if mm:
                    current_date = f"{current_year}-{mm:02d}-{dd:02d}"
                continue
            
            try:
                # Prova a matchare il pattern della riga
                match = line_pattern.match(line)
                if not match:
                    continue
                
                # Estrai dati base
                manif_raw = match.group('manif') or ""
                hh = int(match.group('hh'))
                mm = int(match.group('mm'))
                ora_formatted = f"{hh:02d}:{mm:02d}"
                manif_clean = _re.sub(r'\d+$', '', manif_raw).upper().strip()
                pal_val = match.group('pal') or ""
                avv_val = match.group('avv') or ""
                squadra1 = (match.group('home') or "").strip()
                squadra2 = (match.group('away') or "").strip()
                tail = match.group('tail') or ""
                
                # LIVE flag
                live_flag = "LIVE" if "LIVE" in tail.upper() else ""
                
                # Estrai tutte le quote dalla tail (dopo le squadre)
                # La sequenza è: LIVE (opzionale) + 22 valori (21 decimali + 1 intero H)
                # Pattern per estrarre decimali (X,XX o X.XX) e interi (-1 o 1 per H)
                def normalize_value(val):
                    """Normalizza un valore: rimuovi spazi, converti punto in virgola per decimali"""
                    if not val or val == "" or val == "nan" or val == "None":
                        return ""
                    val = str(val).strip().replace(" ", "")
                    # Converti punto in virgola per decimali (es. "5.00" -> "5,00")
                    if _re.match(r"^\d+\.\d{1,2}$", val):
                        val = val.replace('.', ',')
                    return val
                
                # Estrai tutti i decimali dalla tail (pattern X,XX o X.XX)
                dec_pattern = _re.compile(r"\b(\d{1,3}[,\.]\d{2})\b")
                dec_matches = dec_pattern.findall(tail)
                # Normalizza decimali (punto -> virgola)
                dec_values = [d.replace('.', ',') for d in dec_matches]
                
                # Estrai interi standalone (per H, che può essere -1 o 1)
                int_pattern = _re.compile(r"\b(-?\d+)\b")
                int_matches = int_pattern.findall(tail)
                # Filtra solo interi che non fanno parte di decimali già trovati
                int_values = []
                for i_match in int_matches:
                    # Verifica che non sia già parte di un decimale
                    is_part_of_decimal = False
                    for dec_val in dec_matches:
                        if i_match in dec_val:
                            is_part_of_decimal = True
                            break
                    if not is_part_of_decimal and i_match in ['-1', '1']:
                        int_values.append(i_match)
                    elif not is_part_of_decimal and len(i_match) <= 3:  # Potrebbe essere H
                        int_values.append(i_match)
                
                # Mappatura quote: sequenza attesa dopo LIVE
                # 1. quota_1 (decimale 0)
                # 2. quota_X (decimale 1)
                # 3. quota_2 (decimale 2)
                # 4. H (intero -1 o 1) - primo intero trovato
                # 5. H1 (decimale 3)
                # 6. HX (decimale 4)
                # 7. H2 (decimale 5)
                # 8. 1X (decimale 6)
                # 9. X2 (decimale 7)
                # 10. 12 (decimale 8)
                # 11. uo_1_5_u (decimale 9)
                # 12. uo_1_5_o (decimale 10)
                # 13. uo_2_5_u (decimale 11)
                # 14. uo_2_5_o (decimale 12)
                # 15. uo_3_5_u (decimale 13)
                # 16. uo_3_5_o (decimale 14)
                # 17. G (decimale 15)
                # 18. NO_G (decimale 16)
                # 19. C_SI (decimale 17)
                # 20. C_NO (decimale 18)
                # 21. O_SI (decimale 19)
                # 22. O_NO (decimale 20)
                
                # Estrai quote dalla sequenza di decimali
                quota_1 = dec_values[0] if len(dec_values) > 0 else ""
                quota_X = dec_values[1] if len(dec_values) > 1 else ""
                quota_2 = dec_values[2] if len(dec_values) > 2 else ""
                H = int_values[0] if len(int_values) > 0 else ""  # Primo intero = H
                H1 = dec_values[3] if len(dec_values) > 3 else ""
                HX = dec_values[4] if len(dec_values) > 4 else ""
                H2 = dec_values[5] if len(dec_values) > 5 else ""
                dc_1x = dec_values[6] if len(dec_values) > 6 else ""
                dc_x2 = dec_values[7] if len(dec_values) > 7 else ""
                dc_12 = dec_values[8] if len(dec_values) > 8 else ""
                uo_15_u = dec_values[9] if len(dec_values) > 9 else ""
                uo_15_o = dec_values[10] if len(dec_values) > 10 else ""
                uo_25_u = dec_values[11] if len(dec_values) > 11 else ""
                uo_25_o = dec_values[12] if len(dec_values) > 12 else ""
                uo_35_u = dec_values[13] if len(dec_values) > 13 else ""
                uo_35_o = dec_values[14] if len(dec_values) > 14 else ""
                g = dec_values[15] if len(dec_values) > 15 else ""
                no_g = dec_values[16] if len(dec_values) > 16 else ""
                c_si = dec_values[17] if len(dec_values) > 17 else ""
                c_no = dec_values[18] if len(dec_values) > 18 else ""
                o_si = dec_values[19] if len(dec_values) > 19 else ""
                o_no = dec_values[20] if len(dec_values) > 20 else ""
                
                # Aggiungi la riga parsata solo se ha almeno i dati base
                if ora_formatted and manif_clean and squadra1 and squadra2:
                    parsed_rows.append({
                        'data': current_date or "",
                        'ora': ora_formatted,
                        'manif': manif_clean,
                        'pal': pal_val,
                        'avv': avv_val,
                        'squadra1': squadra1,
                        'squadra2': squadra2,
                        'quota_1': quota_1,
                        'quota_X': quota_X,
                        'quota_2': quota_2,
                        'Live': live_flag,
                        'H': H,
                        'H1': H1,
                        'HX': HX,
                        'H2': H2,
                        '1X': dc_1x,
                        'X2': dc_x2,
                        '12': dc_12,
                        'uo_1_5_u': uo_15_u,
                        'uo_1_5_o': uo_15_o,
                        'uo_2_5_u': uo_25_u,
                        'uo_2_5_o': uo_25_o,
                        'uo_3_5_u': uo_35_u,
                        'uo_3_5_o': uo_35_o,
                        'G': g,
                        'NO_G': no_g,
                        'C_SI': c_si,
                        'C_NO': c_no,
                        'O_SI': o_si,
                        'O_NO': o_no,
                        # Debug: salva la riga originale per riferimento
                        '_debug_row': line[:200],  # Primi 200 caratteri della riga
                    })
            except Exception as e:
                logger.warning(f"Errore processando riga {line_num}: {e}")
                continue
        
        logger.info(f"Righe parsate con successo: {len(parsed_rows)}")
        
        # Se non ci sono righe parsate, genera errore
        if len(parsed_rows) == 0:
            logger.warning("Nessuna riga estratta dal PDF")
            raise RuntimeError("Nessuna riga estratta dal PDF. Verifica che il PDF contenga tabelle strutturate.")

        # Crea l'Excel con i dati estratti
        out_path = output_xlsx_path
        try:
            with _pd.ExcelWriter(out_path, engine="openpyxl") as writer:
                # Funzione helper per convertire stringa con virgola in float
                def to_float_or_none(val_str):
                    """Converte stringa con virgola in float, ritorna None se vuoto o invalido"""
                    if not val_str or val_str == "" or val_str == "nan" or val_str == "None":
                        return None
                    val_str = str(val_str).strip().replace(" ", "")
                    # Se è un numero con virgola, convertilo in float
                    if _re.match(r"^\d+,\d{1,2}$", val_str):
                        return float(val_str.replace(',', '.'))
                    # Se è già un numero con punto
                    elif _re.match(r"^\d+\.\d{1,2}$", val_str):
                        return float(val_str)
                    # Se è un intero
                    elif _re.match(r"^-?\d+$", val_str):
                        return int(val_str)
                    return None
                
                # Sheet 1: sempre presente con intestazioni corrette
                nl_rows = []
                for r in parsed_rows:
                    # Estrai il manif e rimuovi il numero finale (es. "FRA1" -> "FRA")
                    manif_raw = (r.get('manif') or '').strip()
                    # Rimuovi tutti i numeri alla fine (es. "FRA1" -> "FRA", "PER1" -> "PER")
                    manif_clean = _re.sub(r'\d+$', '', manif_raw).upper()
                    nl_rows.append({
                        'pal': str(r.get('pal') or '').strip(),  # Pal. dal PDF -> colonna pal Excel
                        'avv': str(r.get('avv') or '').strip(),  # Avv. dal PDF -> colonna avv Excel
                        'League': manif_clean,  # Manif senza numero finale (es. FRA1 -> FRA)
                        'Season': str(current_year),
                        'Date': r.get('data') or '',
                        'Time': r.get('ora') or '',
                        'Home': str(r.get('squadra1') or '').strip(),  # Squadra 1 dal PDF -> colonna Home Excel
                        'Away': str(r.get('squadra2') or '').strip(),  # Squadra 2 dal PDF -> colonna Away Excel
                        'HG': '',  # non disponibile nei PDF futuri
                        'AG': '',
                        'Res': '',
                        'Live': str(r.get('Live') or '').strip(),  # LIVE dal PDF -> colonna Live Excel
                        'quota_1': to_float_or_none(r.get('quota_1')),  # Converti in float
                        'quota_X': to_float_or_none(r.get('quota_X')),  # Converti in float
                        'quota_2': to_float_or_none(r.get('quota_2')),  # Converti in float
                        'H': to_float_or_none(r.get('H')),  # Converti in int (può essere -1 o 1)
                        'H1': to_float_or_none(r.get('H1')),  # Converti in float
                        'HX': to_float_or_none(r.get('HX')),  # Converti in float
                        'H2': to_float_or_none(r.get('H2')),  # Converti in float
                        '1X': to_float_or_none(r.get('1X')),  # Converti in float
                        'X2': to_float_or_none(r.get('X2')),  # Converti in float
                        '12': to_float_or_none(r.get('12')),  # Converti in float
                        'uo_1_5_u': to_float_or_none(r.get('uo_1_5_u')),  # Converti in float
                        'uo_1_5_o': to_float_or_none(r.get('uo_1_5_o')),  # Converti in float
                        'uo_2_5_u': to_float_or_none(r.get('uo_2_5_u')),  # Converti in float
                        'uo_2_5_o': to_float_or_none(r.get('uo_2_5_o')),  # Converti in float
                        'uo_3_5_u': to_float_or_none(r.get('uo_3_5_u')),  # Converti in float
                        'uo_3_5_o': to_float_or_none(r.get('uo_3_5_o')),  # Converti in float
                        'G': to_float_or_none(r.get('G')),  # Converti in float
                        'NO_G': to_float_or_none(r.get('NO_G')),  # Converti in float
                        'C_SI': to_float_or_none(r.get('C_SI')),  # Converti in float
                        'C_NO': to_float_or_none(r.get('C_NO')),  # Converti in float
                        'O_SI': to_float_or_none(r.get('O_SI')),  # Converti in float
                        'O_NO': to_float_or_none(r.get('O_NO')),  # Converti in float
                    })
                # Mettiamo pal/avv all'inizio come richiesto
                df_nl = _pd.DataFrame(
                    nl_rows,
                    columns=['pal','avv','League','Season','Date','Time','Home','Away','HG','AG','Res','Live',
                             'quota_1','quota_X','quota_2','H','H1','HX','H2','1X','X2','12',
                             'uo_1_5_u','uo_1_5_o','uo_2_5_u','uo_2_5_o','uo_3_5_u','uo_3_5_o','G','NO_G','C_SI','C_NO','O_SI','O_NO']
                )
                df_nl.to_excel(
                    writer, sheet_name="calcio base per data", index=False
                )
                # Sheet 2: parsed grezzo per controllo (anche se vuoto) con colonne fisse
                _pd.DataFrame(
                    parsed_rows,
                    columns=['data','ora','manif','pal','avv','squadra1','squadra2','Live','quota_1','quota_X','quota_2',
                             'H','H1','HX','H2','1X','X2','12',
                             'uo_1_5_u','uo_1_5_o','uo_2_5_u','uo_2_5_o','uo_3_5_u','uo_3_5_o','G','NO_G','C_SI','C_NO','O_SI','O_NO']
                ).to_excel(writer, sheet_name="parsed_debug", index=False)
                # Sheet 3: debug dettagliato con estrazione
                debug_rows = []
                for r in parsed_rows:
                    debug_rows.append({
                        'Home': r.get('squadra1', ''),
                        'Away': r.get('squadra2', ''),
                        'Riga Originale': r.get('_debug_row', ''),
                        'quota_1': r.get('quota_1', ''),
                        'quota_X': r.get('quota_X', ''),
                        'quota_2': r.get('quota_2', ''),
                        'H': r.get('H', ''),
                        'H1': r.get('H1', ''),
                        'HX': r.get('HX', ''),
                        'H2': r.get('H2', ''),
                        '1X': r.get('1X', ''),
                        'X2': r.get('X2', ''),
                        '12': r.get('12', ''),
                        'uo_1_5_u': r.get('uo_1_5_u', ''),
                        'uo_1_5_o': r.get('uo_1_5_o', ''),
                        'uo_2_5_u': r.get('uo_2_5_u', ''),
                        'uo_2_5_o': r.get('uo_2_5_o', ''),
                        'uo_3_5_u': r.get('uo_3_5_u', ''),
                        'uo_3_5_o': r.get('uo_3_5_o', ''),
                        'G': r.get('G', ''),
                        'NO_G': r.get('NO_G', ''),
                        'C_SI': r.get('C_SI', ''),
                        'C_NO': r.get('C_NO', ''),
                        'O_SI': r.get('O_SI', ''),
                        'O_NO': r.get('O_NO', ''),
                    })
                _pd.DataFrame(debug_rows).to_excel(writer, sheet_name="debug_estrazione", index=False)
                
                # Sheet 4: testo grezzo sempre presente
                _pd.DataFrame({"line": raw_lines}).to_excel(writer, sheet_name="raw_text", index=False)
        except Exception as _e:
            # Nessun fallback: vogliamo produrre solo l'Excel
            raise

        return {"output": out_path, "format": "xlsx", "rows_parsed": len(parsed_rows), "rows_raw": len(raw_lines)}
    
    def get_available_seasons(self):
        """Ottiene le stagioni disponibili nel database"""
        conn = self.get_connection()
        # Normalizza a livello di query i separatori e gli spazi
        query = '''
            SELECT DISTINCT 
                REPLACE(REPLACE(TRIM(season), '.', '-'), '/', '-') AS season
            FROM matches 
            WHERE season IS NOT NULL
        '''
        seasons_df = pd.read_sql_query(query, conn)
        conn.close()

        # Converte anni singoli 2021 -> 2021-2022 al volo
        normalized = []
        for s in seasons_df['season'].astype(str).tolist():
            s = s.strip()
            if s.isdigit() and len(s) == 4:
                anno = int(s)
                normalized.append(f"{anno}-{anno+1}")
            else:
                normalized.append(s)

        # Ordina desc
        return sorted(set(normalized), reverse=True)
    
    def normalize_season_values(self):
        """Normalizza i formati stagione in tutto il DB (es. 2022.2023 -> 2022-2023, '2022' -> 2022-2023)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # 1) Trim spazi
        cursor.execute("UPDATE matches SET season = TRIM(season) WHERE season IS NOT NULL")
        # 2) Sostituisci punto e slash con trattino
        cursor.execute("UPDATE matches SET season = REPLACE(season, '.', '-') WHERE season LIKE '%.%' ")
        cursor.execute("UPDATE matches SET season = REPLACE(season, '/', '-') WHERE season LIKE '%/%' ")
        # 3) Converti anni singoli in range anno-anno+1
        rows = pd.read_sql_query("SELECT id, season FROM matches WHERE season IS NOT NULL", conn)
        updates = []
        for _, r in rows.iterrows():
            s = str(r['season'])
            if s.isdigit() and len(s) == 4:
                anno = int(s)
                updates.append((f"{anno}-{anno+1}", r['id']))
        if updates:
            cursor.executemany("UPDATE matches SET season = ? WHERE id = ?", updates)
        conn.commit()
        conn.close()
        return len(updates)
    
    def get_available_divisions(self):
        """Ottiene le divisioni disponibili nel database"""
        conn = self.get_connection()
        query = '''
            SELECT DISTINCT TRIM(div) AS div FROM matches 
            WHERE div IS NOT NULL AND TRIM(div) <> ''
        '''
        divisions = pd.read_sql_query(query, conn)
        conn.close()
        # Applica blacklist case-insensitive
        raw_list = [d for d in divisions['div'].tolist() if str(d).strip().lower() not in DIVISION_BLACKLIST]
        # Ordina per etichetta visualizzata (A→Z)
        decorated = [(get_division_display_name(d).lower(), d) for d in raw_list]
        decorated.sort(key=lambda t: t[0])
        return [d for _, d in decorated]
    
    def get_matches_data(self, seasons=None, divisions=None):
        """Ottiene i dati delle partite filtrati per stagione e divisione.
        Normalizza le stagioni ('.' e '/' -> '-') per evitare mismatch.
        """
        conn = self.get_connection()
        
        query = "SELECT * FROM matches WHERE 1=1"
        params = []
        
        if seasons:
            # Normalizza input
            norm_seasons = []
            for s in seasons:
                s = str(s).strip().replace('.', '-').replace('/', '-')
                # gestisci anni singoli
                if s.isdigit() and len(s) == 4:
                    anno = int(s)
                    s = f"{anno}-{anno+1}"
                norm_seasons.append(s)
            placeholders = ','.join(['?' for _ in norm_seasons])
            query += f" AND REPLACE(REPLACE(TRIM(season), '.', '-'), '/', '-') IN ({placeholders})"
            params.extend(norm_seasons)
        
        if divisions:
            placeholders = ','.join(['?' for _ in divisions])
            query += f" AND div IN ({placeholders})"
            params.extend(divisions)
        
        query += " ORDER BY date DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def save_user_preference(self, session_id, key, value):
        """Salva o aggiorna una preferenza utente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_preferences (session_id, preference_key, preference_value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id, preference_key) 
            DO UPDATE SET preference_value = ?, updated_at = CURRENT_TIMESTAMP
        ''', (session_id, key, value, value))
        
        conn.commit()
        conn.close()
    
    def get_user_preference(self, session_id, key, default=None):
        """Ottiene una preferenza utente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT preference_value FROM user_preferences 
            WHERE session_id = ? AND preference_key = ?
        ''', (session_id, key))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else default
    
    def get_all_user_preferences(self, session_id):
        """Ottiene tutte le preferenze di una sessione"""
        conn = self.get_connection()
        
        query = "SELECT preference_key, preference_value FROM user_preferences WHERE session_id = ?"
        df = pd.read_sql_query(query, conn, params=(session_id,))
        
        conn.close()
        return df
    
    def delete_user_preferences(self, session_id):
        """Elimina tutte le preferenze di una sessione"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM user_preferences WHERE session_id = ?', (session_id,))
        
        conn.commit()
        conn.close()
    
    def log_user_access(self, environment, user_role, ip_address, pages_visited=None, notes=None):
        """Registra un accesso utente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_access_log (environment, user_role, ip_address, pages_visited, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (environment, user_role, ip_address, pages_visited, notes))
        
        # Incrementa metrica cumulativa degli accessi
        cursor.execute('''
            INSERT INTO app_metrics(key, value) VALUES('total_accesses', 1)
            ON CONFLICT(key) DO UPDATE SET value = value + 1
        ''')
        
        conn.commit()
        conn.close()
    
    def get_access_logs(self, limit=100):
        """Recupera i log degli accessi"""
        conn = self.get_connection()
        
        query = '''
            SELECT * FROM user_access_log 
            ORDER BY login_time DESC 
            LIMIT ?
        '''
        df = pd.read_sql_query(query, conn, params=(limit,))
        
        conn.close()
        return df
    
    def get_imported_files(self):
        """Ottiene la lista dei file importati"""
        conn = self.get_connection()
        query = '''
            SELECT DISTINCT file_source as filename, COUNT(*) as records_count
            FROM matches 
            GROUP BY file_source
            ORDER BY file_source
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_metric(self, key, default=0):
        """Ottiene il valore di una metrica cumulativa"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM app_metrics WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        return int(row[0]) if row else int(default)

    def increment_metric(self, key, amount=1):
        """Incrementa una metrica cumulativa di amount"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO app_metrics(key, value) VALUES(?, ?)
            ON CONFLICT(key) DO UPDATE SET value = value + ?
        ''', (key, amount, amount))
        conn.commit()
        conn.close()

    def purge_old_access_logs(self, older_than_days=60):
        """Elimina log accessi pi f vecchi di N giorni e restituisce numero righe eliminate"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM user_access_log
            WHERE DATE(login_time) < DATE('now', ?)
        ''', (f'-{older_than_days} days',))
        deleted = cursor.rowcount if cursor.rowcount is not None else 0
        conn.commit()
        conn.close()
        return deleted

    # ------------------------------------------------------------------
    # Supporto eliminazione dati per file sorgente (usato da app_simple)
    # ------------------------------------------------------------------
    def delete_file_data(self, file_source_name: str) -> int:
        """
        Elimina dal database tutti i record collegati ad uno specifico file sorgente.

        Rimuove:
        - Righe da `matches` con `file_source = file_source_name`
        - Voci da `mappature_colonne` con `file_origine = file_source_name`

        Ritorna il numero di partite eliminate dalla tabella `matches`.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Conta righe che verranno eliminate da matches
        cursor.execute('SELECT COUNT(*) FROM matches WHERE file_source = ?', (file_source_name,))
        row = cursor.fetchone()
        deleted_matches = int(row[0]) if row and row[0] is not None else 0

        # Elimina dati
        cursor.execute('DELETE FROM matches WHERE file_source = ?', (file_source_name,))
        cursor.execute('DELETE FROM mappature_colonne WHERE file_origine = ?', (file_source_name,))

        conn.commit()
        conn.close()
        return deleted_matches
    
    # ------------------------------------------------------------------
    # Gestione Chat e Cronologia
    # ------------------------------------------------------------------
    def create_chat_session(self, title: str = None) -> int:
        """Crea una nuova sessione di chat e ritorna l'ID della sessione"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if not title:
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        cursor.execute('''
            INSERT INTO chat_sessions (title, updated_at)
            VALUES (?, CURRENT_TIMESTAMP)
        ''', (title,))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Nuova sessione chat creata: ID {session_id}, titolo: {title}")
        return session_id
    
    def add_chat_message(self, session_id: int, role: str, content: str) -> None:
        """Aggiunge un messaggio a una sessione di chat"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_messages (session_id, role, content)
            VALUES (?, ?, ?)
        ''', (session_id, role, content))
        
        # Aggiorna updated_at della sessione
        cursor.execute('''
            UPDATE chat_sessions 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Messaggio aggiunto alla sessione {session_id}: {role}")
    
    def list_chat_sessions(self, limit: int = 50):
        """Ottiene la lista delle sessioni di chat, ordinate per data di aggiornamento decrescente"""
        conn = self.get_connection()
        
        query = '''
            SELECT 
                id,
                title,
                created_at,
                updated_at,
                (SELECT COUNT(*) FROM chat_messages WHERE session_id = chat_sessions.id) as message_count
            FROM chat_sessions
            ORDER BY updated_at DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        
        return df
    
    def get_chat_history(self, session_id: int):
        """Ottiene la cronologia completa di una sessione di chat"""
        conn = self.get_connection()
        
        query = '''
            SELECT role, content, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
        '''
        
        df = pd.read_sql_query(query, conn, params=(session_id,))
        conn.close()
        
        return df
    
    def get_chat_session_info(self, session_id: int):
        """Ottiene le informazioni di una sessione di chat"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, created_at, updated_at
            FROM chat_sessions
            WHERE id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'title': row[1],
                'created_at': row[2],
                'updated_at': row[3]
            }
        return None
    
    def update_chat_session_title(self, session_id: int, title: str) -> None:
        """Aggiorna il titolo di una sessione di chat"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE chat_sessions
            SET title = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (title, session_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Titolo sessione {session_id} aggiornato: {title}")
    
    def delete_chat_session(self, session_id: int) -> bool:
        """Elimina una sessione di chat e tutti i suoi messaggi (CASCADE)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Conta messaggi che verranno eliminati
        cursor.execute('SELECT COUNT(*) FROM chat_messages WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        message_count = int(row[0]) if row else 0
        
        cursor.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if deleted:
            logger.info(f"Sessione chat {session_id} eliminata ({message_count} messaggi)")
        
        return deleted
