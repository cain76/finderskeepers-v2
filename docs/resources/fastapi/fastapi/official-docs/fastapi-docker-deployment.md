# FastAPI Docker Deployment Documentation

This document contains official FastAPI documentation for Docker deployment, sourced from the FastAPI GitHub repository.

## Docker Deployment Overview

FastAPI provides excellent support for Docker deployment with multiple approaches and configurations.

## Basic Dockerfile Examples

### Standard Dockerfile for FastAPI
```dockerfile
FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]

# If running behind a proxy like Nginx or Traefik add --proxy-headers
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]
```

### Using Official FastAPI Image
```dockerfile
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app /app
```

### Single-File FastAPI Application
```dockerfile
FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./main.py /code/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
```

## Docker Build and Run Commands

### Building the Image
```bash
docker build -t myimage .
```

### Running the Container
```bash
docker run -d --name mycontainer -p 80:80 myimage
```

## Advanced Docker Configurations

### Multi-Stage Build with Poetry
```dockerfile
FROM python:3.9 as requirements-stage

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.9

WORKDIR /code

COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
```

### FastAPI with Multiple Workers
```dockerfile
FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["fastapi", "run", "app/main.py", "--port", "80", "--workers", "4"]
```

## Proxy Configuration

### Behind TLS Termination Proxy
When running behind a proxy like Nginx or Traefik, use the `--proxy-headers` flag:

```dockerfile
CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
```

### FastAPI with Proxy Headers
```dockerfile
CMD ["fastapi", "run", "app/main.py", "--proxy-headers", "--port", "80"]
```

## Project Structure

### Recommended Directory Structure
```
.
├── app
│   ├── __init__.py
│   └── main.py
├── Dockerfile
└── requirements.txt
```

## Requirements File Examples

### Basic requirements.txt
```
fastapi[standard]>=0.113.0,<0.114.0
pydantic>=2.7.0,<3.0.0
```

### Extended requirements.txt
```
fastapi>=0.68.0,<0.69.0
pydantic>=1.8.0,<2.0.0
uvicorn>=0.15.0,<0.16.0
```

## Sample FastAPI Application

### Basic FastAPI App (main.py)
```python
from typing import Union

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
```

## Docker Cache Optimization

### Leveraging Build Cache
The Dockerfile structure is optimized for Docker's build cache:

1. Copy `requirements.txt` first
2. Install dependencies
3. Copy application code last

This ensures that dependency installation is cached if `requirements.txt` doesn't change, significantly speeding up rebuilds during development.

## Production Considerations

### Installing Production Dependencies
```bash
pip install "uvicorn[standard]" gunicorn
```

### Running in Production Mode
```bash
fastapi run
```

## Best Practices

1. **Use specific Python versions** for reproducible builds
2. **Leverage Docker cache** by copying requirements before application code
3. **Use multi-stage builds** for smaller production images
4. **Configure proxy headers** when running behind load balancers
5. **Set appropriate working directory** (`/code` is recommended)
6. **Use `--no-cache-dir`** to reduce image size
7. **Specify exact dependency versions** for reproducible builds

## Source
This documentation is compiled from the official FastAPI repository: https://github.com/tiangolo/fastapi