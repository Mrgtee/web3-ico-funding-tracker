FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir langgraph-api uvicorn

ENV LANGGRAPH_RUNTIME_EDITION=inmem

CMD ["sh", "-c", "echo PORT=$PORT && python - <<'PY'\nimport os\nimport uvicorn\nfrom langgraph_api.server import app\nport = int(os.environ.get('PORT', '8080'))\nuvicorn.run(app, host='0.0.0.0', port=port)\nPY"]

ENV LANGGRAPH_RUNTIME_EDITION=inmem
ENV LANGGRAPH_CONFIG=langgraph.json
