FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything
COPY . .

# Environment
ENV PYTHONUNBUFFERED=1
ENV HF_API_TOKEN=""
ENV OLLAMA_HOST="http://model-runner:11434"

# Expose API port
EXPOSE 8000

# Default entrypoint — overridable in docker-compose.yml
CMD ["uvicorn", "api.views.service:app", "--host", "0.0.0.0", "--port", "8000"]
