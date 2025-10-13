import json
from pathlib import Path
from datetime import datetime
import uuid
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, field_serializer
from enum import Enum

# Path to artifacts log file
ARTIFACTS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "artifacts.log"


# Enums & Models
class Status(str, Enum):
    """Allowed status values for query execution logs."""
    success = "success"
    blocked = "blocked"
    error = "error"


class QueryLog(BaseModel):
    """Structured representation of a query event."""
    id: str
    question: str
    prompt: Optional[str] = None  # optional
    sql: str
    results: Optional[list[dict[str, Any]]] = None
    status: Status
    timestamp: datetime

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    @field_serializer("timestamp")
    def serialize_timestamp(self, v: datetime) -> str:
        return v.isoformat()



# Functions

def log_event(
    question: str,
    sql: str,
    results: Any,
    status: Status = Status.success,
    prompt: Optional[str] = None
) -> str:
    log = QueryLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        question=question,
        prompt=prompt,
        sql=sql,
        results=results if isinstance(results, list) else None,
        status=status,
    )

    ARTIFACTS_FILE.parent.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACTS_FILE, "a", encoding="utf-8") as f:
        f.write(log.model_dump_json() + "\n")

    # print(f" Logged event → {ARTIFACTS_FILE}")
    # return log.id


def find_cached_sql(question: str) -> Optional[str]:
    """
    Look up artifacts log to find a cached SQL query for a given question.

    Args:
        question: The natural language question to look for.

    Returns:
        The most recent SQL query for the question, or None if not found.
    """
    if not ARTIFACTS_FILE.exists():
        return None

    with open(ARTIFACTS_FILE, "r", encoding="utf-8") as f:
        for line in reversed(f.readlines()):  # Search newest first
            try:
                event = json.loads(line.strip())
                if event.get("question") == question and event.get("sql"):
                    return event["sql"]
            except json.JSONDecodeError:
                continue
    return None


