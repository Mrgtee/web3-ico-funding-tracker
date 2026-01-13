FROM langchain/langgraph-api:3.11

ADD . /deps

RUN pip install --no-cache-dir -r /deps/requirements.txt

# The --port 8080 ensures Railway can talk to it.
# The 'dev' command skips the license check.
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8080"]