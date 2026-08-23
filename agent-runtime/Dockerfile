FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS test
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock .python-version ./
COPY app app
COPY alembic alembic
COPY alembic.ini ./
COPY db db
COPY tests tests
RUN uv sync --frozen
RUN uv run pytest

FROM test
COPY docker-entrypoint.sh ./
RUN uv sync --frozen --no-dev \
    && rm -rf tests \
    && chmod +x docker-entrypoint.sh
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 3008
ENTRYPOINT ["./docker-entrypoint.sh"]
