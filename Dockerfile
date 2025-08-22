FROM python:3.13-slim AS builder
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    uv venv /venv
ENV PATH="/venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml .
RUN uv pip install --no-cache-dir .

FROM python:3.13-slim
RUN useradd -m appuser

WORKDIR /app
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"
COPY . .
RUN chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
