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
        logger.info("Database avanzato inizializzato correttamente")
    
    def get_connection(self):
        """Ottiene una connessione al database"""
        return sqlite3.connect(self.db_path)
    
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

            # Normalizza il nome campionato e fallback al nome foglio se mancante
            if 'div' in df_normalizzato.columns:
                df_normalizzato['div'] = df_normalizzato['div'].astype(str).str.strip()
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
            
            # CONTROLLO DUPLICATI
            conn = self.get_connection()
            cursor = conn.cursor()
            
            logger.info("Controllo duplicati...")
            
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
            
            # Salva solo le partite nuove
            if len(df_nuove) > 0:
                df_nuove.to_sql('matches', conn, if_exists='append', index=False)
                logger.info(f"{len(df_nuove)} partite importate nel database")
                
                success_message = f"File importato con successo! {len(df_nuove)} record aggiunti."
                if STREAMLIT_AVAILABLE:
                    st.success(success_message)
                else:
                    print(success_message)
            else:
                logger.warning("Nessuna partita nuova da importare (tutte duplicate)")
                if STREAMLIT_AVAILABLE:
                    st.warning("Nessuna partita nuova da importare (tutte duplicate)")
                else:
                    print("Nessuna partita nuova da importare (tutte duplicate)")
            
            # Salva mappatura usata
            for colonna_orig, colonna_dest in mappatura.items():
                cursor.execute('''
                    INSERT INTO mappature_colonne (file_origine, colonna_originale, colonna_destinazione, note)
                    VALUES (?, ?, ?, ?)
                ''', (os.path.basename(file_path), colonna_orig, colonna_dest, f"Mappatura: {mappatura_nome}"))
            
            conn.commit()
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
