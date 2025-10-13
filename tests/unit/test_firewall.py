import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from api.controllers.sql_firewall import validate_sql

# def test_sqlglot_import():
#     """Verify SQLGlot is working"""
# assert hasattr(sqlglot, 'parse_one'), "SQLGlot parse_one not found"

allowed_tables = ["customers", "orders"]

@pytest.mark.parametrize("sql, expected", [
    ("SELECT * FROM customers", True),
    ("DELETE FROM customers", False),
    ("DROP TABLE orders", False),
    ("UPDATE customers SET city='LA'", False),
    ("SELECT * FROM secret_table", False),
])
def test_firewall_rules(sql, expected):
    print(f"\nTesting SQL: {sql}")  # Debug print
    ok, reason = validate_sql(sql, allowed_tables)
    print(f"Result: {ok}, Reason: {reason}")  # Debug print
    assert ok == expected, f"Expected {expected}, got {reason}"