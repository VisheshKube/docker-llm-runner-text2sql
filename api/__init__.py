"""
AI-SQL Pipeline Package

This package contains all modules needed to run the private AI-SQL pipeline:
- prompt_builder: builds system + user prompts from schema
- llm_runner: runs SQLCoder model to generate SQL
- sql_firewall: validates and blocks unsafe SQL
- db_executor: executes queries in read-only mode
- artifact_store: logs all interactions (prompts, SQL, results)
"""
