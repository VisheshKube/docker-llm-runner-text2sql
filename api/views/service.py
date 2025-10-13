import os, sys
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Any, List, Dict, Optional

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from api.controllers.main import run_pipeline


from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Optional
from api.controllers.main import run_pipeline

app = FastAPI(title="Private AI-SQL Service")

#pydantic models for request and response
class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    sql: str
    results: Any
    status: Optional[str] = None
    error: Optional[str] = None


app = FastAPI(title="Text-to-SQL API")


@app.get("/health")
def health() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    """
    Handle natural language query → SQL pipeline.
    """
    result = run_pipeline(req.question)
   
    return QueryResponse(**result)
