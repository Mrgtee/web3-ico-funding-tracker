# 1. Official production image
FROM langchain/langgraph-api:3.11

# 2. Add project files
ADD . /deps

# 3. Install requirements
RUN pip install --no-cache-dir -r /deps/requirements.txt

