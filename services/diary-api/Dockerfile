# FindersKeepers v2 FastAPI Backend - Production UV Build
# Multi-stage build for optimized production image

FROM python:3.11-slim AS builder

# Install uv - pinned version for reproducibility
COPY --from=ghcr.io/astral-sh/uv:0.7.15 /uv /uvx /bin/

# Set environment variables for UV optimization
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_INSTALLER_METADATA=1

# Set work directory
WORKDIR /app

# Copy UV project files first (for Docker layer caching)
COPY pyproject.toml uv.lock* ./

# Install dependencies with cache optimization
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then \
        uv sync --locked --no-install-project --no-editable; \
    else \
        uv sync --no-install-project --no-editable; \
    fi

# Copy application code
COPY . .

# Install the project itself (skip for FastAPI apps that don't need packaging)
# RUN --mount=type=cache,target=/root/.cache/uv \
#     if [ -f uv.lock ]; then \
#         uv sync --locked --no-editable; \
#     else \
#         uv sync --no-editable; \
#     fi

# Production stage - smaller final image
FROM python:3.11-slim

# Set production environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"

# Set work directory
WORKDIR /app

# Copy the virtual environment from builder stage (no source code needed)
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Expose port
EXPOSE 80

# Start command using uvicorn (reliable approach)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]