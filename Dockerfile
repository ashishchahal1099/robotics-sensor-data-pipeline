# Small, fast base image
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (so Docker caches this layer separately from code changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

EXPOSE 5000

# On container start: run the ingestion pipeline once (populates telemetry.db),
# then start the Flask API to serve that data.
CMD ["sh", "-c", "python3 pipeline.py && python3 api.py"]
