# EasyOCR Docker Setup Guide

**Date Created:** July 7, 2025  
**Source:** Research from EasyOCR GitHub and official documentation  

## Summary

EasyOCR is an OCR library that depends on `opencv-python-headless` for image processing. Since August 2021 (Issue #485), EasyOCR officially uses `opencv-python-headless` as its dependency, making it Docker-friendly.

## Key Points

### Dependencies
- **Primary:** `opencv-python-headless` (not `opencv-python`)
- **ML Libraries:** PyTorch, Torchvision
- **Image Processing:** Pillow, numpy
- **System Libraries:** Same as opencv-python-headless requirements

### Installation Methods

#### Method 1: Pip Install
```bash
pip install easyocr
```

#### Method 2: From Source
```bash
pip install git+git://github.com/jaidedai/easyocr.git
```

#### Method 3: Docker (coming soon per docs)

## Docker Configuration

### Complete Dockerfile Example

```dockerfile
FROM python:3.11-slim

# Install system dependencies for EasyOCR/OpenCV
RUN apt-get update && apt-get install -y \
    # OpenCV system dependencies
    libglib2.0-0 \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Additional for EasyOCR
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install easyocr

# Verify installation
RUN python -c "import easyocr; print('EasyOCR installed successfully')"
```

### UV-based Installation (for FindersKeepers v2)

```dockerfile
FROM python:3.11-slim AS builder

# Install system dependencies for build
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libmagic-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.7.15 /uv /uvx /bin/

# Set UV environment
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_INSTALLER_METADATA=1

WORKDIR /app

# Copy and install dependencies
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-editable && \
    # Remove conflicts
    uv pip uninstall opencv-python || true

# Production stage
FROM python:3.11-slim

# Install runtime dependencies (complete list for EasyOCR)
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment
COPY --from=builder /app/.venv /app/.venv

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# Copy application
COPY . .
```

## Common Issues and Solutions

### Issue 1: ImportError: No module named 'cv2'
**Cause:** Missing opencv-python-headless or system dependencies  
**Solution:** Install complete system dependency list

### Issue 2: libGL.so.1 Error
**Cause:** Missing OpenGL libraries  
**Solution:** Install `libgl1-mesa-glx`

### Issue 3: Package Conflicts
**Cause:** Both opencv-python and opencv-python-headless installed  
**Solution:** Uninstall opencv-python, keep only headless version

### Issue 4: EasyOCR Model Download Issues
**Cause:** Network restrictions in container  
**Solution:** Pre-download models or configure proxy

## pyproject.toml Configuration

```toml
[project]
dependencies = [
    "easyocr>=1.7.0",  # Includes opencv-python-headless
    # Don't explicitly add opencv-python-headless - let EasyOCR manage it
]
```

## Testing EasyOCR Installation

```python
# Complete test script
import easyocr
import cv2
import numpy as np

# Test OpenCV
print(f"OpenCV version: {cv2.__version__}")

# Test EasyOCR
try:
    reader = easyocr.Reader(['en'])
    print("EasyOCR Reader initialized successfully")
    
    # Test with simple image
    test_image = np.ones((100, 300, 3), dtype=np.uint8) * 255
    cv2.putText(test_image, 'TEST', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    results = reader.readtext(test_image)
    print(f"OCR Results: {results}")
    print("EasyOCR test completed successfully")
    
except Exception as e:
    print(f"EasyOCR test failed: {e}")
```

## Model Management

EasyOCR downloads models on first use:
- Default location: `~/.EasyOCR/`
- Models are cached automatically
- For Docker: consider mounting volume for model cache

```dockerfile
# Example with model cache volume
VOLUME ["/root/.EasyOCR"]
```

## Performance Considerations

### CPU vs GPU
- CPU mode: Default, works in all containers
- GPU mode: Requires CUDA-enabled base image

### Memory Requirements
- Minimum: 1GB RAM
- Recommended: 2GB+ RAM for multiple languages

## References

- [EasyOCR GitHub Issue #485](https://github.com/JaidedAI/EasyOCR/issues/485) - opencv-python-headless adoption
- [EasyOCR Official Installation](https://www.jaided.ai/easyocr/install/)
- [EasyOCR GitHub Repository](https://github.com/JaidedAI/EasyOCR)
- [OpenCV Python Headless Documentation](../opencv-python-headless-docker-requirements.md)