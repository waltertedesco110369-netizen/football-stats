import sqlite3
import pandas as pd


def main(db_path: str = 'football_stats_test.db') -> None:
    con = sqlite3.connect(db_path)
    def show(title: str, query: str) -> None:
        print(f"\n=== {title} ===")
        try:
            df = pd.read_sql_query(query, con)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"Errore: {e}")

    show(
        'DISTINCT div (ALL)',
        "SELECT TRIM(div) AS div, COUNT(*) as n FROM matches GROUP BY TRIM(div) ORDER BY div",
    )
    show(
        'new_leagues_data divisions',
        "SELECT TRIM(div) AS div, COUNT(*) as n FROM matches WHERE file_source LIKE 'new_leagues_data%' GROUP BY TRIM(div) ORDER BY div",
    )
    show(
        'Empty or NULL div rows',
        "SELECT COUNT(*) as empty_div FROM matches WHERE div IS NULL OR TRIM(div)=''",
    )
    show(
        'Seasons per div (sample new_leagues)',
        "SELECT season, TRIM(div) AS div, COUNT(*) n FROM matches WHERE file_source LIKE 'new_leagues_data%' GROUP BY season, TRIM(div) ORDER BY season DESC, div LIMIT 100",
    )
    con.close()


if __name__ == '__main__':
    main()


