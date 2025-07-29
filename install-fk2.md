# FindersKeepers v2 Installation Guide

## Overview

FindersKeepers v2 is a personal AI agent knowledge hub designed for advanced knowledge management, workflow automation, and AI-powered data processing. This installation guide will help you set up the entire system on a new machine with GPU acceleration support.

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04/22.04 or similar Linux distribution
- **GPU**: NVIDIA GPU with CUDA support (tested with RTX 2080 Ti)
- **RAM**: Minimum 16GB (32GB recommended)
- **Storage**: At least 50GB free space for Docker images and data
- **Network**: Stable internet connection for pulling Docker images and AI models

### Software Requirements

1. **Docker Engine** (v24.0+)
2. **Docker Compose** (v2.20+)
3. **NVIDIA Container Toolkit** (for GPU support)
4. **Git** (for cloning repositories)

## Quick Start

If you already have all prerequisites installed, simply run:

```bash
cd /media/cain/linux_storage/projects/finderskeepers-v2
./start-fk2.sh
```

## Detailed Installation Steps

### 1. Install Docker

```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the stable repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to the docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Install NVIDIA Container Toolkit

```bash
# Add NVIDIA package repositories
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Update package list
sudo apt-get update

# Install nvidia-docker2
sudo apt-get install -y nvidia-docker2

# Restart Docker
sudo systemctl restart docker

# Test GPU support
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 3. Clone the Repository

```bash
# Create project directory if it doesn't exist
sudo mkdir -p /media/cain/linux_storage/projects
sudo chown $USER:$USER /media/cain/linux_storage/projects

# Clone the repository (replace with your actual repository URL)
cd /media/cain/linux_storage/projects
git clone https://github.com/bitcainnet/finderskeepers-v2.git
cd finderskeepers-v2
```

### 4. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your credentials
nano .env
```

**Required environment variables:**
- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_TOKEN`: Your Docker Hub access token
- `OPENAI_API_KEY`: OpenAI API key (optional, for fallback)
- `GOOGLE_API_KEY`: Google API key (optional)
- `ANTHROPIC_API_KEY`: Anthropic API key (optional)

### 5. Run the Startup Script

```bash
# Make the script executable (if not already)
chmod +x start-fk2.sh

# Run the startup script
./start-fk2.sh
```

The script will:
1. ✅ Load environment variables from `.env`
2. ✅ Log into Docker Hub using your credentials
3. ✅ Check for GPU support and NVIDIA Docker runtime
4. ✅ Create the required Docker network
5. ✅ Set up necessary directories and configurations
6. ✅ Pull the latest Docker images
7. ✅ Start all services with GPU acceleration
8. ✅ Download Ollama models for local LLM inference
9. ✅ Display access URLs and credentials

## Service Access Points

After successful installation, you can access:

| Service | URL | Credentials |
|---------|-----|-------------|
| n8n Workflows | http://localhost:5678 | Username: jeremy.cn.davis@gmail.com<br>Password: Toolman7424! |
| FastAPI Docs | http://localhost:8000/docs | No auth required |
| Frontend UI | http://localhost:3000 | No auth required |
| Neo4j Browser | http://localhost:7474 | Username: neo4j<br>Password: fk2025neo4j |
| Qdrant Dashboard | http://localhost:6333/dashboard | No auth required |
| Ollama API | http://localhost:11434 | No auth required |

## GPU-Accelerated Services

The following services benefit from GPU acceleration:
- **Ollama**: Local LLM inference (optimized for RTX 2080 Ti)
- **Qdrant**: Vector similarity search operations
- **PostgreSQL (pgvector)**: Vector operations and similarity search
- **Neo4j**: Graph algorithms and data science operations
- **FastAPI**: ML model inference and embeddings
- **n8n**: AI-powered workflow nodes

## Troubleshooting

### Docker Login Issues

If you encounter Docker login problems:
```bash
# Manually login
docker login -u bitcainnet
# Enter your Docker token when prompted
```

### GPU Not Detected

1. Check NVIDIA drivers:
```bash
nvidia-smi
```

2. Verify Docker GPU support:
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

3. Restart Docker daemon:
```bash
sudo systemctl restart docker
```

### Services Not Starting

1. Check Docker logs:
```bash
docker compose logs -f [service_name]
```

2. Verify network exists:
```bash
docker network ls | grep shared-network
```

3. Check disk space:
```bash
df -h
```

### Ollama Model Download Failures

If Ollama models fail to download:
```bash
# Manually pull models
docker compose exec ollama ollama pull mxbai-embed-large
docker compose exec ollama ollama pull llama3.2:3b
```

## Maintenance Commands

### View All Logs
```bash
docker compose logs -f
```

### Stop All Services
```bash
docker compose down
```

### Remove All Data (Warning: Destructive!)
```bash
docker compose down -v
```

### Update Services
```bash
docker compose pull
docker compose up -d
```

### Check GPU Usage
```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# Check container GPU usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## Data Persistence

All data is stored in Docker named volumes:
- `postgres_data`: PostgreSQL database
- `neo4j_data`: Neo4j graph database
- `qdrant_data`: Qdrant vector database
- `redis_data`: Redis cache
- `n8n_data`: n8n workflows and credentials
- `ollama_data`: Downloaded LLM models

To backup data:
```bash
# Create backup directory
mkdir -p ~/fk2-backups/$(date +%Y%m%d)

# Backup all volumes
for volume in postgres_data neo4j_data qdrant_data redis_data n8n_data ollama_data; do
    docker run --rm -v ${volume}:/data -v ~/fk2-backups/$(date +%Y%m%d):/backup alpine tar czf /backup/${volume}.tar.gz -C /data .
done
```

## Security Considerations

1. **Change default passwords** in production environments
2. **Use HTTPS** for external access (configure reverse proxy)
3. **Limit port exposure** using firewall rules
4. **Regular updates** of Docker images
5. **Monitor logs** for suspicious activity

## Support

For issues or questions:
1. Check the logs: `docker compose logs -f`
2. Verify GPU support: `nvidia-smi`
3. Review environment variables in `.env`
4. Consult service-specific documentation

## Next Steps

After installation:
1. Access n8n and import workflow templates
2. Configure AI models in FastAPI
3. Set up knowledge graph schemas in Neo4j
4. Create vector collections in Qdrant
5. Customize the frontend UI
6. Build automation workflows

Happy knowledge hunting! 🚀
