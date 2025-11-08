#!/usr/bin/env python3
"""Genera un file Excel "delta" con sole le righe nuove rispetto al database locale.

Esempio d'uso:

    python tools/genera_delta_import.py \
        --db football_stats_test.db \
        --input "Import/Database/File/new_leagues_data.xlsx" \
        --output "Import/Database/File/new_leagues_data_delta.xlsx"

Lo script replica la logica di normalizzazione usata durante l'import
per calcolare la chiave partita (home_team, away_team, date, time) e
filtra stagioni <= 2019-2020.
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import sqlite3
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

import pandas as pd

from database import MAPPA_LEAGUE_PDF, MAPPATURE_DISPONIBILI

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def rileva_mappatura(df: pd.DataFrame) -> Optional[str]:
    """Replica della logica in `FootballDatabase.rileva_mappatura`."""
    colonne_file = set(df.columns)

    migliore_match = None
    max_corrispondenze = 0

    for nome_mappatura, mappatura in MAPPATURE_DISPONIBILI.items():
        colonne_mappatura = set(mappatura.keys())
        corrispondenze = len(colonne_file.intersection(colonne_mappatura))

        if corrispondenze > max_corrispondenze:
            max_corrispondenze = corrispondenze
            migliore_match = nome_mappatura

    percentuale = (
        (max_corrispondenze / len(colonne_file)) * 100 if len(colonne_file) > 0 else 0
    )
    logger.info(
        "Mappatura rilevata: %s (%d/%d colonne - %.1f%%)",
        migliore_match,
        max_corrispondenze,
        len(colonne_file),
        percentuale,
    )
    return migliore_match


def _to_float_or_none(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s:
        return None
    s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def _normalize_string(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def converti_stagione(stagione_str: object) -> Optional[str]:
    if pd.isna(stagione_str) or stagione_str == "None":
        return None

    stagione_str = str(stagione_str).strip()
    if not stagione_str:
        return None

    stagione_str = stagione_str.replace("/", "-").replace(".", "-")

    if "-" in stagione_str:
        return stagione_str

    if stagione_str.isdigit() and len(stagione_str) == 4:
        anno = int(stagione_str)
        return f"{anno}-{anno + 1}"

    return stagione_str


def carica_file_input(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        df["__sheet_name"] = "CSV"
        logger.info("File CSV caricato: %d righe", len(df))
        return df

    excel_file = pd.ExcelFile(path)
    logger.info("File Excel caricato - Fogli: %d", len(excel_file.sheet_names))

    all_sheets = []
    for sheet_name in excel_file.sheet_names:
        df_sheet = pd.read_excel(path, sheet_name=sheet_name)
        df_sheet["__sheet_name"] = str(sheet_name)
        logger.info("Foglio %s: %d righe", sheet_name, len(df_sheet))
        all_sheets.append(df_sheet)

    df_all = pd.concat(all_sheets, ignore_index=True)
    logger.info("Totale righe da tutti i fogli: %d", len(df_all))
    return df_all


def costruisci_dataframe_normalizzato(
    df: pd.DataFrame,
    file_path: Path,
    mappatura_nome: Optional[str],
) -> pd.DataFrame:
    if not mappatura_nome:
        raise RuntimeError("Impossibile determinare la mappatura da utilizzare")

    mappatura = MAPPATURE_DISPONIBILI.get(mappatura_nome)
    if not mappatura:
        raise RuntimeError(f"Mappatura {mappatura_nome} non trovata")

    df_normalizzato = pd.DataFrame(index=df.index)

    for colonna_orig, colonna_dest in mappatura.items():
        if colonna_orig in df.columns:
            df_normalizzato[colonna_dest] = df[colonna_orig]
        else:
            df_normalizzato[colonna_dest] = None

    # Quote opzionali (convertite in float) - solo se esistono
    for extra in [
        "quota_1",
        "quota_X",
        "quota_2",
        "uo_1_5_u",
        "uo_1_5_o",
        "uo_2_5_u",
        "uo_2_5_o",
        "uo_3_5_u",
        "uo_3_5_o",
        "live",
        "h",
        "h1",
        "hx",
        "h2",
        "dc_1x",
        "dc_x2",
        "dc_12",
        "g",
        "no_g",
        "c_si",
        "c_no",
        "o_si",
        "o_no",
    ]:
        if extra in df.columns:
            df_normalizzato[extra] = df[extra].apply(_to_float_or_none)

    if "div" in df_normalizzato.columns:
        df_normalizzato["div"] = df_normalizzato["div"].astype(str).str.strip()
        mask_league = df_normalizzato["div"].notna() & (df_normalizzato["div"] != "")
        df_normalizzato.loc[mask_league, "div"] = df_normalizzato.loc[mask_league, "div"].apply(
            lambda x: MAPPA_LEAGUE_PDF.get(str(x).upper().strip(), str(x).strip())
        )

        if "__sheet_name" in df.columns:
            mask_missing_div = df_normalizzato["div"].isna() | (
                df_normalizzato["div"] == ""
            ) | (df_normalizzato["div"].str.lower() == "none")
            df_normalizzato.loc[mask_missing_div, "div"] = (
                df.loc[mask_missing_div, "__sheet_name"].astype(str).str.strip()
            )

    nome_file = os.path.basename(file_path)
    stagione_impostata = None

    if mappatura_nome == "standard":
        match = re.search(r"(\d{4})-(\d{4})", nome_file)
        if match:
            stagione_impostata = f"{match.group(1)}-{match.group(2)}"
            df_normalizzato["season"] = stagione_impostata
            logger.info("[standard] Stagione forzata dal nome file: %s", stagione_impostata)

    if "season" in df_normalizzato.columns:
        if stagione_impostata is None:
            df_normalizzato["season"] = df_normalizzato["season"].apply(converti_stagione)
        else:
            df_normalizzato["season"] = df_normalizzato["season"].apply(converti_stagione)

    if "season" in df_normalizzato.columns:
        df_normalizzato = df_normalizzato[df_normalizzato["season"].notna()].copy()

    if "season" in df_normalizzato.columns:
        prima = len(df_normalizzato)
        df_normalizzato = df_normalizzato[df_normalizzato["season"] > "2019-2020"].copy()
        scartate = prima - len(df_normalizzato)
        if scartate > 0:
            logger.warning("%d partite scartate (stagioni <= 2019-2020 o mancanti)", scartate)
        logger.info("Partite valide dopo filtro stagione: %d", len(df_normalizzato))

    for col in ["date", "time", "season"]:
        if col in df_normalizzato.columns:
            df_normalizzato[col] = df_normalizzato[col].astype(str)

    df_normalizzato["file_source"] = nome_file
    return df_normalizzato


def costruisci_delta(
    df_originale: pd.DataFrame,
    df_normalizzato: pd.DataFrame,
    existing_with_time: Set[Tuple[str, str, str, str]],
    existing_without_time: Set[Tuple[str, str, str]],
) -> pd.DataFrame:
    df = df_originale.copy()
    df["__is_new"] = False

    for idx, row in df_normalizzato.iterrows():
        home = _normalize_string(row.get("home_team"))
        away = _normalize_string(row.get("away_team"))
        date = _normalize_string(row.get("date"))

        if not home or not away or not date:
            continue

        time_val = _normalize_string(row.get("time")) if "time" in row else ""
        time_val = time_val if time_val and time_val.lower() not in {"none", "nan"} else ""

        if time_val:
            key = (home, away, date, time_val)
            if key not in existing_with_time:
                df.at[idx, "__is_new"] = True
        else:
            key = (home, away, date)
            if key not in existing_without_time:
                df.at[idx, "__is_new"] = True

    delta_df = df[df["__is_new"]].drop(columns=["__is_new"], errors="ignore")
    if "__sheet_name" in delta_df.columns:
        delta_df = delta_df.drop(columns=["__sheet_name"], errors="ignore")

    # Rimuovi colonne helper interne (se presenti)
    for helper in ["__row_id", "__chiave"]:
        if helper in delta_df.columns:
            delta_df = delta_df.drop(columns=[helper])

    # Evita duplicati interni al delta
    chiave_cols = [col for col in ["HomeTeam", "AwayTeam", "Date", "Time"] if col in delta_df.columns]
    if chiave_cols:
        delta_df = delta_df.drop_duplicates(subset=chiave_cols)

    return delta_df


def carica_chiavi_database(conn: sqlite3.Connection) -> Tuple[
    Set[Tuple[str, str, str, str]],
    Set[Tuple[str, str, str]],
]:
    query = "SELECT home_team, away_team, date, time FROM matches"
    df_db = pd.read_sql_query(query, conn)

    with_time = set()
    without_time = set()

    for _, row in df_db.iterrows():
        home = _normalize_string(row.get("home_team"))
        away = _normalize_string(row.get("away_team"))
        date = _normalize_string(row.get("date"))
        time_val = _normalize_string(row.get("time"))

        if not home or not away or not date:
            continue

        if time_val and time_val.lower() not in {"none", "nan"}:
            with_time.add((home, away, date, time_val))
        else:
            without_time.add((home, away, date))

    logger.info("Partite presenti nel database: %d", len(df_db))
    return with_time, without_time


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera un file delta da importare su Render")
    parser.add_argument(
        "--db",
        default="football_stats_test.db",
        help="Percorso al database locale su cui confrontare (default: football_stats_test.db)",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="File Excel/CSV completo da confrontare",
    )
    parser.add_argument(
        "--output",
        help="Percorso del file delta da generare (se omesso viene aggiunto _delta.xlsx)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise FileNotFoundError(f"Database non trovato: {db_path}")

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"File di input non trovato: {input_path}")

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_name(f"{input_path.stem}_delta.xlsx")

    df_originale = carica_file_input(input_path)
    if df_originale.empty:
        logger.warning("Il file di input è vuoto. Nessun delta generato.")
        return

    mappatura_nome = rileva_mappatura(df_originale.drop(columns=["__sheet_name"], errors="ignore"))
    df_normalizzato = costruisci_dataframe_normalizzato(df_originale, input_path, mappatura_nome)

    with sqlite3.connect(db_path) as conn:
        existing_with_time, existing_without_time = carica_chiavi_database(conn)

    delta_df = costruisci_delta(df_originale, df_normalizzato, existing_with_time, existing_without_time)

    if delta_df.empty:
        logger.info("Nessuna nuova riga trovata. Nessun file generato.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() == ".csv":
        delta_df.to_csv(output_path, index=False)
    else:
        delta_df.to_excel(output_path, index=False)

    logger.info("Delta generato: %s (%d righe)", output_path, len(delta_df))


if __name__ == "__main__":
    main()
