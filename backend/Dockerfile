# ---- Stage 1: Build dependencies ----
FROM python:3.11-slim AS builder

WORKDIR /app

# System dependencies needed to build some Python packages (e.g. psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Stage 2: Runtime image ----
FROM python:3.11-slim

WORKDIR /app

# Runtime-only system dependency (psycopg2 needs libpq at runtime too,
# but NOT the full -dev/gcc toolchain that was only needed to BUILD it)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy only the installed Python packages from the builder stage -
# none of the build tools (gcc, libpq-dev) make it into this final image
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

# Offline mode for HuggingFace models (Step 14's fix) - baked into the
# image build so it applies from container start, not just app runtime
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

EXPOSE 8000

# Production ASGI server config - NOT --reload (that's dev-only, Step 1).
# Multiple workers for real concurrent request handling.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]