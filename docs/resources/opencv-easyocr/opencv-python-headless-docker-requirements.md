# OpenCV-Python-Headless Docker Requirements

**Date Created:** July 7, 2025  
**Source:** Research from GitHub issues and documentation  

## Summary

`opencv-python-headless` is designed for server/headless environments (like Docker) but still requires specific system dependencies to function properly. This document outlines the complete requirements for successful installation.

## Key Dependencies

### Required System Packages for Debian/Ubuntu

Based on PEP 513 manylinux policy and GitHub issues #203 and #208, these packages are required:

```bash
# Essential runtime dependencies
libglib2.0-0        # Core system library (always required)
libgl1-mesa-glx     # OpenGL library
libglib2.0-dev      # Development headers (sometimes needed)

# Additional X11 libraries (even for headless)
libsm6              # Session management library
libxext6            # X11 extensions
libxrender-dev      # X11 render extension
libgomp1            # OpenMP runtime library
```

### Python Requirements

- Python 3.7+ (tested versions)
- No conflicting opencv packages

## Version History

- **4.0.0.21 - 4.3.0.38**: Required `libglib2.0-0`
- **4.3.0.38+**: Additional X11 dependencies required
- **Latest (4.11.0.86)**: Full dependency list needed

## Common Issues

### 1. Missing cv2 Module
**Error:** `ModuleNotFoundError: No module named 'cv2'`  
**Cause:** Missing system dependencies  
**Solution:** Install required system packages

### 2. libGL.so.1 Error
**Error:** `libGL.so.1: cannot open shared object file`  
**Cause:** Missing OpenGL libraries  
**Solution:** Install `libgl1-mesa-glx`

### 3. libgthread-2.0.so.0 Error
**Error:** `libgthread-2.0.so.0: cannot open shared object file`  
**Cause:** Missing GLib threading library  
**Solution:** Install `libglib2.0-0`

## Docker Best Practices

### Dockerfile Example (Python 3.11 Slim)

```dockerfile
FROM python:3.11-slim

# Install system dependencies for opencv-python-headless
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install opencv-python-headless
```

### Multi-stage Build Example

```dockerfile
# Builder stage
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install packages
RUN pip install opencv-python-headless

# Production stage
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
```

## Package Conflicts

### opencv-python vs opencv-python-headless

**NEVER install both packages together:**
- `opencv-python` - Includes GUI dependencies
- `opencv-python-headless` - Server/Docker optimized

**Resolution:**
```bash
pip uninstall opencv-python
pip install opencv-python-headless
```

## Testing Installation

```python
# Test script to verify installation
import cv2
print(f"OpenCV version: {cv2.__version__}")
print("OpenCV installed successfully!")
```

## References

- [GitHub Issue #203](https://github.com/opencv/opencv-python/issues/203) - libglib2.0-0 requirement
- [GitHub Issue #208](https://github.com/opencv/opencv-python/issues/208) - X11 dependencies
- [PEP 513 manylinux policy](https://www.python.org/dev/peps/pep-0513/)
- [OpenCV Python Packages Documentation](https://pypi.org/project/opencv-python-headless/)