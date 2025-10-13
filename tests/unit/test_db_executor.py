import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from api.models.db_executor import run_sql_ro

def test_valid_query():
    sql = "SELECT name FROM customers LIMIT 2"
    result, status = run_sql_ro(sql)
    assert status == "OK"
    assert len(result) > 0

def test_invalid_query():
    sql = "SELECT * FROM does_not_exist"
    result, status = run_sql_ro(sql)
    assert "Error" in status

def test_join_query():
    sql = """
    SELECT c.name, o.total 
    FROM customers c 
    JOIN orders o ON c.id=o.customer_id 
    LIMIT 3
    """
    result, status = run_sql_ro(sql)
    assert status == "OK"
    assert len(result) > 0

def test_aggregate_query():
    sql = "SELECT COUNT(*) as cnt FROM customers"
    result, status = run_sql_ro(sql)
    assert status == "OK"
    # DataFrame: check first row of 'cnt'
    assert result["cnt"].iloc[0] > 0


def test_ordering_and_limit():
    sql = "SELECT name FROM customers ORDER BY id DESC LIMIT 1"
    result, status = run_sql_ro(sql)
    assert status == "OK"
    assert len(result) == 1
