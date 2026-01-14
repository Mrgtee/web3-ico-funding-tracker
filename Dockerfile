FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir langgraph langgraph-api langchain

EXPOSE 8080

CMD ["python", "-m", "langgraph_api.server"]
