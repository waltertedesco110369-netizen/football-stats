import sqlite3
import pandas as pd
import os

DB_PATH = os.environ.get('DB_PATH', 'football_stats_test.db')

print('DB:', DB_PATH, 'exists:', os.path.exists(DB_PATH))
con = sqlite3.connect(DB_PATH)
cur = con.cursor()

print('\n-- SCHEMA matches --')
for r in cur.execute('PRAGMA table_info(matches)'):
    print(r)

print('\n-- Distinct seasons sample --')
print(pd.read_sql_query('SELECT DISTINCT season FROM matches ORDER BY season DESC LIMIT 10', con))

print('\n-- Count by season/div (top 20) --')
print(pd.read_sql_query('SELECT season, div, COUNT(*) as n FROM matches GROUP BY season, div ORDER BY season DESC, n DESC LIMIT 20', con))

print('\n-- Sample rows 2025-2026 --')
print(pd.read_sql_query("SELECT season, div, date, home_team, away_team, ft_home_goals, ft_away_goals, ft_result FROM matches WHERE season = '2025-2026' LIMIT 5", con))

con.close()
