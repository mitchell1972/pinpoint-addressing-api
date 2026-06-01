# Pinpoint API image.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PINPOINT_DATABASE_URL=postgresql://pinpoint:pinpoint@db:5432/pinpoint

WORKDIR /app

# Install runtime deps (from pyproject [project.dependencies]) + the app itself.
# Editable so the bundled static files under src/app/web are served from disk.
COPY pyproject.toml ./
COPY src ./src
COPY db ./db
COPY scripts ./scripts
RUN pip install --no-cache-dir -e .

EXPOSE 8000

# Liveness probe hits /health; orchestrators can use /ready for readiness.
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=10 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
