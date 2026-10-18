
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py migrate.py ./
COPY migrations ./migrations

CMD ["sh", "-c", "python migrate.py && exec uvicorn app:app --host 0.0.0.0 --port 8000"]
