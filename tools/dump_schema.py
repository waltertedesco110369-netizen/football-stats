import sys
import sqlite3
from pathlib import Path


def dump_schema(db_path: str, out_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT sql FROM sqlite_master
        WHERE sql IS NOT NULL
          AND type IN ('table','index','view','trigger')
        ORDER BY CASE type
            WHEN 'table' THEN 1
            WHEN 'index' THEN 2
            WHEN 'view' THEN 3
            WHEN 'trigger' THEN 4
        END, name
        """
    )
    sqls = [r[0] for r in rows if r[0]]
    schema = "\n\n".join(s.strip() + ";" for s in sqls)
    Path(out_path).write_text(schema, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tools/dump_schema.py <db_path> <out_path>")
        sys.exit(1)
    dump_schema(sys.argv[1], sys.argv[2])
    print(sys.argv[2])


