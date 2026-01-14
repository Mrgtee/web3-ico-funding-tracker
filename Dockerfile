FROM langchain/langgraph-api:3.11

# Put your project in /app (clear + standard)
WORKDIR /app
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Railway provides PORT env var; default to 8080 locally
CMD ["sh", "-c", "langgraph dev --host 0.0.0.0 --port ${PORT:-8080}"]
