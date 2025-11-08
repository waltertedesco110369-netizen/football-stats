"""
Script semplice: legge Excel convertito e crea Excel compatibile per importazione
Formato identico a new_leagues_data.xlsx
"""
import pandas as pd
import re
from datetime import datetime
import os
import sys

def converti_excel_compatibile(excel_convertito_path, output_path=None):
    """
    Legge Excel convertito e crea Excel compatibile con il database
    Formato: League, Season, Date, Time, Home, Away, quote...
    """
    
    if not os.path.exists(excel_convertito_path):
        print(f"❌ ERRORE: File non trovato: {excel_convertito_path}")
        return None
    
    # Path output se non specificato
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(excel_convertito_path))[0]
        output_path = f"Import/Database/File/{base_name}_compatibile.xlsx"
    
    print(f"📖 Leggo file: {excel_convertito_path}")
    
    # Leggi Excel convertito (senza header per trovare intestazioni)
    df_raw = pd.read_excel(excel_convertito_path, sheet_name=0, header=None)
    
    # Trova riga intestazioni (cerca "Ora", "Manif", "Squadra 1")
    riga_intestazioni = None
    for idx in range(min(5, len(df_raw))):
        row_values = [str(v).strip() if pd.notna(v) else '' for v in df_raw.iloc[idx]]
        if any('ora' in str(v).lower() or 'manif' in str(v).lower() or 'squadra' in str(v).lower() 
               for v in row_values[:10]):
            riga_intestazioni = idx
            break
    
    if riga_intestazioni is None:
        print("❌ ERRORE: Intestazioni non trovate")
        return None
    
    # Leggi con intestazioni dalla riga trovata
    df = pd.read_excel(excel_convertito_path, sheet_name=0, header=riga_intestazioni)
    
    # Estrai data italiana (cerca "sabato, 1 novembre")
    giorni_it = r"lunedì|lunedi|martedì|martedi|mercoledì|mercoledi|giovedì|giovedi|venerdì|venerdi|sabato|domenica"
    mesi_it = "gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre"
    date_header_re = re.compile(fr"^(?:{giorni_it})\s*,\s*(\d{{1,2}})\s+({mesi_it})$", re.IGNORECASE)
    
    month_map = {
        'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4, 'maggio': 5, 'giugno': 6,
        'luglio': 7, 'agosto': 8, 'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
    }
    
    current_year = datetime.now().year
    current_date = None
    current_season = str(current_year)
    
    # Cerca data nel file
    df_raw_check = pd.read_excel(excel_convertito_path, sheet_name=0, header=None, nrows=10)
    for idx in range(len(df_raw_check)):
        for val in df_raw_check.iloc[idx]:
            if pd.notna(val):
                match = date_header_re.match(str(val).strip())
                if match:
                    dd = int(match.group(1))
                    mm_name = match.group(2).lower()
                    mm = month_map.get(mm_name)
                    if mm:
                        current_date = f"{current_year}-{mm:02d}-{dd:02d}"
                        current_season = str(current_year)
                        break
        if current_date:
            break
    
    # Cerca colonne per nome
    def trova_col(df, nomi_possibili):
        for nome in nomi_possibili:
            for col in df.columns:
                if nome.lower() in str(col).lower():
                    return col
        return None
    
    ora_col = trova_col(df, ['Ora', 'Time', 'ora', 'time'])
    manif_col = trova_col(df, ['Manif', 'Manif.', 'League', 'league'])
    pal_col = trova_col(df, ['Pal', 'Pal.', 'pal'])
    avv_col = trova_col(df, ['Avv', 'Avv.', 'avv'])
    squadra1_col = trova_col(df, ['Squadra 1', 'Home', 'home', 'Squadra1'])
    squadra2_col = trova_col(df, ['Squadra 2', 'Away', 'away', 'Squadra2'])
    live_col = trova_col(df, ['LIVE', 'Live', 'live', 'L I V E'])
    
    # Estrai dati
    dati_compatibili = []
    
    for idx, row in df.iterrows():
        # Skip righe vuote
        if row.isna().all():
            continue
        
        # Estrai dati base
        ora_raw = str(row[ora_col]).strip() if ora_col and pd.notna(row[ora_col]) else ''
        manif = str(row[manif_col]).strip() if manif_col and pd.notna(row[manif_col]) else ''
        pal_raw = str(row[pal_col]).strip() if pal_col and pd.notna(row[pal_col]) else ''
        avv_raw = str(row[avv_col]).strip() if avv_col and pd.notna(row[avv_col]) else ''
        
        # Formatta orario: 21.05 → 21:05, 21.3 → 21:30, 22 → 22:00
        ora = ''
        if ora_raw:
            ora_raw = ora_raw.replace(',', '.').replace(':', '.')
            try:
                # Se ha punto decimale
                if '.' in ora_raw:
                    parts = ora_raw.split('.')
                    hh = int(float(parts[0]))
                    if len(parts) > 1:
                        mm_str = parts[1].strip()
                        if len(mm_str) == 1:
                            mm = int(mm_str) * 10  # 21.3 → 21:30
                        else:
                            mm = int(mm_str[:2])  # 21.05 → 21:05
                    else:
                        mm = 0
                    ora = f"{hh:02d}:{mm:02d}"
                else:
                    # Solo numero (22 → 22:00)
                    hh = int(float(ora_raw))
                    ora = f"{hh:02d}:00"
            except:
                ora = ora_raw
        
        # Pal e Avv: rimuovi .0, converti in intero
        pal = ''
        if pal_raw:
            try:
                pal = str(int(float(pal_raw.replace(',', '.'))))
            except:
                pal = pal_raw.replace('.0', '').replace(',', '')
        
        avv = ''
        if avv_raw:
            try:
                avv = str(int(float(avv_raw.replace(',', '.'))))
            except:
                avv = avv_raw.replace('.0', '').replace(',', '')
        squadra1 = str(row[squadra1_col]).strip() if squadra1_col and pd.notna(row[squadra1_col]) else ''
        squadra2 = str(row[squadra2_col]).strip() if squadra2_col and pd.notna(row[squadra2_col]) else ''
        live = 'LIVE' if (live_col and pd.notna(row[live_col]) and 'LIVE' in str(row[live_col]).upper()) else ''
        
        # Skip se mancano dati essenziali
        if not ora or not manif or not squadra1 or not squadra2:
            continue
        
        # Formatta orario (verifica finale)
        if '.' in ora and ':' not in ora:
            # Se ancora ha punto, converti
            try:
                parts = ora.split('.')
                hh = int(float(parts[0]))
                if len(parts) > 1:
                    mm_str = parts[1].strip()
                    if len(mm_str) == 1:
                        mm = int(mm_str) * 10
                    else:
                        mm = int(mm_str[:2])
                else:
                    mm = 0
                ora = f"{hh:02d}:{mm:02d}"
            except:
                pass
        
        # Mantieni manif con il numero (FRA1, FRA2, PER1, ecc.) - sono campionati diversi!
        manif_clean = manif.upper().strip()
        
        # Estrai quote (dalla colonna 7 in poi, dopo LIVE)
        colonne_ordine = list(df.columns)
        start_idx = 7  # Dopo Ora, Manif, Pal, Avv, Squadra1, Squadra2, LIVE
        
        colonne_quote = [
            'quota_1', 'quota_X', 'quota_2', 'H', 'H1', 'HX', 'H2',
            '1X', 'X2', '12',
            'uo_1_5_u', 'uo_1_5_o', 'uo_2_5_u', 'uo_2_5_o', 'uo_3_5_u', 'uo_3_5_o',
            'G', 'NO_G', 'C_SI', 'C_NO', 'O_SI', 'O_NO'
        ]
        
        quote = {}
        for i, col_quote in enumerate(colonne_quote):
            col_idx = start_idx + i
            if col_idx < len(colonne_ordine):
                col_name = colonne_ordine[col_idx]
                val = row[col_name]
                if pd.notna(val):
                    val_str = str(val).strip().replace(',', '.')
                    try:
                        quote[col_quote] = float(val_str)
                    except:
                        try:
                            quote[col_quote] = int(val_str)
                        except:
                            pass
        
        # Crea record compatibile
        record = {
            'League': manif_clean,
            'Season': current_season,
            'Date': current_date or '',
            'Time': ora,
            'Home': squadra1,
            'Away': squadra2,
            'HG': None,
            'AG': None,
            'Res': None,
            'Live': live,
            'pal': pal,
            'avv': avv,
            **quote
        }
        
        dati_compatibili.append(record)
    
    if not dati_compatibili:
        print("❌ ERRORE: Nessun dato trovato")
        return None
    
    # Crea DataFrame compatibile
    df_compatibile = pd.DataFrame(dati_compatibili)
    
    # Ordina colonne come new_leagues_data
    colonne_ordine = ['League', 'Season', 'Date', 'Time', 'Home', 'Away', 'HG', 'AG', 'Res', 'Live',
                      'quota_1', 'quota_X', 'quota_2', 'H', 'H1', 'HX', 'H2', '1X', 'X2', '12',
                      'uo_1_5_u', 'uo_1_5_o', 'uo_2_5_u', 'uo_2_5_o', 'uo_3_5_u', 'uo_3_5_o',
                      'G', 'NO_G', 'C_SI', 'C_NO', 'O_SI', 'O_NO', 'pal', 'avv']
    
    # Aggiungi colonne mancanti
    for col in colonne_ordine:
        if col not in df_compatibile.columns:
            df_compatibile[col] = None
    
    # Riordina colonne
    df_compatibile = df_compatibile[[col for col in colonne_ordine if col in df_compatibile.columns]]
    
    # Salva Excel compatibile
    df_compatibile.to_excel(output_path, index=False, sheet_name='Sheet1')
    
    print(f"✓ File compatibile creato: {output_path}")
    print(f"  Righe: {len(df_compatibile)}")
    print(f"  Colonne: {len(df_compatibile.columns)}")
    print(f"\n✅ FATTO! Ora puoi importare questo file direttamente nell'applicazione.")
    
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python converti_excel_compatibile.py <file_excel_convertito>")
        print("\nEsempio:")
        print("  python converti_excel_compatibile.py \"Import/Database/File/calcio base per data (2).xlsx\"")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    converti_excel_compatibile(excel_file)

