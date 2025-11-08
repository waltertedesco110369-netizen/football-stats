import sqlite3
import sys

# Connetti al database TEST
db_path = 'football_stats_test.db'
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ottieni struttura tabella matches
    cursor.execute('PRAGMA table_info(matches)')
    cols = cursor.fetchall()
    
    print("=" * 70)
    print("STRUTTURA TABELLA MATCHES")
    print("=" * 70)
    print(f"{'Nome Colonna':<30} | {'Tipo':<15} | {'Default':<10}")
    print("-" * 70)
    
    for col in cols:
        col_name = col[1]
        col_type = col[2]
        col_default = col[4] if col[4] else "NULL"
        print(f"{col_name:<30} | {col_type:<15} | {col_default:<10}")
    
    print("\n" + "=" * 70)
    print("TOTALE COLONNE:", len(cols))
    print("=" * 70)
    
    # Verifica se esistono colonne quote
    col_names = [col[1] for col in cols]
    
    print("\nVERIFICA COLONNE QUOTE:")
    print("-" * 70)
    quote_cols = ['quote_1', 'quote_X', 'quote_2', 'quote_home', 'quote_draw', 'quote_away',
                  'b365_home', 'b365_draw', 'b365_away', 'odds_1', 'odds_X', 'odds_2']
    
    for qc in quote_cols:
        if qc in col_names:
            print(f"✅ {qc:<30} - ESISTE")
        else:
            print(f"❌ {qc:<30} - VUOTO")
    
    conn.close()
    
except Exception as e:
    print(f"Errore: {e}")
    sys.exit(1)



