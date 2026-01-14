FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir langgraph langgraph-api

# LangGraph runtime mode (Railway will also set this as an env var; this is a safe default)
ENV LANGGRAPH_RUNTIME_EDITION=inmem

CMD ["sh", "-c", "python -m langgraph_api.server --host 0.0.0.0 --port ${PORT}"]
