# Use FastAPI official image that includes uvicorn
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

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

# Set environment variables for GPU access
ENV CUDA_VISIBLE_DEVICES=0
ENV NVIDIA_VISIBLE_DEVICES=0