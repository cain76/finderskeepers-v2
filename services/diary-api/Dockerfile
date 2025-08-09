# Use Python 3.12 official image
FROM python:3.12-slim

# Install system dependencies including OpenGL for EasyOCR and PostgreSQL client
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libmagic1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file first
COPY requirements.txt /app/

# Install PyTorch with CUDA support for GPU acceleration
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install dependencies using requirements file
RUN pip install -r /app/requirements.txt

# Install additional dependencies not in requirements
RUN pip install \
    python-magic \
    websockets

# Copy application code
COPY . /app

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Set environment variables for GPU access
ENV CUDA_VISIBLE_DEVICES=0
ENV NVIDIA_VISIBLE_DEVICES=0

# Expose port
EXPOSE 80

# Use entrypoint script for initialization
ENTRYPOINT ["/app/docker-entrypoint.sh"]