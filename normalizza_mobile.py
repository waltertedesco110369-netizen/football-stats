#!/usr/bin/env python3
"""Normalizza stagioni nel database MOBILE"""
import sqlite3

con = sqlite3.connect('football_stats_mobile.db')
cur = con.cursor()

# 1. Slash -> trattino
cur.execute("UPDATE matches SET season = REPLACE(season, '/', '-') WHERE season LIKE '%/%'")
s1 = cur.rowcount

# 2. Anno singolo -> range
cur.execute("UPDATE matches SET season = CAST(season AS INTEGER) || '-' || CAST(CAST(season AS INTEGER)+1 AS TEXT) WHERE TRIM(season) GLOB '[0-9][0-9][0-9][0-9]'")
s2 = cur.rowcount

con.commit()
print(f'✅ Stagioni normalizzate su MOBILE: slash->dash={s1}, anno->range={s2}')
con.close()

