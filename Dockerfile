FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Expose the port Railway uses
EXPOSE 8080
CMD ["python", "src/quick_start/main.py"]