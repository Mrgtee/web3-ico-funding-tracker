# 1. Use the official LangGraph API image as the base
FROM langchain/langgraph-api:3.11

# 2. Add your project files to the container
ADD . /deps

# 3. Install your specific dependencies (requirements.txt)
RUN pip install --no-cache-dir -e /deps
