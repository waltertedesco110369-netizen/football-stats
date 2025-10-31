import os
import sqlite3
from pathlib import Path

import pandas as pd

def main() -> None:
    db_path = os.environ.get("DB_PATH", "football_stats_test.db")
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database non trovato: {db_path}")

    exports_dir = Path("exports")
    exports_dir.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as con:
        # 1) Schema tabella matches
        df_schema = pd.read_sql_query("PRAGMA table_info(matches);", con)
        schema_csv = exports_dir / "matches_schema.csv"
        df_schema.to_csv(schema_csv, index=False, encoding="utf-8")

        # 2) Un record stagione 2025-2026
        df_2025 = pd.read_sql_query(
            """
            SELECT season, div, date, time, home_team, away_team,
                   ft_home_goals, ft_away_goals, ft_result
            FROM matches
            WHERE season = '2025-2026'
            LIMIT 1;
            """,
            con,
        )
        sample_2025_csv = exports_dir / "sample_2025_2026.csv"
        df_2025.to_csv(sample_2025_csv, index=False, encoding="utf-8")

        # 3) Un record importato dai file multi-stagione temp_new_leagues_data
        df_temp = pd.read_sql_query(
            """
            SELECT season, div, date, time, home_team, away_team,
                   ft_home_goals, ft_away_goals, ft_result, file_source
            FROM matches
            WHERE file_source LIKE 'temp_new_leagues_data%'
            LIMIT 1;
            """,
            con,
        )
        sample_temp_csv = exports_dir / "sample_temp_new_leagues.csv"
        df_temp.to_csv(sample_temp_csv, index=False, encoding="utf-8")

    # Prova a creare anche un unico file Excel (se disponibile openpyxl)
    xlsx_path = exports_dir / "verifica.xlsx"
    try:
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            df_schema.to_excel(writer, sheet_name="schema_matches", index=False)
            df_2025.to_excel(writer, sheet_name="sample_2025_2026", index=False)
            df_temp.to_excel(writer, sheet_name="sample_temp_new", index=False)
        print(f"Creato Excel: {xlsx_path}")
    except Exception as exc:
        print(
            "Impossibile creare XLSX (manca openpyxl?). Proseguo solo con i CSV.",
            f"Dettagli: {exc}",
        )

    print("File generati:")
    print(f" - {schema_csv}")
    print(f" - {sample_2025_csv}")
    print(f" - {sample_temp_csv}")
    if xlsx_path.exists():
        print(f" - {xlsx_path}")


if __name__ == "__main__":
    main()


