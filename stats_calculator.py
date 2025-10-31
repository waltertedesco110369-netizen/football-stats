import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st

class FootballStatsCalculator:
    def __init__(self, db):
        self.db = db
    
    def calculate_standings(self, matches_df, standings_type="total", exclude_top=None, exclude_bottom=None, venue_filter="TOTALE"):
        """
        Calcola le classifiche per tipo specificato
        
        Args:
            matches_df: DataFrame con i dati delle partite
            standings_type: "total", "first_half", "second_half", "under_over"
            exclude_top: numero di squadre da escludere dalla cima
            exclude_bottom: numero di squadre da escludere dal fondo
            venue_filter: "TOTALE", "CASA", "FUORI"
        """
        if matches_df.empty:
            return pd.DataFrame()
        
        # Prepara i dati
        df = matches_df.copy()
        
        # Converte le colonne necessarie
        df['ft_home_goals'] = pd.to_numeric(df['ft_home_goals'], errors='coerce')
        df['ft_away_goals'] = pd.to_numeric(df['ft_away_goals'], errors='coerce')
        df['ht_home_goals'] = pd.to_numeric(df['ht_home_goals'], errors='coerce')
        df['ht_away_goals'] = pd.to_numeric(df['ht_away_goals'], errors='coerce')
        
        # Rimuove righe con dati mancanti
        df = df.dropna(subset=['ft_home_goals', 'ft_away_goals'])
        
        standings_data = []
        
        # Ottiene tutte le squadre uniche
        all_teams = set(df['home_team'].unique()) | set(df['away_team'].unique())
        
        for team in all_teams:
            team_stats = self._calculate_team_stats(df, team, standings_type, venue_filter)
            if team_stats:
                standings_data.append(team_stats)
        
        if not standings_data:
            return pd.DataFrame()
        
        standings_df = pd.DataFrame(standings_data)
        
        # Applica sempre il nuovo metodo per garantire calcoli corretti
        # anche quando exclude_top e exclude_bottom sono entrambi 0
        standings_df = self._apply_exclusions(standings_df, exclude_top, exclude_bottom, matches_df, standings_type, venue_filter)
        
        # Ordina per punti e differenza reti
        if 'PT' in standings_df.columns and 'DF' in standings_df.columns:
            standings_df = standings_df.sort_values(['PT', 'DF'], ascending=[False, False])
        else:
            # Fallback per compatibilità
            standings_df = standings_df.sort_values(['points', 'goal_difference'], ascending=[False, False])
        standings_df['PZ'] = range(1, len(standings_df) + 1)
        
        return standings_df
    
    def _calculate_team_stats(self, df, team, standings_type, venue_filter="TOTALE"):
        """Calcola le statistiche per una singola squadra"""
        # Partite in casa
        home_matches = df[df['home_team'] == team].copy()
        # Partite in trasferta
        away_matches = df[df['away_team'] == team].copy()
        
        # Applica filtro venue
        if venue_filter == "CASA":
            away_matches = pd.DataFrame()  # Esclude partite fuori casa
        elif venue_filter == "FUORI":
            home_matches = pd.DataFrame()  # Esclude partite in casa
        
        if home_matches.empty and away_matches.empty:
            return None
        
        stats = {
            'team': team,
            'PG': 0,
            'V': 0,
            'N': 0,
            'P': 0,
            'GF': 0,
            'GS': 0,
            'DF': 0,
            'PT': 0,
            'V%': 0,
            'N%': 0,
            'P%': 0
        }
        
        # Processa partite in casa
        for _, match in home_matches.iterrows():
            stats['PG'] += 1
            
            if standings_type == "total":
                goals_for = match['ft_home_goals']
                goals_against = match['ft_away_goals']
                result = match['ft_result']
            elif standings_type == "first_half":
                goals_for = match['ht_home_goals']
                goals_against = match['ht_away_goals']
                result = match['ht_result']
            elif standings_type == "second_half":
                goals_for = match['ft_home_goals'] - match['ht_home_goals']
                goals_against = match['ft_away_goals'] - match['ht_away_goals']
                # Determina il risultato del secondo tempo
                if goals_for > goals_against:
                    result = 'H'
                elif goals_for < goals_against:
                    result = 'A'
                else:
                    result = 'D'
            else:
                continue
            
            stats['GF'] += goals_for
            stats['GS'] += goals_against
            
            if result == 'H':
                stats['V'] += 1
                stats['PT'] += 3
            elif result == 'D':
                stats['N'] += 1
                stats['PT'] += 1
            else:
                stats['P'] += 1
        
        # Processa partite in trasferta
        for _, match in away_matches.iterrows():
            stats['PG'] += 1
            
            if standings_type == "total":
                goals_for = match['ft_away_goals']
                goals_against = match['ft_home_goals']
                result = match['ft_result']
            elif standings_type == "first_half":
                goals_for = match['ht_away_goals']
                goals_against = match['ht_home_goals']
                result = match['ht_result']
            elif standings_type == "second_half":
                goals_for = match['ft_away_goals'] - match['ht_away_goals']
                goals_against = match['ft_home_goals'] - match['ht_home_goals']
                # Determina il risultato del secondo tempo
                if goals_for > goals_against:
                    result = 'A'
                elif goals_for < goals_against:
                    result = 'H'
                else:
                    result = 'D'
            else:
                continue
            
            stats['GF'] += goals_for
            stats['GS'] += goals_against
            
            if result == 'A':
                stats['V'] += 1
                stats['PT'] += 3
            elif result == 'D':
                stats['N'] += 1
                stats['PT'] += 1
            else:
                stats['P'] += 1
        
        # Calcola differenza reti e percentuali
        stats['DF'] = stats['GF'] - stats['GS']
        
        if stats['PG'] > 0:
            stats['V%'] = round((stats['V'] / stats['PG']) * 100, 2)
            stats['N%'] = round((stats['N'] / stats['PG']) * 100, 2)
            stats['P%'] = round((stats['P'] / stats['PG']) * 100, 2)
        
        return stats
    
    def _apply_exclusions(self, standings_df, exclude_top, exclude_bottom, matches_df, standings_type, venue_filter):
        """Applica le esclusioni per le classifiche con parametri"""
        # Identifica le squadre da escludere
        excluded_teams = []
        if exclude_top:
            top_teams = standings_df.head(exclude_top)['team'].tolist()
            excluded_teams.extend(top_teams)
        if exclude_bottom:
            bottom_teams = standings_df.tail(exclude_bottom)['team'].tolist()
            excluded_teams.extend(bottom_teams)
        
        # Ricalcola le classifiche escludendo solo gli scontri diretti contro le squadre escluse
        standings_data = []
        
        # Ottiene tutte le squadre originali (non filtrate)
        all_teams = set(matches_df['home_team'].unique()) | set(matches_df['away_team'].unique())
        
        for team in all_teams:
            # Per ogni squadra, calcola le statistiche escludendo solo le partite contro le squadre escluse
            team_stats = self._calculate_team_stats_with_exclusions(
                matches_df, team, standings_type, venue_filter, excluded_teams
            )
            if team_stats:
                standings_data.append(team_stats)
        
        if not standings_data:
            return pd.DataFrame()
        
        filtered_standings_df = pd.DataFrame(standings_data)
        
        # Ordina per punti e differenza reti
        if 'PT' in filtered_standings_df.columns and 'DF' in filtered_standings_df.columns:
            filtered_standings_df = filtered_standings_df.sort_values(['PT', 'DF'], ascending=[False, False])
        else:
            filtered_standings_df = filtered_standings_df.sort_values(['points', 'goal_difference'], ascending=[False, False])
        
        filtered_standings_df['PZ'] = range(1, len(filtered_standings_df) + 1)
        
        return filtered_standings_df
    
    def _calculate_team_stats_with_exclusions(self, df, team, standings_type, venue_filter, excluded_teams):
        """Calcola le statistiche per una singola squadra escludendo le partite contro le squadre escluse"""
        # Partite in casa (escludendo quelle contro squadre escluse)
        home_matches = df[(df['home_team'] == team) & (~df['away_team'].isin(excluded_teams))].copy()
        # Partite in trasferta (escludendo quelle contro squadre escluse)
        away_matches = df[(df['away_team'] == team) & (~df['home_team'].isin(excluded_teams))].copy()
        
        # Applica filtro venue
        if venue_filter == "CASA":
            away_matches = pd.DataFrame()  # Esclude partite fuori casa
        elif venue_filter == "FUORI":
            home_matches = pd.DataFrame()  # Esclude partite in casa
        
        if home_matches.empty and away_matches.empty:
            return None
        
        stats = {
            'team': team,
            'PG': 0,
            'V': 0,
            'N': 0,
            'P': 0,
            'GF': 0,
            'GS': 0,
            'DF': 0,
            'PT': 0,
            'V%': 0,
            'N%': 0,
            'P%': 0
        }
        
        # Processa partite in casa
        for _, match in home_matches.iterrows():
            stats['PG'] += 1
            
            home_goals = int(match['ft_home_goals']) if pd.notna(match['ft_home_goals']) else 0
            away_goals = int(match['ft_away_goals']) if pd.notna(match['ft_away_goals']) else 0
            
            stats['GF'] += home_goals
            stats['GS'] += away_goals
            
            if home_goals > away_goals:
                stats['V'] += 1
                stats['PT'] += 3
            elif home_goals == away_goals:
                stats['N'] += 1
                stats['PT'] += 1
            else:
                stats['P'] += 1
        
        # Processa partite in trasferta
        for _, match in away_matches.iterrows():
            stats['PG'] += 1
            
            home_goals = int(match['ft_home_goals']) if pd.notna(match['ft_home_goals']) else 0
            away_goals = int(match['ft_away_goals']) if pd.notna(match['ft_away_goals']) else 0
            
            stats['GF'] += away_goals
            stats['GS'] += home_goals
            
            if away_goals > home_goals:
                stats['V'] += 1
                stats['PT'] += 3
            elif away_goals == home_goals:
                stats['N'] += 1
                stats['PT'] += 1
            else:
                stats['P'] += 1
        
        # Calcola differenza reti
        stats['DF'] = stats['GF'] - stats['GS']
        
        # Calcola percentuali
        if stats['PG'] > 0:
            stats['V%'] = round((stats['V'] / stats['PG']) * 100, 2)
            stats['N%'] = round((stats['N'] / stats['PG']) * 100, 2)
            stats['P%'] = round((stats['P'] / stats['PG']) * 100, 2)
        
        return stats
    
    def calculate_under_over_standings(self, matches_df, threshold=2.5, venue_filter="TOTALE", time_filter="TOTALE"):
        """Calcola le classifiche Under/Over per una soglia specifica"""
        if matches_df.empty:
            return pd.DataFrame()
        
        df = matches_df.copy()
        df['ft_home_goals'] = pd.to_numeric(df['ft_home_goals'], errors='coerce')
        df['ft_away_goals'] = pd.to_numeric(df['ft_away_goals'], errors='coerce')
        df['ht_home_goals'] = pd.to_numeric(df['ht_home_goals'], errors='coerce')
        df['ht_away_goals'] = pd.to_numeric(df['ht_away_goals'], errors='coerce')
        df = df.dropna(subset=['ft_home_goals', 'ft_away_goals'])
        
        standings_data = []
        all_teams = set(df['home_team'].unique()) | set(df['away_team'].unique())
        
        for team in all_teams:
            team_stats = self._calculate_under_over_stats(df, team, threshold, venue_filter, time_filter)
            if team_stats:
                standings_data.append(team_stats)
        
        if not standings_data:
            return pd.DataFrame()
        
        standings_df = pd.DataFrame(standings_data)
        
        # Calcola percentuali
        standings_df['U%'] = standings_df.apply(lambda row: round((row['U'] / row['PG']) * 100, 2) if row['PG'] > 0 else 0, axis=1)
        standings_df['O%'] = standings_df.apply(lambda row: round((row['O'] / row['PG']) * 100, 2) if row['PG'] > 0 else 0, axis=1)
        
        # Determina "Gioca"
        standings_df['Gioca'] = standings_df.apply(
            lambda row: 'U' if row['U%'] > row['O%'] else ('O' if row['O%'] > row['U%'] else '-'), axis=1
        )
        
        # Ordina per O% decrescente
        standings_df = standings_df.sort_values(by='O%', ascending=False).reset_index(drop=True)
        
        return standings_df
    
    def _calculate_under_over_stats(self, df, team, threshold, venue_filter="TOTALE", time_filter="TOTALE"):
        """Calcola le statistiche Under/Over per una squadra"""
        home_matches = df[df['home_team'] == team]
        away_matches = df[df['away_team'] == team]
        
        if home_matches.empty and away_matches.empty:
            return None
        
        total_matches = 0
        under_matches = 0
        over_matches = 0
        goals_for = 0
        goals_against = 0
        
        # Processa partite in casa
        if venue_filter in ["TOTALE", "CASA"]:
            for _, match in home_matches.iterrows():
                # Calcola gol in base al filtro tempo
                if time_filter == "I TEMPO":
                    home_goals = match['ht_home_goals']
                    away_goals = match['ht_away_goals']
                elif time_filter == "II TEMPO":
                    home_goals = match['ft_home_goals'] - match['ht_home_goals']
                    away_goals = match['ft_away_goals'] - match['ht_away_goals']
                else:  # TOTALE
                    home_goals = match['ft_home_goals']
                    away_goals = match['ft_away_goals']
                
                # Assicurati che i gol siano numerici e non NaN
                home_goals = pd.to_numeric(home_goals, errors='coerce')
                away_goals = pd.to_numeric(away_goals, errors='coerce')
                if pd.isna(home_goals): home_goals = 0
                if pd.isna(away_goals): away_goals = 0
                
                total_goals = home_goals + away_goals
                total_matches += 1
                goals_for += home_goals
                goals_against += away_goals
                
                if total_goals < threshold:
                    under_matches += 1
                else:
                    over_matches += 1
        
        # Processa partite in trasferta
        if venue_filter in ["TOTALE", "FUORI"]:
            for _, match in away_matches.iterrows():
                # Calcola gol in base al filtro tempo
                if time_filter == "I TEMPO":
                    home_goals = match['ht_home_goals']
                    away_goals = match['ht_away_goals']
                elif time_filter == "II TEMPO":
                    home_goals = match['ft_home_goals'] - match['ht_home_goals']
                    away_goals = match['ft_away_goals'] - match['ht_away_goals']
                else:  # TOTALE
                    home_goals = match['ft_home_goals']
                    away_goals = match['ft_away_goals']
                
                # Assicurati che i gol siano numerici e non NaN
                home_goals = pd.to_numeric(home_goals, errors='coerce')
                away_goals = pd.to_numeric(away_goals, errors='coerce')
                if pd.isna(home_goals): home_goals = 0
                if pd.isna(away_goals): away_goals = 0
                
                total_goals = home_goals + away_goals
                total_matches += 1
                goals_for += away_goals  # Per la squadra in trasferta
                goals_against += home_goals
                
                if total_goals < threshold:
                    under_matches += 1
                else:
                    over_matches += 1
        
        if total_matches == 0:
            return None
        
        return {
            'team': team,
            'PG': total_matches,
            'U': under_matches,
            'O': over_matches,
            'GF': goals_for,
            'GS': goals_against,
            'G/P': round((goals_for + goals_against) / total_matches, 2) if total_matches > 0 else 0
        }
    
    def calculate_best_standings(self, matches_df, percentage_type="wins", exclude_top=None, exclude_bottom=None):
        """Calcola le classifiche BEST per percentuale specifica"""
        if percentage_type == "under_over":
            # Per Under/Over usiamo il metodo specifico
            return self.calculate_under_over_standings(matches_df)
        
        # Per le altre percentuali usiamo le classifiche normali
        standings_type = "total"
        if exclude_top or exclude_bottom:
            standings_type = "total_with_params"
        
        standings_df = self.calculate_standings(matches_df, standings_type, exclude_top, exclude_bottom)
        
        if standings_df.empty:
            return pd.DataFrame()
        
        # Ordina per la percentuale richiesta
        if percentage_type == "wins":
            standings_df = standings_df.sort_values('V%', ascending=False)
        elif percentage_type == "draws":
            standings_df = standings_df.sort_values('N%', ascending=False)
        elif percentage_type == "losses":
            standings_df = standings_df.sort_values('P%', ascending=False)
        
        standings_df['PZ'] = range(1, len(standings_df) + 1)
        
        return standings_df
    
    def get_team_last_matches(self, matches_df, team, limit=5):
        """Ottiene le ultime N partite di una squadra"""
        team_matches = matches_df[
            (matches_df['home_team'] == team) | (matches_df['away_team'] == team)
        ].copy()
        
        team_matches = team_matches.sort_values('date', ascending=False)
        return team_matches.head(limit)
    
    def get_head_to_head(self, matches_df, team1, team2, limit=5):
        """Ottiene gli ultimi N scontri diretti tra due squadre"""
        h2h_matches = matches_df[
            ((matches_df['home_team'] == team1) & (matches_df['away_team'] == team2)) |
            ((matches_df['home_team'] == team2) & (matches_df['away_team'] == team1))
        ].copy()
        
        h2h_matches = h2h_matches.sort_values('date', ascending=False)
        return h2h_matches.head(limit)
    
    def detect_team_achievements(self, standings_df, season, matches_remaining=8):
        """Rileva i traguardi raggiunti dalle squadre"""
        achievements = {}
        
        if standings_df.empty:
            return achievements
        
        # Determina le posizioni per i traguardi (esempio per Serie A)
        total_teams = len(standings_df)
        
        # Se non siamo nell'ultima stagione, assegna i traguardi normalmente
        if matches_remaining == 0:
            return self._assign_achievements_by_position(standings_df)
        
        # Per l'ultima stagione, verifica matematicamente se gli obiettivi sono raggiungibili
        return self._calculate_mathematical_achievements(standings_df, matches_remaining)
    
    def _assign_achievements_by_position(self, standings_df):
        """Assegna traguardi basandosi solo sulla posizione (stagioni concluse)"""
        achievements = {}
        total_teams = len(standings_df)
        
        # Campione (1° posto)
        if total_teams > 0:
            champion = standings_df.iloc[0]['team']
            achievements[champion] = "Campione"
        
        # Champions League (posizioni 1-4)
        for i in range(min(4, total_teams)):
            team = standings_df.iloc[i]['team']
            if team not in achievements:
                achievements[team] = "Champions League"
        
        # Europa League (posizioni 5-6)
        for i in range(4, min(6, total_teams)):
            team = standings_df.iloc[i]['team']
            if team not in achievements:
                achievements[team] = "Europa League"
        
        # Conference League (posizione 7)
        if total_teams >= 7:
            team = standings_df.iloc[6]['team']
            if team not in achievements:
                achievements[team] = "Conference League"
        
        # Retrocessioni (ultime 3 posizioni)
        for i in range(max(0, total_teams-3), total_teams):
            team = standings_df.iloc[i]['team']
            if team not in achievements:
                achievements[team] = "Retrocessa"
        
        return achievements
    
    def _calculate_mathematical_achievements(self, standings_df, matches_remaining):
        """Calcola traguardi matematicamente raggiungibili nell'ultima stagione"""
        achievements = {}
        total_teams = len(standings_df)
        
        if total_teams == 0:
            return achievements
        
        # Punti massimi possibili per ogni squadra
        max_points_per_team = {}
        for _, team in standings_df.iterrows():
            current_points = team.get('PT', 0)
            max_possible_points = current_points + (matches_remaining * 3)
            max_points_per_team[team['team']] = max_possible_points
        
        # Ordina le squadre per punti massimi possibili
        sorted_teams = sorted(max_points_per_team.items(), key=lambda x: x[1], reverse=True)
        
        # Verifica Campione (1° posto matematicamente raggiungibile)
        if len(sorted_teams) > 0:
            potential_champion = sorted_teams[0][0]
            # Verifica se nessun'altra squadra può superare questa squadra
            champion_points = max_points_per_team[potential_champion]
            can_be_overtaken = any(points > champion_points for _, points in sorted_teams[1:])
            if not can_be_overtaken:
                achievements[potential_champion] = "Campione"
        
        # Verifica Champions League (posizioni 1-4 matematicamente raggiungibili)
        for i in range(min(4, len(sorted_teams))):
            team = sorted_teams[i][0]
            if team not in achievements:
                # Verifica se questa squadra può essere superata da squadre fuori dalla top 4
                team_points = max_points_per_team[team]
                teams_behind = sorted_teams[4:] if len(sorted_teams) > 4 else []
                can_be_overtaken = any(points > team_points for _, points in teams_behind)
                if not can_be_overtaken:
                    achievements[team] = "Champions League"
        
        # Verifica Europa League (posizioni 5-6 matematicamente raggiungibili)
        for i in range(4, min(6, len(sorted_teams))):
            team = sorted_teams[i][0]
            if team not in achievements:
                team_points = max_points_per_team[team]
                teams_behind = sorted_teams[6:] if len(sorted_teams) > 6 else []
                can_be_overtaken = any(points > team_points for _, points in teams_behind)
                if not can_be_overtaken:
                    achievements[team] = "Europa League"
        
        # Verifica Conference League (posizione 7 matematicamente raggiungibile)
        if len(sorted_teams) >= 7:
            team = sorted_teams[6][0]
            if team not in achievements:
                team_points = max_points_per_team[team]
                teams_behind = sorted_teams[7:] if len(sorted_teams) > 7 else []
                can_be_overtaken = any(points > team_points for _, points in teams_behind)
                if not can_be_overtaken:
                    achievements[team] = "Conference League"
        
        # Verifica Retrocessioni (ultime 3 posizioni matematicamente raggiungibili)
        for i in range(max(0, total_teams-3), total_teams):
            team = sorted_teams[i][0]
            if team not in achievements:
                team_points = max_points_per_team[team]
                teams_ahead = sorted_teams[:i] if i > 0 else []
                can_overtake = any(points < team_points for _, points in teams_ahead)
                if not can_overtake:
                    achievements[team] = "Retrocessa"
        
        return achievements
