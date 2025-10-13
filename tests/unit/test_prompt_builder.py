import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from api.controllers.prompt_builder import load_schema, build_prompt_with_question

def test_schema_loads():
    schema = load_schema()
    assert "tables" in schema
    assert "customers" in schema["tables"]

def test_prompt_contains_question():
    schema = load_schema()
    prompt = build_prompt_with_question(schema, "Show all customers")
    assert "User Question:" in prompt
    assert "Show all customers" in prompt

def test_prompt_contains_tables_and_columns():
    schema = load_schema()
    prompt = build_prompt_with_question(schema, "dummy")
    for table, info in schema["tables"].items():
        assert table in prompt
        for col in info["columns"].keys():
            assert col in prompt

def test_prompt_contains_joins_if_any():
    schema = load_schema()
    if "joins" in schema:
        prompt = build_prompt_with_question(schema, "dummy")
        for join in schema["joins"]:
            assert join in prompt
