import glob
import os
from datetime import datetime
from pathlib import Path

from dump_schema import dump_schema  # reuse helper


def main():
    Path("backups").mkdir(parents=True, exist_ok=True)
    db_files = [
        *glob.glob("football_stats_*.db"),
    ]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    wrote_any = False
    for db in db_files:
        out = Path("backups") / f"schema_{Path(db).name}_{timestamp}.sql"
        try:
            dump_schema(db, str(out))
            print(str(out))
            wrote_any = True
        except Exception as exc:
            print(f"ERROR dumping {db}: {exc}")
    if not wrote_any:
        print("No matching DB files found (football_stats_*.db)")


if __name__ == "__main__":
    main()


