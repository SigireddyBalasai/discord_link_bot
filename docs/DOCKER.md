# Docker build guide for discord-link-bot

This document covers best-practice Docker builds for this project using `uv` to manage Python dependencies.

Highlights
- Use `uv sync` during build time so no packages are installed at runtime.
- Create `uv.lock` via `uv lock` for reproducible builds and use `--locked` in Dockerfile
- Use multi-stage builds to keep `uv` out of final runtime images
- Use BuildKit cache mounts and `UV_COMPILE_BYTECODE` for faster builds and smaller runtime images.

Available Docker builds in this repo
- `Dockerfile` — Alpine-based builder and runtime by default; uses `ghcr.io/astral-sh/uv:python3.13-alpine` for the builder and `python:3.13-alpine` for the runtime. This produces a small runtime image while keeping uv in the builder stage.

How to build

Default (Alpine-based):
```bash
DOCKER_BUILDKIT=1 docker build -t discord-link-bot:local .
```

If you prefer a Debian-based image instead, update the `Dockerfile` to use the Debian builder and runtime (or add a separate `Dockerfile.debian` stage) and then build with:
```bash
DOCKER_BUILDKIT=1 docker build -t discord-link-bot:debian .
```

How it works (summary)
- `pyproject.toml` and `uv.lock` are copied and run through `uv sync --locked` to install runtime dependencies into `.venv` during build.
- The repo is then copied and the project is installed using `uv sync` again (to include local project packages); `.venv` is then copied into the final runtime stage.
- The final stage sets `PATH` to the `.venv/bin` so `python` resolves to the environment created during build time.

Best practices & notes
- Do not put secrets (e.g., `DISCORD_TOKEN`) in the Dockerfile; pass them at runtime. For example:
  - `docker run -e DISCORD_TOKEN=$(cat .env | grep DISCORD_TOKEN) discord-link-bot:local`
  - Consider Docker secrets for production deploys.
- Use BuildKit (DOCKER_BUILDKIT=1) for cache mounts; faster incremental builds.

Docker Hub pulls in CI
 If your Dockerfile uses base images hosted on Docker Hub (or other rate-limited registries) and you hit rate limits in AWS CodeBuild, we recommend providing DockerHub credentials to CodeBuild via AWS Secrets Manager.

  Steps:
  1. Terraform creates a placeholder Secrets Manager secret named `discord/dockerhub` when you run `terraform apply` under `infra/` — it contains `username` and `password` fields you must replace with your Docker Hub credentials (see one-line CLI below).
  2. No Terraform variables are required. Once the secret contains your real Docker Hub credentials, CodeBuild will automatically inject `DOCKERHUB_USERNAME` and `DOCKERHUB_PASSWORD` into the build environment and `buildspec.yml` logs into Docker Hub before pulls.
  3. Update the secret value (JSON) that Terraform created in `discord/dockerhub` with both `username` and `password` keys; for example:
     ```bash
     aws secretsmanager put-secret-value \
       --secret-id arn:aws:secretsmanager:us-east-1:123456789012:secret:discord/dockerhub \
       --secret-string '{"username":"your_dockerhub_user","password":"supersecret"}' --region us-east-1
     ```
  4. Re-run the pipeline (or push a commit) so CodeBuild picks up authenticated pulls.
  2. Update `infra/terraform.tfvars` with `dockerhub_username = "<your-username>"` and `dockerhub_password_secret_arn = "arn:aws:secretsmanager:...:secret:discord/dockerhub/password-XYZ"`.
  3. Run `terraform plan` and `terraform apply` to update the `aws_codebuild_project` environment variables.
  4. The pipeline will then inject `DOCKERHUB_USERNAME` (plaintext) and `DOCKERHUB_PASSWORD` (from Secrets Manager) into the build environment; `buildspec.yml` automatically logs in before pulling images.
- If you track `uv.lock` in git, use `uv lock` to regenerate after dependency changes. `uv sync --locked` will use uv.lock.
 - If you track `uv.lock` in git, use `uv lock` to regenerate after dependency changes. `uv sync --locked` will use uv.lock.
 - Caching notes (from uv docs):
   - Use BuildKit cache mounts to speed up dependency resolution and re-use cached artifacts across builds: `--mount=type=cache,target=/root/.cache/uv` and `--mount=type=cache,target=/root/.cache/uv/python`.
   - For reproducible builds pin `uv` and use a lockfile — `uv.lock` generated with `uv lock` can be mounted into the build: for example `--mount=type=bind,source=uv.lock,target=uv.lock` so the `uv sync --locked` step reads the lock file from your host context.
   - Mount `pyproject.toml` at build time too with `--mount=type=bind` to make a stable layer for dependency resolution while keeping build cache behaviour.
   - Use `--no-install-project` for the first sync to only install transitive dependencies in a cacheable layer, then copy the source and re-run `uv sync --locked --no-editable` to install the project itself into `.venv`.
   - Use `UV_LINK_MODE=copy` to avoid hardlinking warnings when the cache is on a different filesystem.
   - Pin `uv` binaries: copy from a specific tag or digest to ensure builds are reproducible and verify provenance. Example in `Dockerfile`: `COPY --from=ghcr.io/astral-sh/uv:0.9.10 /uv /uvx /bin/`.
   - You can call `uv cache dir` to discover UV cache directory locations inside the image; then set `UV_CACHE_DIR` or `UV_PYTHON_CACHE_DIR` to a constant location and bind it to a BuildKit cache mount to reuse cached downloaded/python artifacts between builds.
   - To reduce image size when you don't want uv in runtime, you can copy only the installed `.venv` into the final image and omit the `COPY --from=ghcr.io/astral-sh/uv...` step; but keeping `uv` in runtime lets you use `uv run` and `uv tool` in the container if desired.
   - Use `UV_NO_CACHE=1` when you want to force a cache-free installation (useful for CI reproducibility), and `uv sync --no-cache` if you want to skip the uv cache.
   - Use `uv sync --no-install-workspace` for workspaces and `--no-install-package <name>` to exclude packages from sync when needed.
   - Use `UV_SYSTEM_PYTHON=1` if you prefer to install packages into the system Python environment instead of creating a venv; this is helpful if you want `python` and the environment to be shared globally in the image.
If a package fails to build on Alpine, add system build dependencies to the builder stage (e.g., `libffi`, `openssl`, `build-base`, or `cargo`) — this is a local addition to the `Dockerfile` when needed.
- If you want even smaller images you can use `python:slim` or distroless images and copy only the installed `.venv` while keeping system dependencies minimal.

Troubleshooting
- If `uv sync --locked` fails complaining about missing `uv.lock`, run:
  ```bash
  uv lock
  ```
- If a package fails to build on Alpine, ensure required dev packages are included (e.g., `rust` for cryptography + `build-base` for wheels).

Rebuild and test
- Build image
  ```bash
  DOCKER_BUILDKIT=1 docker build -t discord-link-bot:local .
  ```
- Run a short command to verify installed packages
  ```bash
  docker run --rm discord-link-bot:local /bin/sh -c "ls -la /app/.venv/lib/python3.13/site-packages | head -n 30"
  ```

If you want me to add more details or a `docker-compose.yml` example, say the word and I will add it.
