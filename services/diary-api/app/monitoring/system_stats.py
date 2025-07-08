"""
Real-time system monitoring for FindersKeepers v2
Provides actual Docker container stats and system metrics
"""

import asyncio
import json
import logging
import psutil
import docker
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ContainerStats:
    """Container statistics data class"""
    name: str
    status: str
    cpu_percent: float
    memory_usage_mb: float
    memory_limit_mb: float
    memory_percent: float
    network_rx_mb: float
    network_tx_mb: float
    disk_read_mb: float
    disk_write_mb: float

class SystemMonitor:
    """Real-time system monitoring for Docker containers and host metrics"""
    
    def __init__(self):
        self.docker_client = None
        self.container_prefixes = ['fk2_', 'finderskeepers']
        self._init_docker_client()
    
    def _init_docker_client(self):
        """Initialize Docker client with error handling"""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None
    
    async def get_container_stats(self) -> List[ContainerStats]:
        """Get real-time statistics for FindersKeepers containers"""
        if not self.docker_client:
            logger.warning("Docker client not available")
            return []
        
        container_stats = []
        
        try:
            # Get all containers (running and stopped)
            containers = self.docker_client.containers.list(all=True)
            fk_containers = [c for c in containers if any(prefix in c.name for prefix in self.container_prefixes)]
            
            for container in fk_containers:
                try:
                    stats = await self._get_single_container_stats(container)
                    if stats:
                        container_stats.append(stats)
                except Exception as e:
                    logger.error(f"Error getting stats for container {container.name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
        
        return container_stats
    
    async def _get_single_container_stats(self, container) -> Optional[ContainerStats]:
        """Get statistics for a single container"""
        try:
            # Get container info
            container_info = container.attrs
            name = container.name
            status = container.status
            
            # If container is not running, return basic info
            if status != 'running':
                return ContainerStats(
                    name=name,
                    status=status,
                    cpu_percent=0.0,
                    memory_usage_mb=0.0,
                    memory_limit_mb=0.0,
                    memory_percent=0.0,
                    network_rx_mb=0.0,
                    network_tx_mb=0.0,
                    disk_read_mb=0.0,
                    disk_write_mb=0.0
                )
            
            # Get real-time stats for running containers
            stats_stream = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_percent = self._calculate_cpu_percent(stats_stream)
            
            # Calculate memory usage
            memory_stats = stats_stream.get('memory_stats', {})
            memory_usage = memory_stats.get('usage', 0)
            memory_limit = memory_stats.get('limit', 0)
            memory_usage_mb = memory_usage / 1024 / 1024
            memory_limit_mb = memory_limit / 1024 / 1024
            memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0.0
            
            # Calculate network I/O
            network_stats = stats_stream.get('networks', {})
            network_rx = sum(net.get('rx_bytes', 0) for net in network_stats.values())
            network_tx = sum(net.get('tx_bytes', 0) for net in network_stats.values())
            network_rx_mb = network_rx / 1024 / 1024
            network_tx_mb = network_tx / 1024 / 1024
            
            # Calculate disk I/O
            blkio_stats = stats_stream.get('blkio_stats', {})
            disk_read = sum(entry.get('value', 0) for entry in blkio_stats.get('io_service_bytes_recursive', []) if entry.get('op') == 'read')
            disk_write = sum(entry.get('value', 0) for entry in blkio_stats.get('io_service_bytes_recursive', []) if entry.get('op') == 'write')
            disk_read_mb = disk_read / 1024 / 1024
            disk_write_mb = disk_write / 1024 / 1024
            
            return ContainerStats(
                name=name,
                status=status,
                cpu_percent=cpu_percent,
                memory_usage_mb=memory_usage_mb,
                memory_limit_mb=memory_limit_mb,
                memory_percent=memory_percent,
                network_rx_mb=network_rx_mb,
                network_tx_mb=network_tx_mb,
                disk_read_mb=disk_read_mb,
                disk_write_mb=disk_write_mb
            )
            
        except Exception as e:
            logger.error(f"Error getting stats for container {container.name}: {e}")
            return None
    
    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU percentage from Docker stats"""
        try:
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            cpu_usage = cpu_stats.get('cpu_usage', {})
            precpu_usage = precpu_stats.get('cpu_usage', {})
            
            cpu_total = cpu_usage.get('total_usage', 0)
            precpu_total = precpu_usage.get('total_usage', 0)
            
            system_cpu = cpu_stats.get('system_cpu_usage', 0)
            presystem_cpu = precpu_stats.get('system_cpu_usage', 0)
            
            online_cpus = cpu_stats.get('online_cpus', 0)
            if online_cpus == 0:
                online_cpus = len(cpu_usage.get('percpu_usage', []))
            
            if online_cpus == 0:
                return 0.0
            
            cpu_delta = cpu_total - precpu_total
            system_delta = system_cpu - presystem_cpu
            
            if system_delta > 0.0:
                cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
                return round(cpu_percent, 2)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating CPU percentage: {e}")
            return 0.0
    
    def get_host_system_stats(self) -> Dict[str, Any]:
        """Get host system statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / 1024 / 1024 / 1024
            memory_available_gb = memory.available / 1024 / 1024 / 1024
            memory_used_gb = memory.used / 1024 / 1024 / 1024
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_total_gb = disk.total / 1024 / 1024 / 1024
            disk_used_gb = disk.used / 1024 / 1024 / 1024
            disk_free_gb = disk.free / 1024 / 1024 / 1024
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / 1024 / 1024
            network_recv_mb = network.bytes_recv / 1024 / 1024
            
            # Load average (Unix/Linux only)
            try:
                load_avg = psutil.getloadavg()
                load_1min, load_5min, load_15min = load_avg
            except:
                load_1min = load_5min = load_15min = 0.0
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_1min': load_1min,
                    'load_5min': load_5min,
                    'load_15min': load_15min
                },
                'memory': {
                    'total_gb': round(memory_total_gb, 2),
                    'used_gb': round(memory_used_gb, 2),
                    'available_gb': round(memory_available_gb, 2),
                    'percent': memory_percent
                },
                'disk': {
                    'total_gb': round(disk_total_gb, 2),
                    'used_gb': round(disk_used_gb, 2),
                    'free_gb': round(disk_free_gb, 2),
                    'percent': round(disk_percent, 2)
                },
                'network': {
                    'sent_mb': round(network_sent_mb, 2),
                    'recv_mb': round(network_recv_mb, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting host system stats: {e}")
            return {}
    
    async def get_comprehensive_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics including containers and host"""
        container_stats = await self.get_container_stats()
        host_stats = self.get_host_system_stats()
        
        # Convert container stats to dict format
        containers_dict = []
        for container in container_stats:
            containers_dict.append({
                'name': container.name,
                'status': container.status,
                'cpu_percent': container.cpu_percent,
                'memory_usage_mb': container.memory_usage_mb,
                'memory_limit_mb': container.memory_limit_mb,
                'memory_percent': container.memory_percent,
                'network_rx_mb': container.network_rx_mb,
                'network_tx_mb': container.network_tx_mb,
                'disk_read_mb': container.disk_read_mb,
                'disk_write_mb': container.disk_write_mb
            })
        
        # Calculate total stats
        total_containers = len(container_stats)
        running_containers = len([c for c in container_stats if c.status == 'running'])
        total_memory_usage = sum(c.memory_usage_mb for c in container_stats)
        total_cpu_usage = sum(c.cpu_percent for c in container_stats)
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'host': host_stats,
            'containers': {
                'total': total_containers,
                'running': running_containers,
                'total_memory_usage_mb': round(total_memory_usage, 2),
                'total_cpu_usage_percent': round(total_cpu_usage, 2),
                'details': containers_dict
            },
            'summary': {
                'healthy': running_containers == total_containers,
                'total_services': total_containers,
                'operational_services': running_containers,
                'system_load': host_stats.get('cpu', {}).get('percent', 0),
                'memory_pressure': host_stats.get('memory', {}).get('percent', 0) > 80,
                'disk_pressure': host_stats.get('disk', {}).get('percent', 0) > 80
            }
        }

# Global system monitor instance
system_monitor = SystemMonitor()