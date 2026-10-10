"""
main.py  -  Budget Transparency Explorer (SDG 16)
Builds budget.db from the CSVs and runs every query in sql/queries.sql.

Run:  python generate_sample_data.py  then  python main.py
"""

import csv
import math
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DB_PATH = ROOT / "budget.db"
TABLES = {"states": ["state_id", "name", "population"],
          "sectors": ["sector_id", "name", "sdg"],
          "budget_lines": ["year", "state_id", "sector_id", "allocated", "released", "spent"]}


def connect(path):
    """Open the database and add a sqrt() function, which some SQLite builds lack."""
    conn = sqlite3.connect(path)
    conn.create_function("sqrt", 1, lambda x: math.sqrt(x) if x and x > 0 else None)  # name, number of args, Python function
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def load(conn):
    conn.executescript((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
    for table, cols in TABLES.items():                         # dicts keep insertion order: parents first
        with open(ROOT / "data" / f"{table}.csv", newline="", encoding="utf-8") as f:
            rows = [[r[c] for c in cols] for r in csv.DictReader(f)]
        conn.executemany(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", rows)
    conn.commit()


def split_queries(text):
    """Split queries.sql into (title, sql) pairs on '-- name:' lines."""
    out, title, lines = [], None, []
    for line in text.splitlines():
        if line.startswith("-- name:"):
            if title:
                out.append((title, "\n".join(lines)))
            title, lines = line.removeprefix("-- name:").strip(), []
        elif title:
            lines.append(line)
    if title:
        out.append((title, "\n".join(lines)))
    return out


def show(title, cur):
    headers = [d[0] for d in cur.description]
    rows = [["" if v is None else str(v) for v in r] for r in cur.fetchall()]
    print(f"\n=== {title} ===")
    if not rows:
        print("(none)")
        return
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    for r in rows:
        print("  ".join(v.ljust(w) for v, w in zip(r, widths)))


def main():
    if not (ROOT / "data" / "budget_lines.csv").exists():
        sys.exit("No data. Run: python generate_sample_data.py")
    conn = connect(DB_PATH)
    load(conn)
    for title, sql in split_queries((ROOT / "sql" / "queries.sql").read_text(encoding="utf-8")):
        show(title, conn.execute(sql))
    conn.close()
    print(f"\nDatabase saved to {DB_PATH.name}")


if __name__ == "__main__":
    main()
