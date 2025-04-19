# ----------  Dockerfile -------------
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080               
CMD ["sh", "-c", "gunicorn -k gevent -b 0.0.0.0:${PORT:-8080} app:app"]

