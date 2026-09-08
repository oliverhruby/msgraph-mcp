FROM python:3.12-slim AS base

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir . 2>/dev/null || true
COPY src/ src/
RUN pip install --no-cache-dir .

USER app

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r=httpx.get('http://127.0.0.1:3000/sse' if False else 'http://127.0.0.1:3000/mcp'); exit(0 if r.status_code in (200,405) else 1)" 2>/dev/null || exit 0

ENTRYPOINT ["python", "-m", "msgraph_mcp"]
