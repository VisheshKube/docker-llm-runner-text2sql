import sqlite3
from pathlib import Path
import pandas as pd
from typing import Tuple, Union, List, Any

# Path to SQLite DB file
DB_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "demo.db"


def run_sql_ro(sql: str) -> Tuple[Union[pd.DataFrame, List[Any]], str]:
    """
    Execute a SQL query against SQLite in read-only mode.
    Returns:
          - results: A Pandas DataFrame (if conversion works) or raw rows (list of tuples).
          - status: "OK" if success, or an error string if failure.
    """
    conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
    cur = conn.cursor()

    try:
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
    except sqlite3.Error as e:
        conn.close()
        return [], f"DB Error: {e}"

    conn.close()

    # Try to return results as DataFrame; fallback to raw rows
    try:
        df = pd.DataFrame(rows, columns=cols)
        return df, "OK"
    except Exception:
        return rows, "OK"


if __name__ == "__main__":
    # Quick manual test
    query = "SELECT name, city FROM customers LIMIT 5"
    results, status = run_sql_ro(query)
    # print results

