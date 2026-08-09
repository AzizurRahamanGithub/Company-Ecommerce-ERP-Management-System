#############################
# STAGE 1: Install Deps     #
#############################
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Preinstall build tools + Cairo dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

#####################################
# STAGE 2: Production Runtime Only  #
#####################################
FROM python:3.11-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies (including Cairo runtime library)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY --from=builder /install /usr/local

# Copy project files
COPY manage.py ./
COPY config/ ./config/
COPY apps/ ./apps/

# Optional: expose both ports
EXPOSE 8001
EXPOSE 8002