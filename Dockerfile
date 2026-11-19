FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY Backend/requirements.txt ./Backend/requirements.txt
RUN pip install --no-cache-dir -r ./Backend/requirements.txt

COPY Backend ./Backend
COPY ML ./ML

ENV PYTHONPATH="/app:/app/Backend:/app/ML"
ENV PORT=8000

WORKDIR /app/Backend

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
