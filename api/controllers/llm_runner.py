import os
import re
from typing import Dict, Optional
from openai import OpenAI
from api.controllers.prompt_builder import build_prompt_with_question
from api.models.artifact_store import find_cached_sql
from dotenv import load_dotenv

load_dotenv()

# Defaults for production Ollama runner
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://model-runner:11434")
DEFAULT_MODEL = os.getenv("HF_MODEL", "mistral:latest")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")



def clean_sql_output(raw: str) -> str:
    """
    Clean raw model output:
    - Extract the first SELECT statement
    - Remove markdown/code fences and comments
    - Return SQL in single line (strip newlines and extra spaces)
    """
    if not raw:
        return ""

    # Remove ```sql and ``` fences
    raw = re.sub(r"```sql|```", "", raw, flags=re.I)

    # Collapse all newlines and tabs into spaces
    raw = re.sub(r"[\n\r\t]+", " ", raw)

    # Remove extra spaces
    raw = re.sub(r"\s{2,}", " ", raw).strip()

    # Extract first SELECT... until semicolon or end
    match = re.search(r"(select[\s\S]*?)(;|$)", raw, re.IGNORECASE)
    return match.group(1).strip() if match else raw.strip()



class LLMRunner:
    """
    Unified LLM Runner:
    - Default: Ollama (for main pipeline)
    - Optional: Hugging Face (for evaluation)
    """

    def __init__(
        self,
        use_cache: bool = True,
        backend: str = "ollama",
        model_id: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.use_cache = use_cache
        self.backend = backend.lower()

        # Default model if not provided
        if not model_id:
            model_id = DEFAULT_MODEL
        self.model = model_id
        # Configure backend
        if self.backend == "huggingface":
            if not api_key:
                api_key = os.getenv("HF_API_TOKEN")
            if not api_key:
                raise RuntimeError("HF_API_TOKEN must be set for Hugging Face backend")

            self.client = OpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=api_key,
            )
           # print(f" Using Hugging Face API model={self.model}")

        elif self.backend == "ollama":
            ollama_host = os.getenv("OLLAMA_HOST", OLLAMA_HOST)
            self.client = OpenAI(
                base_url=f"{ollama_host}/v1",
                api_key="ollama",  # Ollama ignores auth
            )
            #print(f" Using Ollama runner at {ollama_host}, model={self.model}")

        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def generate_sql(self, schema: Dict, question: str) -> str:
        """Generate SQL from question + schema context."""
        if self.use_cache:
            cached = find_cached_sql(question)
            if cached:
               # print(" Using cached SQL from artifact store")
                return cached

        prompt = build_prompt_with_question(schema, question)

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.0,
            )
            raw_output = completion.choices[0].message.content
            return clean_sql_output(raw_output)
        except Exception as e:
            raise RuntimeError(f"{self.backend.capitalize()} API error: {e}")
