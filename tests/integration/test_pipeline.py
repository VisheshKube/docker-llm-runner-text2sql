import os
import sys
import pytest
import pandas as pd
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from api.controllers.prompt_builder import load_schema, build_prompt_with_question
from api.controllers.sql_firewall import validate_sql
from api.models.db_executor import run_sql_ro
from api.controllers.main import run_pipeline


@pytest.mark.parametrize("sql", [
    "SELECT * FROM customers",
    "SELECT name, city FROM customers WHERE city='New York'",
    "SELECT c.name, SUM(o.total) as total_spent FROM customers c "
    "JOIN orders o ON c.id=o.customer_id GROUP BY c.name LIMIT 5"
])
def test_pipeline_various_queries(sql):
    """Ensure different valid queries pass firewall and run in DB."""
    schema = load_schema()

    # Firewall validation
    ok, reason = validate_sql(sql, schema["allowed_tables"])
    assert ok, f"Firewall blocked query: {reason}"

    # DB execution
    result, status = run_sql_ro(sql)
    assert status == "OK"
    assert isinstance(result, (pd.DataFrame, list))
    assert len(result) > 0


def test_pipeline_forbidden_sql():
    """Ensure forbidden SQL is blocked by firewall."""
    schema = load_schema()
    sql = "DROP TABLE customers"  # not allowed
    ok, reason = validate_sql(sql, schema["allowed_tables"])
    assert not ok
    # flexible assertion so any forbidden message works
    assert "forbidden" in reason.lower()


def test_pipeline_with_fake_llm():
    """Simulate an LLM output via patch and run the real pipeline."""
    with patch("api.controllers.llm_runner.LLMRunner.generate_sql", return_value="SELECT * FROM customers"):
        result = run_pipeline("Show all customers")
        assert "sql" in result
        assert "results" in result
        # results may be a DataFrame or list of dicts
        assert isinstance(result["results"], (list, pd.DataFrame))
        assert len(result["results"]) > 0


def test_pipeline_db_error_handling():
    """Simulate bad SQL from LLM and ensure DB errors are handled gracefully."""
    with patch("api.controllers.llm_runner.LLMRunner.generate_sql", return_value="SELECT * FROM does_not_exist"):
        result = run_pipeline("nonexistent table")
        assert "sql" in result
        assert "results" in result
        # Accept either 'status' (success path) or 'error' (failure path)
        assert "status" in result or "error" in result
        if "error" in result:
            assert result["results"] is None or result["results"] == []
        else:
            assert result["results"] == [] or result["status"].lower().startswith("error")

