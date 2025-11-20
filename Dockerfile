ARG BUILDER_BASE=public.ecr.aws/docker/library/python:3.13-slim
ARG RUNTIME_BASE=public.ecr.aws/docker/library/python:3.13-slim
FROM ${BUILDER_BASE} AS builder
# Install UV in the builder stage
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"
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
COPY --from=builder /app/main.py /app/main.py
COPY --from=builder /app/cogs /app/cogs
COPY --from=builder /app/core /app/core
COPY --from=builder /app/link_utils /app/link_utils
COPY --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --from=builder /app/uv.lock /app/uv.lock
RUN pip install uv
RUN uv sync --no-editable --compile-bytecode
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "main.py"]