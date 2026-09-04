FROM python:3.11.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements-api.lock pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -r requirements-api.lock \
    && pip install --no-cache-dir --no-deps . \
    && useradd --create-home --uid 10001 behaviortune

USER behaviortune
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"]
CMD ["uvicorn", "behaviortune.api:app", "--host", "0.0.0.0", "--port", "8000"]
