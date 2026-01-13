FROM langchain/langgraph-api:3.11
ADD . /deps
RUN pip install --no-cache-dir -r /deps/requirements.txt

# This forces the server to use local memory instead of a database
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8080"]