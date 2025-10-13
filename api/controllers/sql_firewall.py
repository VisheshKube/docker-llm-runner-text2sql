import re
from typing import Tuple, Optional
from sqlglot import parse_one, exp

FORBIDDEN = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE)\b", re.I)

def validate_sql(sql: str, allowed_tables: Optional[list[str]] = None) -> Tuple[bool, str]:
    """
    Validate SQL query:
    - Only SELECT statements allowed
    - No forbidden keywords
    - Allowed tables enforced if provided
    """
    if not sql.strip():
        return False, "Empty SQL"

    if ";" in sql:
        return False, "Multiple statements not allowed"

    if FORBIDDEN.search(sql):
        return False, "Forbidden operation detected"

    try:
        tree = parse_one(sql, read="sqlite")
    except Exception:
        return False, "Invalid SQL syntax"

    if not isinstance(tree, exp.Select):
        return False, "Only SELECT queries are allowed"

    if allowed_tables:
        for t in tree.find_all(exp.Table):
            if t.name.lower() not in [x.lower() for x in allowed_tables]:
                return False, f"Table {t.name} is not in allowlist"

    return True, "OK"
