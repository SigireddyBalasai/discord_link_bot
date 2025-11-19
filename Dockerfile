ARG BUILDER_BASE=ghcr.io/astral-sh/uv:python3.13-alpine
ARG RUNTIME_BASE=python:3.13-alpine
FROM ${BUILDER_BASE} AS builder
WORKDIR /app
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_CACHE_DIR=/root/.cache/uv/python
ENV UV_COMPILE_BYTECODE=1
COPY pyproject.toml requirements.txt uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
	--mount=type=cache,target=/root/.cache/uv/python \
	--mount=type=bind,source=uv.lock,target=uv.lock \
	--mount=type=bind,source=pyproject.toml,target=pyproject.toml \
	uv sync --locked --no-install-project --no-editable --compile-bytecode
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
	--mount=type=bind,source=pyproject.toml,target=pyproject.toml \
	uv sync --locked --no-editable --compile-bytecode

FROM ${RUNTIME_BASE} AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "main.py"]