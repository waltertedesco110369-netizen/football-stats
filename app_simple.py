import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import os
import json
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

from database import FootballDatabase
from stats_calculator import FootballStatsCalculator

def run_app(environment="test"):
    """Funzione principale per eseguire l'app con ambiente specifico"""

    # CSS personalizzato per ridurre il padding superiore e alzare tutta la videata
    st.markdown(
    """
    <style>
    .stApp {
        padding-top: 0.5rem !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    .main .block-container {
        padding-top: 1rem !important;
    }
    .stSidebar {
        padding-top: 1rem !important;
    }
    .stMultiSelect, .stSelectbox {
        width: 150px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Funzione helper per gestire i filtri stagioni con multiselect e default alla stagione più recente
def get_season_filters(seasons, key_prefix="seasons"):
    """Crea filtri stagioni con multiselect e default alla stagione più recente"""
    if not seasons:
        return []
    
    # Ordina le stagioni e prendi l'ultima (più recente)
    seasons_sorted = sorted(seasons)
    default_season = seasons_sorted[-1]
    
    # Inizializza session state se non esiste O se la stagione selezionata non è più valida
    if f'{key_prefix}_selected' not in st.session_state:
        st.session_state[f'{key_prefix}_selected'] = [default_season]
    elif not st.session_state[f'{key_prefix}_selected'] or st.session_state[f'{key_prefix}_selected'][0] != default_season:
        # Se la stagione salvata non è più la più recente, aggiorna
        st.session_state[f'{key_prefix}_selected'] = [default_season]
    
    # Usa multiselect con checkbox visibili
    selected_seasons = st.multiselect(
        "Stagioni",
        seasons_sorted,
        default=st.session_state[f'{key_prefix}_selected'],
        key=f"{key_prefix}_multiselect"
    )
    
    # Aggiorna session state
    if selected_seasons:
        st.session_state[f'{key_prefix}_selected'] = selected_seasons
    else:
        st.session_state[f'{key_prefix}_selected'] = [default_season]
    
    return selected_seasons

# Funzioni per gestire la persistenza della configurazione
def load_divisions_config():
    """Carica la configurazione dei campionati da file"""
    config_file = "divisions_config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_divisions_config(config):
    """Salva la configurazione dei campionati su file"""
    config_file = "divisions_config.json"
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Errore nel salvare la configurazione: {e}")

# Configurazione pagina
st.set_page_config(
    page_title="Football Stats App",

    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CONFIGURAZIONE AUTENTICAZIONE (DOPO ZONA PROTETTA - riga 106+)
# ============================================================================
# Valori di default per ambiente TEST; possono essere sovrascritti da variabili d'ambiente
APP_ENV = os.getenv("APP_ENV", "test").lower()  # Possibili valori: test | web | mobile
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "False").lower() == "true"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # Password amministratore
GUEST_PASSWORD = os.getenv("GUEST_PASSWORD", "guest")  # Password ospite

def check_authentication(db=None):
    """Gestisce autenticazione utente"""
    if not AUTH_ENABLED:
        # Ambiente TEST: nessun autenticazione
        return "admin"
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.login_error = None
    
    if not st.session_state.authenticated:
        # Mostra form di login
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔐 Login")
            
            # Menu per scegliere tipo utente
            selected_role = st.radio("Seleziona tipo utente:", ["👤 Ospite", "🔑 Amministratore"], key="role_selector")
            
            # Campo password unico che funziona con Invio
            password = st.text_input("Password", type="password", key="password_input")
            
            # Controlla automaticamente quando viene inserita la password
            if password:
                if selected_role == "👤 Ospite":
                    if password == GUEST_PASSWORD:
                        st.session_state.authenticated = True
                        st.session_state.role = "guest"
                        # Registra accesso se db è disponibile
                        if db:
                            db.log_user_access(
                                environment=APP_ENV,
                                user_role="guest",
                                ip_address="localhost"
                            )
                        st.session_state.login_time = datetime.now()
                        st.rerun()
                    elif st.session_state.login_error is None or st.session_state.login_error != "guest_error":
                        st.session_state.login_error = "guest_error"
                        st.error("❌ Password ospite errata!")
                        st.rerun()
                else:  # Amministratore
                    if password == ADMIN_PASSWORD:
                        st.session_state.authenticated = True
                        st.session_state.role = "admin"
                        # Registra accesso se db è disponibile
                        if db:
                            db.log_user_access(
                                environment=APP_ENV,
                                user_role="admin",
                                ip_address="localhost"
                            )
                        st.session_state.login_time = datetime.now()
                        st.rerun()
                    elif st.session_state.login_error is None or st.session_state.login_error != "admin_error":
                        st.session_state.login_error = "admin_error"
                        st.error("❌ Password amministratore errata!")
                        st.rerun()
        
        st.stop()
    
    return st.session_state.role

# Inizializza il database e il calcolatore per ambiente TEST
@st.cache_resource
def init_app():
    db = FootballDatabase(environment=APP_ENV)
    calculator = FootballStatsCalculator(db)
    return db, calculator

db, calculator = init_app()

# Verifica autenticazione
user_role = check_authentication(db)

# Sidebar per navigazione
st.sidebar.title("⚽ Football Stats")
st.sidebar.markdown(f"**Ambiente {APP_ENV.upper()}**")

# Menu navigazione in base al ruolo
st.sidebar.markdown("### Navigazione")

if st.sidebar.button("📊 Dashboard", use_container_width=True):
    st.session_state.page = "📊 Dashboard"

# Solo Admin può vedere Gestione Dati
if user_role == "admin":
    if st.sidebar.button("📁 Gestione Dati", use_container_width=True):
        st.session_state.page = "📁 Gestione Dati"

if st.sidebar.button("🏆 Classifiche", use_container_width=True):
    st.session_state.page = "🏆 Classifiche"

if st.sidebar.button("📊 Under/Over", use_container_width=True):
    st.session_state.page = "📊 Under/Over"

if st.sidebar.button("🏆 Best Teams", use_container_width=True):
    st.session_state.page = "🏆 Best Teams"

if st.sidebar.button("📊 Classifiche con Parametri", use_container_width=True):
    st.session_state.page = "📊 Classifiche con Parametri"

if st.sidebar.button("🎯 Giocata Proposta", use_container_width=True):
    st.session_state.page = "🎯 Giocata Proposta"

# Solo Admin può vedere Import PDF
if user_role == "admin":
    if st.sidebar.button("📄 Import PDF", use_container_width=True):
        st.session_state.page = "📄 Import PDF"
    
    # Solo Admin può vedere Log Accessi
    if st.sidebar.button("📋 Log Accessi", use_container_width=True):
        st.session_state.page = "📋 Log Accessi"

# Logout per ambienti WEB/MOBILE
if AUTH_ENABLED and user_role in ["admin", "guest"]:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Utente:** {user_role.upper()}")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.page = "📊 Dashboard"
        st.rerun()

# Inizializza la pagina se non esiste
if 'page' not in st.session_state:
    st.session_state.page = "📊 Dashboard"

page = st.session_state.page

# Mostra la pagina corrente
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Pagina Corrente:** {page}")

# Funzione per mostrare le classifiche senza PyArrow
def show_standings_simple(standings_df, title, show_achievements=False, current_season=None):
    if standings_df.empty:
        st.warning("Nessun dato disponibile per i filtri selezionati.")
        return
    
    # Layout speciale per Under/Over: metriche sulla stessa riga del titolo
    if "Under/Over" in title:
        # Crea una riga con titolo e metriche insieme
        col_title, col1, col2, col3 = st.columns([2, 1, 1, 1])
        
        with col_title:
            st.subheader(title)
        
        with col1:
            st.metric("Squadre", len(standings_df))
        
        with col2:
            if 'PG' in standings_df.columns:
                total_matches = standings_df['PG'].sum()
            else:
                total_matches = standings_df['matches_played'].sum() if 'matches_played' in standings_df.columns else 0
            st.metric("Partite Totali", total_matches)
        
        with col3:
            avg_goals = 0
            if total_matches > 0:
                if 'GF' in standings_df.columns:
                    avg_goals = round(standings_df['GF'].sum() / total_matches, 2)
                elif 'goals_for' in standings_df.columns:
                    avg_goals = round(standings_df['goals_for'].sum() / total_matches, 2)
                elif 'under_matches' in standings_df.columns:
                    avg_goals = round(standings_df['under_percentage'].mean(), 2)
            st.metric("Media Gol/Partita" if 'GF' in standings_df.columns or 'goals_for' in standings_df.columns else "Media % Under", avg_goals)
    
    else:
        # Layout normale per le altre classifiche
        st.subheader(title)
        
        # Mostra le statistiche principali
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Squadre", len(standings_df))
        
        with col2:
            if 'PG' in standings_df.columns:
                total_matches = standings_df['PG'].sum()
            else:
                # Fallback per compatibilità
                total_matches = standings_df['matches_played'].sum() if 'matches_played' in standings_df.columns else 0
            st.metric("Partite Totali", total_matches)
        
        with col3:
            avg_goals = 0
            if total_matches > 0:
                if 'GF' in standings_df.columns:
                    avg_goals = round(standings_df['GF'].sum() / total_matches, 2)
                elif 'goals_for' in standings_df.columns:
                    # Fallback per compatibilità
                    avg_goals = round(standings_df['goals_for'].sum() / total_matches, 2)
                elif 'under_matches' in standings_df.columns:
                    # Per classifiche Under/Over, mostra la percentuale media Under
                    avg_goals = round(standings_df['under_percentage'].mean(), 2)
            st.metric("Media Gol/Partita" if 'GF' in standings_df.columns or 'goals_for' in standings_df.columns else "Media % Under", avg_goals)
        
        # Mostra "Prima in Classifica" solo per classifiche normali (non Under/Over)
        with col4:
            best_team = standings_df.iloc[0]['team'] if not standings_df.empty and 'team' in standings_df.columns else 'N/A'
            st.metric("Prima in Classifica", best_team)
    
    # Mostra la classifica usando HTML
    display_df = standings_df.copy()
    
    # Rinomina la colonna team in Squadra
    if 'team' in display_df.columns:
        display_df = display_df.rename(columns={'team': 'Squadra'})
    
    # Aggiunge colonna traguardi se richiesto
    if show_achievements:
        # Determina se siamo nell'ultima stagione disponibile nel database
        seasons = db.get_available_seasons()
        if seasons and current_season:
            # Ottieni l'ultima stagione disponibile nel database
            latest_season_in_db = seasons[-1]
            
            # Verifica se la stagione corrente è l'ultima disponibile nel database
            is_current_season = current_season == latest_season_in_db
            
            # Calcola partite rimanenti per l'ultima stagione
            matches_remaining = 8 if is_current_season else 0
        else:
            matches_remaining = 0
        
        achievements = calculator.detect_team_achievements(standings_df, current_season or "current", matches_remaining)
        display_df['Traguardo'] = display_df['Squadra'].map(achievements).fillna('')
    
    # Formatta le percentuali
    if 'V%' in display_df.columns:
        display_df['V%'] = display_df['V%'].astype(str) + '%'
        display_df['N%'] = display_df['N%'].astype(str) + '%'
        display_df['P%'] = display_df['P%'].astype(str) + '%'
    elif 'win_percentage' in display_df.columns:
        # Fallback per compatibilità
        display_df['win_percentage'] = display_df['win_percentage'].astype(str) + '%'
        display_df['draw_percentage'] = display_df['draw_percentage'].astype(str) + '%'
        display_df['loss_percentage'] = display_df['loss_percentage'].astype(str) + '%'
    
    # Mostra la tabella usando HTML per evitare problemi con pyarrow
    html_table = display_df.to_html(index=False, escape=False)
    
    # Aggiunge CSS per allineare Squadra e Traguardo a sinistra
    css_style = """
    <style>
    table.dataframe th:nth-child(1), table.dataframe td:nth-child(1) { text-align: left !important; }
    """
    
    # Trova la posizione della colonna Traguardo e allinea anche quella
    if 'Traguardo' in display_df.columns:
        traguardo_position = list(display_df.columns).index('Traguardo') + 1
        css_style += f"table.dataframe th:nth-child({traguardo_position}), table.dataframe td:nth-child({traguardo_position}) {{ text-align: left !important; }}"
    
    css_style += "</style>"
    
    st.markdown(css_style + html_table, unsafe_allow_html=True)

# Pulsante rimosso - la navigazione è già visibile nella sidebar

# Pagina Dashboard
if page == "📊 Dashboard":
    st.title("📊 Dashboard Football Stats")
    
    # Statistiche generali
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        seasons = db.get_available_seasons()
        st.metric("Stagioni Disponibili", len(seasons))
        # Debug temporaneo per vedere le stagioni (evita pyarrow)
        st.text(f"🔍 Stagioni nel DB: {', '.join(seasons)}")
    
    with col2:
        divisions = db.get_available_divisions()
        st.metric("Campionati", len(divisions))
    
    with col3:
        conn = db.get_connection()
        total_matches = pd.read_sql_query("SELECT COUNT(*) as count FROM matches", conn)['count'][0]
        conn.close()
        st.metric("Partite Totali", total_matches)
    
    with col4:
        imported_files = db.get_imported_files()
        st.metric("File Importati", len(imported_files))
    
    # Grafico delle stagioni
    if seasons:
        st.subheader("Distribuzione Partite per Stagione")
        conn = db.get_connection()
        season_stats = pd.read_sql_query("""
            SELECT season, COUNT(*) as matches_count 
            FROM matches 
            GROUP BY season 
            ORDER BY season
        """, conn)
        conn.close()
        
        fig = px.bar(season_stats, x='season', y='matches_count', 
                    title="Partite per Stagione")
        st.plotly_chart(fig, use_container_width=True)
    
    # Ultimi file importati
    st.subheader("Ultimi File Importati")
    if not imported_files.empty:
        # Converte DataFrame in formato HTML per evitare problemi con pyarrow
        st.markdown(imported_files.to_html(index=False), unsafe_allow_html=True)
    else:
        st.info("Nessun file importato ancora.")

# Pagina Gestione Dati
elif page == "📁 Gestione Dati":
    st.title("📁 Gestione Dati")
    
    tab1, tab2, tab3 = st.tabs(["Import File", "Gestione File", "Pulizia Database"])
    
    with tab1:
        st.subheader("Import File Excel/CSV")
        
        # Upload file
        uploaded_file = st.file_uploader(
            "Carica un file Excel o CSV",
            type=['xlsx', 'xls', 'csv'],
            help="Supporta file con colonne standard: Div, Date, Time, HomeTeam, AwayTeam, FTHG, FTAG, FTR, etc."
        )
        
        if uploaded_file is not None:
            # Salva il file temporaneamente
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Opzioni di import
            col1, col2 = st.columns(2)
            
            with col1:
                season = st.selectbox(
                    "Stagione",
                    ["2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025", "2025-2026"],
                    help="Seleziona la stagione del file"
                )
            
            with col2:
                file_type = st.selectbox(
                    "Tipo File",
                    ["main", "new_leagues", "future_matches"],
                    help="Tipo di file per gestire diversamente i dati"
                )
            
            if st.button("Importa File", type="primary"):
                with st.spinner("Importazione in corso..."):
                    success = db.import_excel_file(temp_path, season, file_type)
                    if success:
                        st.success("File importato con successo!")
                        st.rerun()
            
            # Pulisce il file temporaneo
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    with tab2:
        st.subheader("Gestione File Importati")
        
        imported_files = db.get_imported_files()
        
        if not imported_files.empty:
            st.markdown(imported_files.to_html(index=False), unsafe_allow_html=True)
            
            # Selezione file da eliminare
            file_to_delete = st.selectbox(
                "Seleziona file da eliminare",
                ["Nessuno"] + imported_files['filename'].tolist()
            )
            
            if file_to_delete != "Nessuno":
                if st.button("Elimina File", type="secondary"):
                    deleted_count = db.delete_file_data(file_to_delete)
                    st.success(f"Eliminati {deleted_count} record del file {file_to_delete}")
                    st.rerun()
        else:
            st.info("Nessun file importato.")
    
    with tab3:
        st.subheader("Pulizia Database")
        
        st.warning("⚠️ Attenzione: Questa operazione eliminerà permanentemente i dati.")
        
        seasons = db.get_available_seasons()
        if seasons:
            season_to_delete = st.selectbox(
                "Seleziona stagione da eliminare",
                ["Nessuna"] + seasons
            )
            
            if season_to_delete != "Nessuna":
                if st.button("Elimina Stagione", type="secondary"):
                    deleted_count = db.cleanup_old_season(season_to_delete)
                    st.success(f"Eliminati {deleted_count} record della stagione {season_to_delete}")
                    st.rerun()

# Pagina Classifiche
elif page == "🏆 Classifiche":
    st.title("🏆 Classifiche")
    
    # Filtri
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        seasons = db.get_available_seasons()
        selected_seasons = get_season_filters(seasons, "classifiche_seasons")
    
    with col2:
        divisions = db.get_available_divisions()
        
        # Mantieni l'ultima selezione o usa la prima
        if 'classifiche_division' not in st.session_state:
            st.session_state.classifiche_division = divisions[0] if divisions else None
        
        # Verifica che la divisione salvata esista ancora nella lista
        if st.session_state.classifiche_division not in divisions:
            st.session_state.classifiche_division = divisions[0] if divisions else None
        
        selected_division = st.selectbox(
            "Campionato",
            divisions,
            index=divisions.index(st.session_state.classifiche_division) if st.session_state.classifiche_division in divisions else 0,
            help="Seleziona un campionato (digita per cercare)"
        )
        
        # Salva la selezione corrente
        st.session_state.classifiche_division = selected_division
        
        # Converte in lista per compatibilità con il resto del codice
        selected_divisions = [selected_division] if selected_division else []
    
    with col3:
        standings_type = st.selectbox(
            "Tipo Classifica",
            ["Totale", "Casa", "Fuori", "I Tempo", "Casa I Tempo", "Fuori I Tempo", "II Tempo", "Casa II Tempo", "Fuori II Tempo", "Con Parametri"]
        )
    
    with col4:
        st.write("")  # Spazio vuoto
    
    # Carica i dati
    if selected_seasons and selected_divisions:
        matches_df = db.get_matches_data(selected_seasons, selected_divisions)
        
        if not matches_df.empty:
            # Determina la stagione corrente per i traguardi
            current_season_for_achievements = selected_seasons[-1] if selected_seasons else None
            
            # Gestisce i diversi tipi di classifiche
            if standings_type == "Totale":
                standings_df = calculator.calculate_standings(matches_df, "total")
                show_standings_simple(standings_df, "Classifica Totale", show_achievements=True, current_season=current_season_for_achievements)
            
            elif standings_type == "I Tempo":
                standings_df = calculator.calculate_standings(matches_df, "first_half")
                show_standings_simple(standings_df, "Classifica I Tempo")
            
            elif standings_type == "II Tempo":
                standings_df = calculator.calculate_standings(matches_df, "second_half")
                show_standings_simple(standings_df, "Classifica II Tempo")
            
            elif standings_type == "Casa":
                standings_df = calculator.calculate_standings(matches_df, "total", venue_filter="CASA")
                show_standings_simple(standings_df, "Classifica Casa", show_achievements=True, current_season=current_season_for_achievements)
            
            elif standings_type == "Fuori":
                standings_df = calculator.calculate_standings(matches_df, "total", venue_filter="FUORI")
                show_standings_simple(standings_df, "Classifica Fuori", show_achievements=True, current_season=current_season_for_achievements)
            
            elif standings_type == "Casa I Tempo":
                standings_df = calculator.calculate_standings(matches_df, "first_half", venue_filter="CASA")
                show_standings_simple(standings_df, "Classifica Casa I Tempo")
            
            elif standings_type == "Fuori I Tempo":
                standings_df = calculator.calculate_standings(matches_df, "first_half", venue_filter="FUORI")
                show_standings_simple(standings_df, "Classifica Fuori I Tempo")
            
            elif standings_type == "Casa II Tempo":
                standings_df = calculator.calculate_standings(matches_df, "second_half", venue_filter="CASA")
                show_standings_simple(standings_df, "Classifica Casa II Tempo")
            
            elif standings_type == "Fuori II Tempo":
                standings_df = calculator.calculate_standings(matches_df, "second_half", venue_filter="FUORI")
                show_standings_simple(standings_df, "Classifica Fuori II Tempo")
            
            elif standings_type == "Con Parametri":
                col1, col2 = st.columns(2)
                
                with col1:
                    exclude_top = st.selectbox(
                        "Escludi Prime N Squadre",
                        [0, 1, 2, 3, 4, 5, 6],
                        help="Numero di squadre dalla cima da escludere"
                    )
                
                with col2:
                    exclude_bottom = st.selectbox(
                        "Escludi Ultime N Squadre",
                        [0, 1, 2, 3, 4, 5, 6],
                        help="Numero di squadre dal fondo da escludere"
                    )
                
                standings_df = calculator.calculate_standings(
                    matches_df, "total", exclude_top, exclude_bottom
                )
                show_standings_simple(standings_df, "Classifica con Parametri", show_achievements=True, current_season=current_season_for_achievements)
        else:
            st.warning("Nessun dato trovato per i filtri selezionati.")
    else:
        st.info("Seleziona almeno una stagione e un campionato per visualizzare le classifiche.")

# Pagina Under/Over
elif page == "📊 Under/Over":
    st.title("📊 Under/Over")
    
    # Inizializza stato per la soglia selezionata
    if 'selected_threshold_uo' not in st.session_state:
        st.session_state.selected_threshold_uo = 2.5
    
    # Filtri per Under/Over
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        seasons_uo = db.get_available_seasons()
        selected_seasons_uo = get_season_filters(seasons_uo, "underover_seasons")
    
    with col2:
        divisions_uo = db.get_available_divisions()
        
        # Mantieni l'ultima selezione o usa la prima
        if 'underover_division' not in st.session_state:
            st.session_state.underover_division = divisions_uo[0] if divisions_uo else None
        
        # Verifica che la divisione salvata esista ancora nella lista
        if st.session_state.underover_division not in divisions_uo:
            st.session_state.underover_division = divisions_uo[0] if divisions_uo else None
        
        selected_division_uo = st.selectbox(
            "Campionato",
            divisions_uo,
            index=divisions_uo.index(st.session_state.underover_division) if st.session_state.underover_division in divisions_uo else 0,
            key="uo_division"
        )
        
        # Salva la selezione corrente
        st.session_state.underover_division = selected_division_uo
    
    with col3:
        venue_filter = st.selectbox(
            "Filtro",
            ["Totale", "Casa", "Fuori", "I Tempo", "Casa I Tempo", "Fuori I Tempo", "II Tempo", "Casa II Tempo", "Fuori II Tempo"],
            key="uo_venue"
        )
    
    with col4:
        st.write("")  # Spazio vuoto
    
    # Inizializza soglia di default se non presente
    if 'selected_threshold_uo' not in st.session_state:
        st.session_state.selected_threshold_uo = 2.5
    
    # Pulsanti soglie cliccabili (come richiesto dall'utente)
    st.write("**Soglie Under/Over:**")
    # Layout ancora più compatto per spostare i pulsanti più a sinistra
    threshold_cols = st.columns([0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 3.2])  # Colonne più strette
    thresholds = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
    
    for i, threshold in enumerate(thresholds):
        with threshold_cols[i]:
            if st.button(f"{threshold}", key=f"threshold_{threshold}"):
                st.session_state.selected_threshold_uo = threshold
                st.rerun()
    
    # Usa la soglia selezionata
    threshold = st.session_state.selected_threshold_uo
    
    # Mostra sempre una classifica Under/Over
    if selected_seasons_uo and selected_division_uo:
        matches_df_uo = db.get_matches_data(selected_seasons_uo, [selected_division_uo])
        
        if not matches_df_uo.empty:
            # Estrai parametri dal filtro selezionato
            if venue_filter == "Totale":
                venue_param = "TOTALE"
                time_param = "TOTALE"
            elif venue_filter == "Casa":
                venue_param = "CASA"
                time_param = "TOTALE"
            elif venue_filter == "Fuori":
                venue_param = "FUORI"
                time_param = "TOTALE"
            elif venue_filter == "I Tempo":
                venue_param = "TOTALE"
                time_param = "I TEMPO"
            elif venue_filter == "Casa I Tempo":
                venue_param = "CASA"
                time_param = "I TEMPO"
            elif venue_filter == "Fuori I Tempo":
                venue_param = "FUORI"
                time_param = "I TEMPO"
            elif venue_filter == "II Tempo":
                venue_param = "TOTALE"
                time_param = "II TEMPO"
            elif venue_filter == "Casa II Tempo":
                venue_param = "CASA"
                time_param = "II TEMPO"
            elif venue_filter == "Fuori II Tempo":
                venue_param = "FUORI"
                time_param = "II TEMPO"
            else:
                venue_param = "TOTALE"
                time_param = "TOTALE"
            
            # Calcola classifica Under/Over
            standings_df_uo = calculator.calculate_under_over_standings(matches_df_uo, threshold, venue_param, time_param)
            
            # Usa show_standings_simple per visualizzare (come in Best Teams)
            show_standings_simple(standings_df_uo, f"Classifica Under/Over {threshold}")
        else:
            st.warning("Nessuna partita trovata per i filtri selezionati")
    else:
        st.info("Seleziona stagioni e campionato per visualizzare la classifica Under/Over.")

# Pagina Classifiche con Parametri
elif page == "📊 Classifiche con Parametri":
    col_title, col_button = st.columns([3, 1])
    
    with col_title:
        st.title("📊 Classifiche con Parametri")
    
    with col_button:
        st.write("")  # Spazio per centrare il pulsante
        if st.button("⚙️ Impostazioni Best", use_container_width=True, type="primary"):
            st.session_state.page = "⚙️ Impostazioni Best"
            st.rerun()
    
    if st.session_state.page != "⚙️ Impostazioni Best":
        
        # Inizializza config PRIMA dei filtri
        if 'divisions_config' not in st.session_state:
            saved_config = load_divisions_config()
            st.session_state.divisions_config = {}
            divisions = db.get_available_divisions()
            for div in divisions:
                st.session_state.divisions_config[div] = {
                    'exclude_top': saved_config.get(div, {}).get('exclude_top', 0),
                    'exclude_bottom': saved_config.get(div, {}).get('exclude_bottom', 0)
                }
        
        # Filtri principali in alto (Stagioni, Campionato, Prime, Ultime)
        col1, col2, col3, col4, col5 = st.columns([2, 1, 0.3, 0.7, 0.7])
        
        with col1:
            seasons = db.get_available_seasons()
            selected_seasons = get_season_filters(seasons, "parametri_seasons")
        
        with col2:
            divisions = db.get_available_divisions()
             
            # Mantieni l'ultima selezione o usa la prima
            if 'parametri_division' not in st.session_state:
                st.session_state.parametri_division = divisions[0] if divisions else None
            
            # Verifica che la divisione salvata esista ancora nella lista
            if st.session_state.parametri_division not in divisions:
                st.session_state.parametri_division = divisions[0] if divisions else None
            
            selected_division = st.selectbox(
                "Campionato",
                divisions,
                key="parametri_division_selectbox",
                index=divisions.index(st.session_state.parametri_division) if st.session_state.parametri_division in divisions else 0
            )
            
            # Salva la selezione corrente
            st.session_state.parametri_division = selected_division
        
        with col3:
            st.write("")  # Spazio vuoto
        
        with col4:
            # Leggi il valore del campionato selezionato
            current_top_value = st.session_state.divisions_config.get(selected_division, {}).get('exclude_top', 0)
            
            exclude_top = st.number_input(
                "Prime",
                min_value=0,
                max_value=10,
                value=int(current_top_value),
                step=1,
                key=f"exclude_top_filter_{selected_division}"
            )
            # Aggiorna config immediatamente
            if selected_division in st.session_state.divisions_config:
                st.session_state.divisions_config[selected_division]['exclude_top'] = exclude_top
        
        with col5:
            # Leggi il valore del campionato selezionato
            current_bottom_value = st.session_state.divisions_config.get(selected_division, {}).get('exclude_bottom', 0)
            
            exclude_bottom = st.number_input(
                "Ultime",
                min_value=0,
                max_value=10,
                value=int(current_bottom_value),
                step=1,
                key=f"exclude_bottom_filter_{selected_division}"
            )
            # Aggiorna config immediatamente
            if selected_division in st.session_state.divisions_config:
                st.session_state.divisions_config[selected_division]['exclude_bottom'] = exclude_bottom
        
        # Salva config su file solo se necessario
        if selected_division:
            save_divisions_config(st.session_state.divisions_config)
        
        # Layout principale - mostra solo la tabella
        st.subheader("Classifiche con parametri")
        
        if selected_seasons and selected_division:
            # Usa i valori dai filtri invece della config salvata
            # exclude_top e exclude_bottom sono già definiti dai filtri sopra
            
            # Ottieni dati delle partite
            matches_df = db.get_matches_data(selected_seasons, [selected_division])
            
            if not matches_df.empty:
                # Calcola classifiche con esclusione scontri diretti
                standings_df = calculator.calculate_standings(
                    matches_df, 
                    standings_type="TOTALE",
                    exclude_top=exclude_top,
                    exclude_bottom=exclude_bottom
                )
                
                if not standings_df.empty:
                    # Mostra statistiche personalizzate
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Squadre", len(standings_df))
                    
                    with col2:
                        total_matches = standings_df['PG'].sum()
                        st.metric("Partite Totali", total_matches)
                    
                    with col3:
                        # Usa i valori dalla config del campionato selezionato
                        exclude_top_value = st.session_state.divisions_config.get(selected_division, {}).get('exclude_top', 0)
                        st.metric("Escludi Prime", exclude_top_value)
                    
                    with col4:
                        # Usa i valori dalla config del campionato selezionato
                        exclude_bottom_value = st.session_state.divisions_config.get(selected_division, {}).get('exclude_bottom', 0)
                        st.metric("Escludi Ultime", exclude_bottom_value)
                    
                    # Mostra solo la tabella delle classifiche (senza metriche duplicate)
                    if not standings_df.empty:
                        # Mostra la tabella delle classifiche
                        st.markdown(standings_df.to_html(index=False, escape=False), unsafe_allow_html=True)
                else:
                    st.warning("Nessuna classifica disponibile con i parametri selezionati")
            else:
                st.warning("Nessun dato disponibile per i filtri selezionati")
        else:
            st.info("Seleziona stagioni e campionato per visualizzare le classifiche")

# Pagina Impostazioni Best
elif page == "⚙️ Impostazioni Best":
    col_title, col_back = st.columns([3, 1])
    
    with col_title:
        st.title("⚙️ Impostazioni Best")
    
    with col_back:
        st.write("")
        if st.button("← Torna Indietro", use_container_width=True):
            st.session_state.page = "📊 Classifiche con Parametri"
            st.rerun()
    
    st.info("📝 Configura le regole per il calcolo della Classifica BEST basato su obiettivi raggiunti")
    
    # MOSTRA I FILTRI ESISTENTI DAL PAGINA PRECEDENTE
    st.subheader("📌 Filtri Attivi")
    
    # Carica config delle divisioni
    if 'divisions_config' not in st.session_state:
        saved_config = load_divisions_config()
        st.session_state.divisions_config = {}
        divisions = db.get_available_divisions()
        for div in divisions:
            st.session_state.divisions_config[div] = {
                'exclude_top': saved_config.get(div, {}).get('exclude_top', 0),
                'exclude_bottom': saved_config.get(div, {}).get('exclude_bottom', 0)
            }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📌 Filtri Configurazione")
        
        # Intestazione tabella su una riga
        col_header_nazioni, col_header_top, col_header_bottom = st.columns([1, 1, 1])
        
        with col_header_nazioni:
            st.write("**Nazioni**")
        
        with col_header_top:
            st.write("**Prime**")
        
        with col_header_bottom:
            st.write("**Ultime**")
        
        st.markdown("<hr style='margin: 0.1rem 0;'/>", unsafe_allow_html=True)
        
        # Crea tabella per ogni campionato (Nazioni | Prime | Ultime)
        for i, div in enumerate(db.get_available_divisions()):
            col_nazioni, col_top, col_bottom = st.columns([1, 1, 1])
            
            with col_nazioni:
                st.write(f"`{div}`")
            
            with col_top:
                exclude_top = st.number_input(
                    " ",
                    min_value=0,
                    max_value=10,
                    value=st.session_state.divisions_config[div]['exclude_top'],
                    step=1,
                    key=f"settings_top_{div}",
                    label_visibility="collapsed"
                )
                # Salva se il valore è cambiato
                if exclude_top != st.session_state.divisions_config[div]['exclude_top']:
                    st.session_state.divisions_config[div]['exclude_top'] = exclude_top
                    save_divisions_config(st.session_state.divisions_config)
            
            with col_bottom:
                exclude_bottom = st.number_input(
                    " ",
                    min_value=0,
                    max_value=10,
                    value=st.session_state.divisions_config[div]['exclude_bottom'],
                    step=1,
                    key=f"settings_bottom_{div}",
                    label_visibility="collapsed"
                )
                # Salva se il valore è cambiato
                if exclude_bottom != st.session_state.divisions_config[div]['exclude_bottom']:
                    st.session_state.divisions_config[div]['exclude_bottom'] = exclude_bottom
                    save_divisions_config(st.session_state.divisions_config)
            
            if i < len(db.get_available_divisions()) - 1:  # Non aggiungere linea dopo l'ultima riga
                st.markdown("<hr style='margin: 0.1rem 0;'/>", unsafe_allow_html=True)
    
    with col2:
        st.subheader("⚙️ Regole Motivazione")
        st.info("🎯 Sistema di penalità/bonus basato sugli obiettivi raggiunti")
        st.write("")
        st.write("**📊 Obiettivi:**")
        st.write("")
        st.write("🏆 Champions League assicurata: **-10% motivazione**")
        st.write("")
        st.write("🏆 Europa League assicurata: **-7% motivazione**")
        st.write("")
        st.write("📉 Retrocesso matematicamente: **+20% motivazione** *(nessuno stimolo)*")
        st.write("")
        st.write("🎯 Lotta per obiettivi: **motivazione neutra**")
    
    # Placeholder per le impostazioni dettagliate
    st.markdown("---")
    st.subheader("🔧 Impostazioni Avanzate")
    st.write("Qui potrai modificare le regole specifiche per ogni campionato quando implementeremo l'interfaccia completa.")

# Pagina Best Teams
elif page == "🏆 Best Teams":
    st.title("🏆 Best Teams")
    
    # Filtri principali
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        seasons = db.get_available_seasons()
        selected_seasons = get_season_filters(seasons, "bestteams_seasons")
    
    with col2:
        # Filtro percentuale numerico editabile
        percentage_threshold = st.number_input(
            "Soglia (%)",
            min_value=0.0,
            max_value=100.0,
            value=70.0,
            step=1.0,
            format="%.0f",
            help="Inserisci la percentuale minima per includere una squadra nella classifica",
            key="best_threshold"
        )
    
    with col3:
        st.write("")  # Spazio vuoto
    
    with col4:
        st.write("")  # Spazio vuoto
    
    if selected_seasons:
        # Ottieni dati da TUTTI i campionati (nessun filtro divisione)
        matches_df = db.get_matches_data(selected_seasons, [])
        
        if not matches_df.empty:
            tab1, tab2, tab3, tab4 = st.tabs(["Classifica BEST", "Classifica BEST con Parametri", "Classifica BEST Under/Over", "Classifica U/O Totale"])
            
            with tab1:
                st.subheader("Classifica BEST")
                
                # Calcola statistiche per ogni squadra
                teams_stats = []
                
                for team in matches_df['home_team'].unique():
                    # Partite in casa
                    home_matches = matches_df[matches_df['home_team'] == team]
                    # Partite in trasferta
                    away_matches = matches_df[matches_df['away_team'] == team]
                    
                    # Calcola statistiche
                    total_matches = len(home_matches) + len(away_matches)
                    if total_matches == 0:
                        continue
                    
                    # Vittorie
                    home_wins = len(home_matches[home_matches['ft_result'] == 'H'])
                    away_wins = len(away_matches[away_matches['ft_result'] == 'A'])
                    total_wins = home_wins + away_wins
                    win_percentage = (total_wins / total_matches) * 100
                    
                    # Pareggi
                    home_draws = len(home_matches[home_matches['ft_result'] == 'D'])
                    away_draws = len(away_matches[away_matches['ft_result'] == 'D'])
                    total_draws = home_draws + away_draws
                    draw_percentage = (total_draws / total_matches) * 100
                    
                    # Sconfitte
                    home_losses = len(home_matches[home_matches['ft_result'] == 'A'])
                    away_losses = len(away_matches[away_matches['ft_result'] == 'H'])
                    total_losses = home_losses + away_losses
                    loss_percentage = (total_losses / total_matches) * 100
                    
                    # Determina cosa giocare
                    play_what = ""
                    if win_percentage >= percentage_threshold:
                        play_what = "V"
                    elif draw_percentage >= percentage_threshold:
                        play_what = "N"
                    elif loss_percentage >= percentage_threshold:
                        play_what = "P"
                    
                    # Aggiungi solo se supera la soglia
                    if win_percentage >= percentage_threshold or draw_percentage >= percentage_threshold or loss_percentage >= percentage_threshold:
                        teams_stats.append({
                            'Squadra': team,
                            'PG': total_matches,
                            'V': total_wins,
                            'N': total_draws,
                            'P': total_losses,
                            'V%': round(win_percentage, 1),
                            'N%': round(draw_percentage, 1),
                            'P%': round(loss_percentage, 1),
                            'Gioca': play_what
                        })
                
                if teams_stats:
                    # Converti in DataFrame
                    best_teams_df = pd.DataFrame(teams_stats)
                    
                    # Ordina per la percentuale più alta tra V%, N%, P%
                    best_teams_df['Max_Percentage'] = best_teams_df[['V%', 'N%', 'P%']].max(axis=1)
                    best_teams_df = best_teams_df.sort_values('Max_Percentage', ascending=False)
                    
                    # Rimuovi la colonna temporanea
                    best_teams_df = best_teams_df.drop('Max_Percentage', axis=1)
                    
                    # Mostra la classifica
                    show_standings_simple(best_teams_df, f"Best Teams (Soglia: {percentage_threshold}%)")
                else:
                    st.warning(f"Nessuna squadra supera la soglia del {percentage_threshold}%")
            
            with tab2:
                st.subheader("Classifica BEST con Parametri")
                
                # Calcola statistiche per ogni squadra considerando V%, N%, P%
                all_teams_stats = []
                
                for team in matches_df['home_team'].unique():
                    # Partite in casa
                    home_matches = matches_df[matches_df['home_team'] == team]
                    # Partite in trasferta
                    away_matches = matches_df[matches_df['away_team'] == team]
                    
                    # Calcola statistiche
                    total_matches = len(home_matches) + len(away_matches)
                    if total_matches == 0:
                        continue
                    
                    # Vittorie
                    home_wins = len(home_matches[home_matches['ft_result'] == 'H'])
                    away_wins = len(away_matches[away_matches['ft_result'] == 'A'])
                    total_wins = home_wins + away_wins
                    win_percentage = (total_wins / total_matches) * 100
                    
                    # Pareggi
                    home_draws = len(home_matches[home_matches['ft_result'] == 'D'])
                    away_draws = len(away_matches[away_matches['ft_result'] == 'D'])
                    total_draws = home_draws + away_draws
                    draw_percentage = (total_draws / total_matches) * 100
                    
                    # Sconfitte
                    home_losses = len(home_matches[home_matches['ft_result'] == 'A'])
                    away_losses = len(away_matches[away_matches['ft_result'] == 'H'])
                    total_losses = home_losses + away_losses
                    loss_percentage = (total_losses / total_matches) * 100
                    
                    # Calcola punti per ordinamento (3 punti per vittoria, 1 per pareggio)
                    points = (total_wins * 3) + (total_draws * 1)
                    
                    # Aggiungi tutte le squadre con i loro punti per ordinamento
                    all_teams_stats.append({
                        'Squadra': team,
                        'PG': total_matches,
                        'V': total_wins,
                        'N': total_draws,
                        'P': total_losses,
                        'V%': round(win_percentage, 1),
                        'N%': round(draw_percentage, 1),
                        'P%': round(loss_percentage, 1),
                        'PT': points
                    })
                
                if all_teams_stats:
                    # Converti in DataFrame e ordina per punti (classifica normale)
                    all_teams_df = pd.DataFrame(all_teams_stats)
                    all_teams_df = all_teams_df.sort_values(['PT', 'V%'], ascending=[False, False])
                    
                    # Ora filtra per soglia percentuale e aggiungi colonna "Gioca"
                    teams_stats = []
                    for _, row in all_teams_df.iterrows():
                        # Determina cosa giocare
                        play_what = ""
                        if row['V%'] >= percentage_threshold:
                            play_what = "V"
                        elif row['N%'] >= percentage_threshold:
                            play_what = "N"
                        elif row['P%'] >= percentage_threshold:
                            play_what = "P"
                        
                        # Aggiungi solo se supera la soglia
                        if row['V%'] >= percentage_threshold or row['N%'] >= percentage_threshold or row['P%'] >= percentage_threshold:
                            teams_stats.append({
                                'Squadra': row['Squadra'],
                                'PG': row['PG'],
                                'V': row['V'],
                                'N': row['N'],
                                'P': row['P'],
                                'V%': row['V%'],
                                'N%': row['N%'],
                                'P%': row['P%'],
                                'Gioca': play_what
                            })
                
                if teams_stats:
                    # Converti in DataFrame
                    best_teams_df = pd.DataFrame(teams_stats)
                    
                    # Ordina per la percentuale più alta tra V%, N%, P%
                    best_teams_df['Max_Percentage'] = best_teams_df[['V%', 'N%', 'P%']].max(axis=1)
                    best_teams_df = best_teams_df.sort_values('Max_Percentage', ascending=False)
                    
                    # Rimuovi la colonna temporanea
                    best_teams_df = best_teams_df.drop('Max_Percentage', axis=1)
                    
                    # Mostra solo le statistiche delle squadre filtrate
                    total_teams = len(best_teams_df)
                    total_matches = best_teams_df['PG'].sum()
                    avg_goals = round(best_teams_df['PG'].sum() / len(best_teams_df) if len(best_teams_df) > 0 else 0, 2)
                    
                    # Mostra statistiche filtrate
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Squadre", total_teams)
                    with col2:
                        st.metric("Partite Totali", total_matches)
                    with col3:
                        st.metric("Media Gol/Partita", avg_goals)
                    
                    # Mostra la classifica senza sottotitolo e senza statistiche duplicate
                    display_df = best_teams_df.copy()
                    
                    # Mostra la classifica usando HTML
                    st.markdown(display_df.to_html(index=False, escape=False), unsafe_allow_html=True)
                else:
                    st.warning(f"Nessuna squadra supera la soglia del {percentage_threshold}%")
            
            with tab3:
                st.subheader("Classifica BEST Under/Over")
                
                threshold = st.selectbox(
                    "Soglia Under/Over",
                    [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5],
                    index=2,
                    key="best_under_over"
                )
                
                standings_df = calculator.calculate_under_over_standings(matches_df, threshold)
                show_standings_simple(standings_df, f"Classifica BEST Under/Over {threshold}")
            
            with tab4:
                st.subheader("Classifica U/O Totale")
                
                threshold_uo = st.selectbox(
                    "Soglia Percentuale (%)",
                    [70, 75, 80, 85, 90],
                    index=2,
                    key="best_uo_totale"
                )
                
                # Calcola statistiche per ogni squadra su tutte le soglie
                teams_stats_all = []
                all_thresholds = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5]
                
                for team in matches_df['home_team'].unique():
                    team_stats = {}
                    best_threshold = None
                    best_percentage = 0
                    best_type = None  # 'O' o 'U'
                    
                    # Calcola per ogni soglia
                    for th in all_thresholds:
                        stats = calculator._calculate_under_over_stats(matches_df, team, th, "TOTALE", "TOTALE")
                        if stats:
                            pg = stats.get('PG', 0)
                            if pg > 0:
                                u_perc = (stats.get('U', 0) / pg) * 100
                                o_perc = (stats.get('O', 0) / pg) * 100
                                
                                # Tiene la % più alta tra U e O
                                if u_perc > best_percentage:
                                    best_percentage = u_perc
                                    best_threshold = th
                                    best_type = 'U'
                                if o_perc > best_percentage:
                                    best_percentage = o_perc
                                    best_threshold = th
                                    best_type = 'O'
                    
                    # Se supera la soglia specificata
                    if best_percentage >= threshold_uo:
                        team_stats = calculator._calculate_under_over_stats(matches_df, team, best_threshold, "TOTALE", "TOTALE")
                        if team_stats:
                            team_stats['Squadra'] = team
                            team_stats['PG'] = team_stats.get('PG', 0)
                            team_stats['U'] = team_stats.get('U', 0)
                            team_stats['O'] = team_stats.get('O', 0)
                            team_stats['U%'] = round((team_stats['U'] / team_stats['PG']) * 100, 2) if team_stats['PG'] > 0 else 0
                            team_stats['O%'] = round((team_stats['O'] / team_stats['PG']) * 100, 2) if team_stats['PG'] > 0 else 0
                            team_stats['Pron'] = best_threshold
                            team_stats['Gioca'] = best_type
                            team_stats['%'] = round(best_percentage, 2)
                            
                            teams_stats_all.append(team_stats)
                
                if teams_stats_all:
                    best_uo_df = pd.DataFrame(teams_stats_all)
                    # Ordina per % decrescente
                    best_uo_df = best_uo_df.sort_values('%', ascending=False)
                    # Mostra solo le colonne necessarie
                    display_df = best_uo_df[['Squadra', 'PG', 'U', 'O', 'U%', 'O%', 'Pron', 'Gioca', '%']]
                    st.markdown(display_df.to_html(index=False, escape=False), unsafe_allow_html=True)
                else:
                    st.warning(f"Nessuna squadra supera la soglia del {threshold_uo}%")
        else:
            st.warning("Nessun dato trovato per le stagioni selezionate.")
    else:
        st.info("Seleziona almeno una stagione per visualizzare la classifica Best Teams.")

# Pagina Giocata Proposta
elif page == "🎯 Giocata Proposta":
    st.title("🎯 Giocata Proposta")
    
    st.info("🚧 Funzionalità in sviluppo - Sarà implementata dopo il completamento delle classifiche base")
    
    # Placeholder per la funzionalità futura
    st.subheader("Sistema Bonus/Malus")
    st.write("Questa sezione conterrà:")
    st.write("- Analisi delle motivazioni delle squadre")
    st.write("- Sistema di bonus/malus per traguardi raggiunti")
    st.write("- Proposte di giocata basate su statistiche avanzate")
    st.write("- Analisi testa a testa e ultime partite")

# Pagina Import PDF
elif page == "📄 Import PDF":
    st.title("📄 Import PDF")
    
    st.info("🚧 Funzionalità in sviluppo - Sarà implementata per estrarre partite future da PDF")
    
    # Placeholder per la funzionalità futura
    st.subheader("Estrazione Partite Future")
    st.write("Questa sezione conterrà:")
    st.write("- Upload e parsing di file PDF")
    st.write("- Estrazione automatica di partite future")
    st.write("- Integrazione con database principale")
    st.write("- Gestione di campionati non standard")

elif page == "📋 Log Accessi":
    st.title("📋 Log Accessi")
    
    # Recupera i log degli accessi
    access_logs = db.get_access_logs(limit=100)
    
    if not access_logs.empty:
        st.subheader("Ultimi Accessi")
        
        # Mostra statistiche riepilogative
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_logins = len(access_logs)
            st.metric("Accessi Totali", total_logins)
        
        with col2:
            if 'user_role' in access_logs.columns:
                total_admins = len(access_logs[access_logs['user_role'] == 'admin'])
                st.metric("Accessi Admin", total_admins)
        
        with col3:
            if 'user_role' in access_logs.columns:
                total_guests = len(access_logs[access_logs['user_role'] == 'guest'])
                st.metric("Accessi Ospiti", total_guests)
        
        with col4:
            # Ultimi 7 giorni
            if 'login_time' in access_logs.columns:
                recent_logs = access_logs.head(20)  # Ultimi 20 accessi
                st.metric("Visualizzati", 20)
        
        # Tabella dettagliata
        st.subheader("Dettagli Accessi")
        
        # Mostra i dati in modo semplice per evitare errori CSS
        for index, row in access_logs.iterrows():
            with st.expander(f"Accesso {index + 1} - {row.get('login_time', 'N/A')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Utente:** {row.get('user_role', 'N/A').upper()}")
                    st.write(f"**Ambiente:** {row.get('environment', 'N/A').upper()}")
                with col2:
                    st.write(f"**IP:** {row.get('ip_address', 'N/A')}")
                    if 'session_duration' in row and row.get('session_duration'):
                        st.write(f"**Durata:** {row.get('session_duration')} minuti")
        
    else:
        st.info("Nessun accesso registrato ancora.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Football Stats App** v1.0")
st.sidebar.markdown("Sviluppato con Streamlit")
