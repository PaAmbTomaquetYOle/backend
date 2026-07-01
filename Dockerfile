# ── Stage 1: builder ────────────────────────────────────────────────────────
# Install production dependencies into an isolated virtualenv using uv.
FROM python:3.14-slim AS builder

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests first to leverage Docker layer caching.
# The virtualenv is only rebuilt when pyproject.toml or uv.lock change.
COPY pyproject.toml uv.lock ./

# Sync production dependencies into /app/.venv
# --frozen:   respect uv.lock exactly (no resolution)
# --no-dev:   skip development dependencies
# --no-cache: keep the image lean
RUN uv sync --frozen --no-dev --no-cache --no-install-project

# ── Stage 2: runtime ────────────────────────────────────────────────────────
# Clean image with only the virtualenv and application source code.
FROM python:3.14-slim AS runtime

WORKDIR /app

# Copy the pre-built virtualenv from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application source code
COPY src/ ./src/

# Add the virtualenv binaries to PATH so uvicorn is found directly
ENV PATH="/app/.venv/bin:$PATH" \
    # Prevent Python from writing .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    # Disable output buffering for real-time Docker logs
    PYTHONUNBUFFERED=1 \
    # Set the Python module search path to the src directory
    PYTHONPATH="/app/src"

EXPOSE 8888

# Use exec form (array) so Docker sends SIGTERM directly to uvicorn,
# enabling graceful shutdown without an intermediate shell process.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]
