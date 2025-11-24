FROM public.ecr.aws/docker/library/python:3.13-slim as builder

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_PREFERENCE=only-system

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

RUN ls -la /app

FROM public.ecr.aws/docker/library/python:3.13-slim

COPY --from=builder /app/.venv /app/.venv

COPY . /app

# Copy VERSION file if it exists (from build), otherwise create a dev version
RUN if [ -f /app/VERSION ]; then \
        echo "Using VERSION file from build"; \
    else \
        echo "v0.1.0 (dev)" > /app/VERSION; \
    fi

RUN ls -la /app

WORKDIR /app

RUN mkdir -p /app/core/data

ENV PATH="/app/.venv/bin:$PATH"
ENV DB_PATH="/data/bot_data.db"

CMD ["/app/.venv/bin/python", "main.py"]