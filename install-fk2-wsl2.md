# FindersKeepers v2 - Windows 11 WSL2 Installation Guide

## Overview

This guide will help you install FindersKeepers v2 on Windows 11 using WSL2 with Ubuntu, optimized for NVIDIA RTX 2080 Ti GPU acceleration. WSL2 provides near-native Linux performance while keeping the familiarity of Windows.

## Why WSL2?

- ✅ **Near-native Linux performance** in Windows
- ✅ **Full Docker support** with GPU acceleration
- ✅ **Seamless file sharing** between Windows and Linux
- ✅ **Access services from both Windows and WSL2**
- ✅ **Visual Studio Code integration**
- ✅ **Windows Terminal with Linux shells**

## Prerequisites

### System Requirements

- **OS**: Windows 11 (version 22H2 or later)
- **GPU**: NVIDIA RTX 2080 Ti with latest drivers
- **RAM**: Minimum 16GB (32GB recommended for AI workloads)
- **Storage**: At least 100GB free space (WSL2 + Docker images + models)
- **CPU**: x64 processor with virtualization support

## Step-by-Step Installation

### 1. Enable WSL2 and Install Ubuntu

Open **PowerShell as Administrator** and run:

```powershell
# Enable WSL and Virtual Machine Platform
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart Windows
Restart-Computer
```

After restart, continue in **PowerShell as Administrator**:

```powershell
# Set WSL2 as default
wsl --set-default-version 2

# Install Ubuntu (latest LTS)
wsl --install -d Ubuntu

# Or install specific version
wsl --install -d Ubuntu-24.04
```

### 2. Configure Ubuntu in WSL2

Launch Ubuntu from Start Menu and complete initial setup:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget git build-essential
```

### 3. Install Docker Desktop for Windows

1. **Download Docker Desktop**: https://www.docker.com/products/docker-desktop/
2. **Install with WSL2 backend** (check during installation)
3. **Enable WSL2 integration**:
   - Open Docker Desktop
   - Go to Settings → Resources → WSL Integration
   - Enable integration with Ubuntu distribution
   - Click "Apply & Restart"

### 4. Configure NVIDIA GPU Support

#### Install NVIDIA Drivers on Windows

1. Download latest **NVIDIA Game Ready Drivers** (not WSL drivers!)
2. Install on Windows (this enables GPU in WSL2 automatically)

#### Verify GPU Access in WSL2

```bash
# In Ubuntu WSL2 terminal
lspci | grep -i nvidia
```

### 5. Test Docker GPU Support

```bash
# Test GPU access through Docker
docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu22.04 nvidia-smi
```

If this works, you're ready for GPU-accelerated containers!

### 6. Clone and Setup FindersKeepers v2

```bash
# Create project directory
mkdir -p ~/projects
cd ~/projects

# Clone repository (replace with your actual repo URL)
git clone https://github.com/bitcainnet/finderskeepers-v2.git
cd finderskeepers-v2

# Make WSL2 script executable
chmod +x start-fk2-wsl2.sh

# Copy and configure environment
cp .env.example .env
nano .env  # Or use code .env to edit in VS Code
```

### 7. Configure Environment Variables

Edit `.env` file with your credentials:

```bash
# Docker Hub credentials
DOCKER_USERNAME=bitcainnet
DOCKER_TOKEN=your_docker_token_here

# AI API keys (optional fallbacks)
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
ANTHROPIC_API_KEY=your_anthropic_key

# n8n authentication
N8N_BASIC_AUTH_USER=jeremy.cn.davis@gmail.com
N8N_BASIC_AUTH_PASSWORD=Toolman7424!
```

### 8. Launch FindersKeepers v2

```bash
# Run the WSL2-optimized startup script
./start-fk2-wsl2.sh
```

## Service Access Points

After successful installation, access from **both Windows and WSL2**:

| Service | URL | Credentials |
|---------|-----|-------------|
| 🎨 **Frontend UI** | http://localhost:3000 | No auth required |
| 🤖 **n8n Workflows** | http://localhost:5678 | jeremy.cn.davis@gmail.com / Toolman7424! |
| 📊 **FastAPI Docs** | http://localhost:8000/docs | No auth required |
| 🔗 **Neo4j Browser** | http://localhost:7474 | neo4j / fk2025neo4j |
| 🔍 **Qdrant Dashboard** | http://localhost:6333/dashboard | No auth required |
| 🧠 **Ollama API** | http://localhost:11434 | No auth required |

## WSL2-Specific Features

### File System Integration

```bash
# Access Windows files from WSL2
ls /mnt/c/Users/YourUsername/

# Access WSL2 files from Windows Explorer
explorer.exe .

# Open project in VS Code from WSL2
code .
```

### Performance Optimizations

The WSL2 script automatically applies:

- ✅ **Docker BuildKit** for faster builds
- ✅ **WSL2 file system** storage for better I/O
- ✅ **Memory limits** appropriate for Windows
- ✅ **Network optimization** for localhost access

### GPU-Accelerated Services

The following services will use your RTX 2080 Ti:

- 🧠 **Ollama**: Local LLM inference (llama3.2:3b, mxbai-embed-large)
- 🔍 **Qdrant**: Vector similarity search operations
- 🗄️ **PostgreSQL**: pgvector operations 
- 🔗 **Neo4j**: Graph algorithms and analytics
- ⚡ **FastAPI**: AI model inference and embeddings
- 🤖 **n8n**: AI-powered workflow automation
- 🎨 **Frontend**: WebGL-accelerated visualizations

## Troubleshooting

### Docker Desktop Not Starting

```powershell
# Restart WSL2 in PowerShell as Admin
wsl --shutdown
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data

# Restart Docker Desktop
```

### GPU Not Detected

1. **Update Windows**: Ensure Windows 11 22H2 or later
2. **Update NVIDIA Drivers**: Latest Game Ready drivers
3. **Restart Docker Desktop**: After driver updates
4. **Test GPU**: `docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu22.04 nvidia-smi`

### Services Not Accessible from Windows

```bash
# Check WSL2 IP
hostname -I

# Verify Docker networks
docker network ls
```

### Out of Disk Space

```bash
# Check WSL2 disk usage
df -h

# Compact WSL2 VHDX (in PowerShell as Admin)
wsl --shutdown
Optimize-VHD -Path $env:LOCALAPPDATA\Docker\wsl\data\ext4.vhdx -Mode Full
```

### Memory Issues

Create `.wslconfig` in Windows user directory:

```ini
# %USERPROFILE%\.wslconfig
[wsl2]
memory=24GB
processors=8
swap=8GB
```

## Development Workflow

### Recommended Setup

1. **Windows Terminal** with Ubuntu tab
2. **VS Code** with WSL2 extension
3. **Docker Desktop** for container management
4. **Portainer** for web-based container management

### File Editing

```bash
# Edit files in VS Code from WSL2
code ~/.bashrc
code .env
code docker-compose.yml

# Or use nano/vim in terminal
nano .env
```

### Container Management

```bash
# View all containers
docker compose ps

# View logs
docker compose logs -f fastapi
docker compose logs -f ollama

# Restart specific service
docker compose restart frontend

# Stop all services
docker compose down
```

## Advanced Configuration

### Custom Domain Names

Add to Windows `hosts` file (`C:\Windows\System32\drivers\etc\hosts`):

```
127.0.0.1 finderskeepers.local
127.0.0.1 n8n.local
127.0.0.1 api.local
```

### VS Code Integration

Install recommended extensions:
- WSL
- Docker
- Remote - Containers
- GitLens

### Windows Performance Monitoring

Monitor GPU usage from Windows:
- **Task Manager** → Performance → GPU
- **NVIDIA GeForce Experience** → Performance
- **MSI Afterburner** for detailed monitoring

## Backup and Restore

### Backup WSL2 Distribution

```powershell
# Export WSL2 distribution
wsl --export Ubuntu-24.04 C:\backup\ubuntu-backup.tar

# Import on new machine
wsl --import Ubuntu-24.04 C:\WSL2\Ubuntu-24.04 C:\backup\ubuntu-backup.tar
```

### Backup Docker Volumes

```bash
# From WSL2
cd ~/projects/finderskeepers-v2
mkdir -p ~/backups/$(date +%Y%m%d)

# Backup all Docker volumes
for volume in postgres_data neo4j_data qdrant_data n8n_data ollama_data; do
    docker run --rm -v ${volume}:/data -v ~/backups/$(date +%Y%m%d):/backup alpine tar czf /backup/${volume}.tar.gz -C /data .
done
```

## Next Steps

After installation:

1. **Configure n8n workflows** for your automation needs
2. **Import knowledge** into Neo4j and Qdrant
3. **Customize the frontend** for your use case
4. **Set up Windows shortcuts** for easy access
5. **Configure automated backups**

## Benefits of WSL2 Setup

- 🚀 **Best of both worlds**: Windows familiarity + Linux power
- 💻 **Native Windows apps**: Use your favorite Windows tools
- 🔧 **Easy maintenance**: Windows Update handles driver updates
- 🎯 **Optimal performance**: Near-native Linux performance
- 🔄 **Easy switching**: Can dual-boot or use native Linux anytime

**Happy knowledge hunting on Windows! 🚀**
