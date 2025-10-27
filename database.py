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
            
            # ESTRAI STAGIONE
            stagione_mancante = ('season' not in df_normalizzato.columns) or (df_normalizzato['season'].isna().all())
            
            if stagione_mancante:
                if season:
                    df_normalizzato['season'] = season
                    logger.info(f"Stagione impostata manualmente: {season}")
                else:
                    # Estrai stagione dal nome del file
                    nome_file = os.path.basename(file_path)
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
            
            # CONVERSIONE STAGIONE: se è anno singolo (es: 2021) → convertilo in 2021-2022
            if 'season' in df_normalizzato.columns:
                def converti_stagione(stagione_str):
                    if pd.isna(stagione_str) or stagione_str == 'None':
                        return None
                    
                    stagione_str = str(stagione_str).strip()
                    
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
        query = '''
            SELECT DISTINCT season FROM matches 
            WHERE season IS NOT NULL 
            ORDER BY season DESC
        '''
        seasons = pd.read_sql_query(query, conn)
        conn.close()
        return seasons['season'].tolist()
    
    def get_available_divisions(self):
        """Ottiene le divisioni disponibili nel database"""
        conn = self.get_connection()
        query = '''
            SELECT DISTINCT div FROM matches 
            WHERE div IS NOT NULL 
            ORDER BY div
        '''
        divisions = pd.read_sql_query(query, conn)
        conn.close()
        return divisions['div'].tolist()
    
    def get_matches_data(self, seasons=None, divisions=None):
        """Ottiene i dati delle partite filtrati per stagione e divisione"""
        conn = self.get_connection()
        
        query = "SELECT * FROM matches WHERE 1=1"
        params = []
        
        if seasons:
            placeholders = ','.join(['?' for _ in seasons])
            query += f" AND season IN ({placeholders})"
            params.extend(seasons)
        
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
