# Configurazione per gestire diversi tipi di file Excel

FILE_CONFIGS = {
    "all-euro-data-2020-2021": {
        "season": "2020-2021",
        "type": "main",
        "columns": "standard"
    },
    "all-euro-data-2021-2022": {
        "season": "2021-2022", 
        "type": "main",
        "columns": "standard"
    },
    "all-euro-data-2022-2023": {
        "season": "2022-2023",
        "type": "main", 
        "columns": "standard"
    },
    "all-euro-data-2023-2024": {
        "season": "2023-2024",
        "type": "main",
        "columns": "standard"
    },
    "all-euro-data-2024-2025": {
        "season": "2024-2025",
        "type": "main",
        "columns": "extended"  # Ha colonne aggiuntive
    },
    "all-euro-data-2025-2026": {
        "season": "2025-2026", 
        "type": "main",
        "columns": "extended"  # Ha colonne aggiuntive
    },
    "new_leagues_data": {
        "season": "current",
        "type": "new_leagues",
        "columns": "custom"  # Struttura personalizzata
    }
}

# Mapping delle colonne per diversi tipi di file
COLUMN_MAPPINGS = {
    "standard": {
        'div': 'div',
        'date': 'date',
        'time': 'time',
        'hometeam': 'home_team',
        'awayteam': 'away_team',
        'fthg': 'ft_home_goals',
        'ftag': 'ft_away_goals',
        'ftr': 'ft_result',
        'hthg': 'ht_home_goals',
        'htag': 'ht_away_goals',
        'htr': 'ht_result',
        'referee': 'referee',
        'hs': 'home_shots',
        'as': 'away_shots',
        'hst': 'home_shots_target',
        'ast': 'away_shots_target',
        'hf': 'home_fouls',
        'af': 'away_fouls',
        'hc': 'home_corners',
        'ac': 'away_corners',
        'hy': 'home_yellow',
        'ay': 'away_yellow',
        'hr': 'home_red',
        'ar': 'away_red',
        'b365h': 'b365_home',
        'b365d': 'b365_draw',
        'b365a': 'b365_away'
    },
    "extended": {
        # Include tutte le colonne standard più quelle aggiuntive
        **COLUMN_MAPPINGS["standard"],
        'bfh': 'bf_home',  # Nuove colonne per file 2024-2025+
        'bfd': 'bf_draw',
        'bfa': 'bf_away',
        'bfdh': 'bf_draw_home',
        'bfda': 'bf_draw_away'
    },
    "custom": {
        # Per new_leagues_data - struttura personalizzata
        'division': 'div',
        'match_date': 'date',
        'match_time': 'time',
        'home': 'home_team',
        'away': 'away_team',
        'hg': 'ft_home_goals',
        'ag': 'ft_away_goals',
        'result': 'ft_result',
        'hthg': 'ht_home_goals',
        'htag': 'ht_away_goals',
        'htr': 'ht_result'
    }
}

# Configurazione per la gestione delle stagioni
SEASON_CONFIG = {
    "current_year": 2024,
    "seasons_to_keep": 6,  # Numero di stagioni da mantenere
    "auto_cleanup": True,  # Eliminazione automatica delle stagioni vecchie
    "cleanup_warning": True  # Mostra avviso prima dell'eliminazione
}

# Configurazione per le classifiche
STANDINGS_CONFIG = {
    "default_exclude_top": 4,  # Squadre da escludere dalla cima
    "default_exclude_bottom": 4,  # Squadre da escludere dal fondo
    "achievement_positions": {
        "champion": 1,
        "champions_league": [1, 2, 3, 4],
        "europa_league": [5, 6],
        "conference_league": [7],
        "relegation": [-3, -2, -1]  # Ultime 3 posizioni
    }
}

# Configurazione per le soglie Under/Over
UNDER_OVER_THRESHOLDS = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5]

# Configurazione per il sistema bonus/malus
BONUS_MALUS_CONFIG = {
    "achievement_penalties": {
        "champion": -0.1,  # -10% di motivazione
        "champions_league": -0.05,  # -5% di motivazione
        "europa_league": -0.03,  # -3% di motivazione
        "relegation": -0.15  # -15% di motivazione
    },
    "form_bonuses": {
        "win_streak": 0.05,  # +5% per ogni vittoria consecutiva
        "loss_streak": -0.05  # -5% per ogni sconfitta consecutiva
    }
}
