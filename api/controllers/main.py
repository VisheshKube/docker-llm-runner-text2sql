import os, sys
import pandas as pd
import numpy as np
from typing import Any, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from api.controllers.prompt_builder import load_schema, build_prompt_with_question
from api.controllers.llm_runner import LLMRunner
from api.controllers.sql_firewall import validate_sql
from api.models.db_executor import run_sql_ro
from api.models.artifact_store import log_event, Status

LOG_PROMPT = os.getenv("LOG_PROMPT", "false").lower() == "true"

def to_serializable(obj: Any) -> Any:
    """Ensure results are JSON serializable."""
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    if isinstance(obj, (pd.Series,)):
        return obj.to_dict()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, (list, tuple)):
        return [to_serializable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    return obj

def run_pipeline(question: str) -> Dict[str, Any]:
    """
    Full pipeline: Question → Prompt → LLM → Firewall → DB → Artifact Store.
    """
    schema = load_schema()
    prompt = build_prompt_with_question(schema, question)

    runner = LLMRunner()

    try:
        sql = runner.generate_sql(schema, question)
    except Exception as e:
        log_event(question, None, None, status=Status.error,
                  prompt=prompt if LOG_PROMPT else None)
        return {
            "sql": None,
            "results": None,
            "status": "error",
            "error": f"Failed to generate SQL: {e}"
        }

    ok, reason = validate_sql(sql, schema.get("allowed_tables"))
    if not ok:
        log_event(question, sql, None, status=Status.blocked,
                  prompt=prompt if LOG_PROMPT else None)
        return {
            "sql": sql,
            "results": None,
            "status": "blocked",
            "error": reason
        }

    try:
        df, status = run_sql_ro(sql)
        results = to_serializable(df)

        log_event(
            question, sql, results,
            status=Status.success if status == "OK" else Status.error,
            prompt=prompt if LOG_PROMPT else None
        )
        return {    "sql": sql,
            "results": results,
            "status": status,
            "error": None
        }

    except Exception as e:
        log_event(
            question, sql, None,
            status=Status.error,
            prompt=prompt if LOG_PROMPT else None
        )
        return {
            "sql": sql,
            "results": None,
            "status": "error",
            "error": str(e)
        }
