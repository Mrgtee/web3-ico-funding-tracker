# 1. Use the official LangGraph API image
FROM langchain/langgraph-api:3.11

ADD . /deps

RUN pip install --no-cache-dir -r /deps/requirements.txt