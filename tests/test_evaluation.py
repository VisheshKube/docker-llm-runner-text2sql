# tests/evaluate.py

import os, sys, time, yaml, re
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from api.controllers.prompt_builder import load_schema
from api.controllers.llm_runner import LLMRunner
from api.controllers.sql_firewall import validate_sql
from dotenv import load_dotenv
load_dotenv()

QUESTIONS_FILE = "data/questions.yaml"

# Parse model lists from env
HF_MODELS = os.getenv("HF_MODELS", "").split(",")

# Use env var if set, else fall back to defaults
OLLAMA_MODELS = os.getenv("OLLAMA_MODELS", "mistral:latest").split(",")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://model-runner:11434")

CONFIGS = []
for model in HF_MODELS:
     if model.strip():
         CONFIGS.append({
             "backend": "huggingface",
             "model": model.strip(),
             "api_key": os.getenv("HF_API_TOKEN")
       })
for model in OLLAMA_MODELS:
    if model.strip():
        CONFIGS.append({
            "backend": "ollama",
            "model": model.strip(),
            "api_key": "ollama",
            "host": OLLAMA_HOST
        })


def load_tests():
    with open(QUESTIONS_FILE, "r") as f:
        data = yaml.safe_load(f)
    return data["tests"], data.get("synonyms", {})


def score_query(sql: str, expected_keywords: list, synonyms: dict) -> float:
    """Keyword + pattern-based scoring for more semantic accuracy."""
    if not sql:
        return 0.0

    sql_norm = sql.lower()
    matches = 0
    total = len(expected_keywords)

    for kw in expected_keywords:
        kw_norm = kw.lower().rstrip("s")
        group = [kw_norm]

        # Add synonyms if available
        if kw in synonyms:
            group.extend([s.lower().rstrip("s") for s in synonyms[kw]])

        # Pattern-based equivalences
        if kw_norm in ["max", "highest"]:
            if re.search(r"order by .*desc.*limit 1", sql_norm):
                matches += 1
                continue
        if kw_norm in ["min", "lowest"]:
            if re.search(r"order by .*asc.*limit 1", sql_norm):
                matches += 1
                continue
        if kw_norm in ["top", "limit"]:
            if "limit" in sql_norm:
                matches += 1
                continue
        if kw_norm in ["count", "number", "how many"]:
            if "count(" in sql_norm:
                matches += 1
                continue
        if kw_norm in ["sum", "total", "revenue"]:
            if "sum(" in sql_norm:
                matches += 1
                continue
        if kw_norm in ["avg", "average", "mean"]:
            if "avg(" in sql_norm:
                matches += 1
                continue

        # Fallback: substring match
        if any(g in sql_norm for g in group):
            matches += 1

    return matches / total if total > 0 else 0.0


def evaluate():
    schema = load_schema()
    tests, synonyms = load_tests()
    all_results = []

    for cfg in CONFIGS:
        print(f"\nEvaluating {cfg['backend']} model: {cfg['model']}")
        runner = LLMRunner(
            use_cache=False,
            backend=cfg["backend"],
            model_id=cfg["model"],
            api_key=cfg["api_key"],
        )

        for test in tests:
            q = test["question"]
            keywords = test.get("keywords", [])

            start = time.time()
            try:
                sql = runner.generate_sql(schema, q)
                valid, _ = validate_sql(sql)
                latency = (time.time() - start) * 1000

                score = score_query(sql, keywords, synonyms) if valid else 0.0

                all_results.append({
                    "backend": cfg["backend"],
                    "model": cfg["model"],
                    "question": q,
                    "sql": sql,
                    "status": "answered" if valid else "invalid_sql",
                    "latency_ms": round(latency, 2),
                    "soft_score": score,
                })
            except Exception as e:
                all_results.append({
                    "backend": cfg["backend"],
                    "model": cfg["model"],
                    "question": q,
                    "sql": None,
                    "status": f"error: {e}",
                    "latency_ms": round((time.time() - start) * 1000, 2),
                    "soft_score": 0.0,
                })

    df = pd.DataFrame(all_results)

    # Summarize results
    summary = df.groupby(["backend", "model"]).agg(
        correct_count=("soft_score", "sum"),
        total=("soft_score", "count"),
        avg_latency_ms=("latency_ms", "mean"),
    ).reset_index()
    summary["soft_accuracy_%"] = (summary["correct_count"] / summary["total"]) * 100
    summary = summary.round(2)

    print("\n=== Comparison Summary ===")
    print(summary)

    # Save results
    os.makedirs("results", exist_ok=True)
    summary.to_csv("results/summary_results.csv", index=False)
    df.to_csv("results/detailed_results.csv", index=False)

    return df, summary


if __name__ == "__main__":
    evaluate()
