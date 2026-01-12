FROM python:3.11-slim

WORKDIR /app

# 1. Copy and install dependencies first (for faster builds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy the contents of your 'src' folder into the container's '/app'
COPY src/ .

# 3. Railway/Docker now finds main.py directly in /app
CMD ["python", "main.py"]