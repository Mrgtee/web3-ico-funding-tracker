FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir langgraph langgraph-api

CMD ["sh", "-c", "LANGGRAPH_RUNTIME_EDITION=${LANGGRAPH_RUNTIME_EDITION:-inmem} python -m langgraph_api.server --host 0.0.0.0 --port ${PORT:-8080}"]
