# Use an official Python 3.9 slim image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Ensure Python can find modules in the 'src' directory
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the project files into the container
COPY . .

# Expose the port the app will run on. Langgraph server often uses 8000
EXPOSE 8000

# This tells uvicorn to look inside the 'src/quick_start/agent.py' file
# and run the FastAPI object named 'app'.
CMD ["uvicorn", "src.quick_start.agent:app", "--host", "0.0.0.0", "--port", "8000"]
