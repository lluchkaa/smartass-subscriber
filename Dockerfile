ARG PYTHON_VERSION=3.13

FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app/ app/
RUN uv sync --frozen --no-dev


FROM python:${PYTHON_VERSION}-slim-bookworm

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "app.worker"]
