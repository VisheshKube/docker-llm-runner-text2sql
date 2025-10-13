# api/prompt_builder.py
"""
Prompt Builder
- Loads schema from metastore.yaml
- Builds strict system prompts for Text-to-SQL generation
"""

import yaml
from pathlib import Path

SCHEMA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "metastore.yaml"


def load_schema():
    """Load schema definition from YAML metastore."""
    with open(SCHEMA_FILE, "r") as f:
        return yaml.safe_load(f)

def build_system_prompt(schema: dict) -> str:
    """
    Build a strict system prompt from schema.
    Enforces rules: only SELECT, no hallucinations, no unnecessary joins.
    """
    lines = [
        "You are a SQL generator.",
        "STRICT RULES:",
        "1. You must ONLY output one single valid SQL SELECT query.",
        "2. Never output INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or TRUNCATE.",
        "3. Do not output multiple statements, semicolons, comments, or explanations.",
        "4. Only use the tables and columns listed in the schema below.",
        "5. Only use joins explicitly listed in 'Joins allowed'.",
        "6. Do not invent tables, columns, joins, or functions not listed in the schema.",
        "7. Use short aliases (c, o, p) when joining tables.",
        "8. Ensure SQL is syntactically valid for SQLite.",
        "9. Do not output natural language — output SQL only.",
        "10. Output ends immediately after the SQL query (no trailing text).",
        "",
        "Schema:",
    ]

    # Add tables
    for table, info in schema["tables"].items():
        lines.append(f"Table: {table} -- {info['description']}")
        for col, desc in info["columns"].items():
            lines.append(f"  - {col}: {desc}")
        lines.append("")

    # Add allowed joins
    if "joins" in schema:
        lines.append("Joins allowed:")
        for j in schema["joins"]:
            lines.append(f"  - {j}")
        lines.append("")

    # Add allowed tables if defined
    if "allowed_tables" in schema:
        lines.append("Only use these tables:")
        for t in schema["allowed_tables"]:
            lines.append(f"  - {t}")
        lines.append("")

    return "\n".join(lines)



def build_prompt_with_question(schema: dict, question: str) -> str:
    """Combine schema prompt with user question into final input."""
    system_prompt = build_system_prompt(schema)
    return f"""{system_prompt}

User Question:
{question}

SQL:
"""



