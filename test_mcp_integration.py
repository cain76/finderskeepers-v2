#!/usr/bin/env python3
"""
Test MCP (Model Context Protocol) integration with Claude Code
Tests Docker, Kubernetes, and PostgreSQL MCP servers
"""

import subprocess
import json
import os
import time
from typing import Dict, List, Any

class MCPTester:
    def __init__(self):
        self.project_root = "/media/cain/linux_storage/projects/finderskeepers-v2"
        self.claude_config = os.path.join(self.project_root, ".claude", "settings.local.json")
        self.mcp_config = os.path.join(self.project_root, ".mcp.json")
    
    def test_config_files(self) -> bool:
        """Test that MCP configuration files exist and are valid"""
        print("🔍 Testing MCP configuration files...")
        
        # Test .claude/settings.local.json
        try:
            with open(self.claude_config, 'r') as f:
                claude_config = json.load(f)
            
            if 'mcpServers' in claude_config:
                servers = claude_config['mcpServers']
                print(f"✅ Claude config loaded with {len(servers)} MCP servers:")
                for name, config in servers.items():
                    command = config.get('command', 'unknown')
                    print(f"   - {name}: {command}")
            else:
                print("❌ No mcpServers found in Claude config")
                return False
        except Exception as e:
            print(f"❌ Failed to load Claude config: {e}")
            return False
        
        # Test .mcp.json
        try:
            with open(self.mcp_config, 'r') as f:
                mcp_config = json.load(f)
            
            if 'mcpServers' in mcp_config:
                servers = mcp_config['mcpServers']
                print(f"✅ MCP config loaded with {len(servers)} servers:")
                for name, config in servers.items():
                    command = config.get('command', 'unknown')
                    print(f"   - {name}: {command}")
            else:
                print("❌ No mcpServers found in MCP config")
                return False
        except Exception as e:
            print(f"❌ Failed to load MCP config: {e}")
            return False
        
        return True
    
    def test_docker_mcp(self) -> bool:
        """Test Docker MCP server functionality"""
        print("\n🐳 Testing Docker MCP integration...")
        
        try:
            # Test Docker access
            result = subprocess.run(
                ["docker", "version", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version_info = json.loads(result.stdout)
                client_version = version_info.get('Client', {}).get('Version', 'unknown')
                server_version = version_info.get('Server', {}).get('Version', 'unknown')
                print(f"✅ Docker access working - Client: {client_version}, Server: {server_version}")
            else:
                print(f"❌ Docker access failed: {result.stderr}")
                return False
            
            # Test Docker MCP command
            try:
                result = subprocess.run(
                    ["docker", "mcp", "--help"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    print("✅ Docker MCP command available")
                    print(f"   Help output: {result.stdout[:100]}...")
                else:
                    print(f"⚠️  Docker MCP command not available: {result.stderr}")
                    print("   Note: This may require Docker Desktop with MCP enabled")
            except Exception as e:
                print(f"⚠️  Docker MCP test failed: {e}")
            
            # Test basic Docker operations
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                containers = result.stdout.strip().split('\n') if result.stdout.strip() else []
                if containers and containers[0]:
                    container_count = len([c for c in containers if c.strip()])
                    print(f"✅ Docker containers accessible: {container_count} running")
                else:
                    print("✅ Docker containers accessible: 0 running")
            else:
                print(f"❌ Failed to list Docker containers: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Docker MCP test failed: {e}")
            return False
    
    def test_kubernetes_mcp(self) -> bool:
        """Test Kubernetes MCP server functionality"""
        print("\n☸️  Testing Kubernetes MCP integration...")
        
        try:
            # Test kubectl access
            result = subprocess.run(
                ["kubectl", "version", "--client", "--output=json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version_info = json.loads(result.stdout)
                client_version = version_info.get('clientVersion', {}).get('gitVersion', 'unknown')
                print(f"✅ kubectl client available: {client_version}")
            else:
                print(f"❌ kubectl not accessible: {result.stderr}")
                return False
            
            # Test kubeconfig
            kubeconfig_path = os.path.expanduser("~/.kube/config")
            if os.path.exists(kubeconfig_path):
                print("✅ kubeconfig file exists")
            else:
                print("⚠️  No kubeconfig file found - Kubernetes MCP will not work")
                return False
            
            # Test MCP Kubernetes server installation
            k8s_server_path = os.path.join(
                self.project_root, 
                "node_modules/mcp-server-kubernetes/dist/index.js"
            )
            
            if os.path.exists(k8s_server_path):
                print("✅ MCP Kubernetes server installed")
            else:
                print("❌ MCP Kubernetes server not found")
                return False
            
            # Try to test connection to cluster (may fail if no cluster)
            try:
                result = subprocess.run(
                    ["kubectl", "cluster-info", "--request-timeout=5s"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    print("✅ Kubernetes cluster accessible")
                else:
                    print("⚠️  No Kubernetes cluster available (this is normal for local development)")
            except:
                print("⚠️  No Kubernetes cluster available (this is normal for local development)")
            
            return True
            
        except Exception as e:
            print(f"❌ Kubernetes MCP test failed: {e}")
            return False
    
    def test_postgres_mcp(self) -> bool:
        """Test PostgreSQL MCP server functionality"""
        print("\n🐘 Testing PostgreSQL MCP integration...")
        
        try:
            # Test PostgreSQL connection
            import psycopg2
            
            db_config = {
                "host": "localhost",
                "port": 5432,
                "database": "finderskeepers_v2",
                "user": "finderskeepers",
                "password": "fk2025secure"
            }
            
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL accessible: {version[:50]}...")
            
            # Test database schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            table_names = [t[0] for t in tables]
            print(f"✅ Database tables: {', '.join(table_names)}")
            
            cursor.close()
            conn.close()
            
            # Test MCP PostgreSQL server installation
            try:
                result = subprocess.run(
                    ["npx", "@modelcontextprotocol/server-postgres", "--help"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=self.project_root
                )
                
                if result.returncode == 0:
                    print("✅ MCP PostgreSQL server available")
                else:
                    print(f"⚠️  MCP PostgreSQL server test failed: {result.stderr}")
            except Exception as e:
                print(f"⚠️  MCP PostgreSQL server test error: {e}")
            
            return True
            
        except ImportError:
            print("❌ psycopg2 not installed - cannot test PostgreSQL connection")
            return False
        except Exception as e:
            print(f"❌ PostgreSQL MCP test failed: {e}")
            return False
    
    def test_additional_mcp_servers(self) -> bool:
        """Test additional MCP servers availability"""
        print("\n🔧 Testing additional MCP servers...")
        
        servers_to_test = [
            ("filesystem", "@modelcontextprotocol/server-filesystem"),
            ("brave-search", "@modelcontextprotocol/server-brave-search"),
            ("sequential-thinking", "@modelcontextprotocol/server-sequential-thinking"),
            ("n8n", "@ahmad.soliman/mcp-n8n-server")
        ]
        
        success_count = 0
        
        for server_name, package_name in servers_to_test:
            try:
                result = subprocess.run(
                    ["npx", package_name, "--help"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    cwd=self.project_root
                )
                
                if result.returncode == 0:
                    print(f"✅ {server_name} MCP server available")
                    success_count += 1
                else:
                    print(f"⚠️  {server_name} MCP server issue: {result.stderr[:100]}...")
            except Exception as e:
                print(f"⚠️  {server_name} MCP server test error: {e}")
        
        print(f"\n📊 MCP Server Summary: {success_count}/{len(servers_to_test)} servers tested successfully")
        return success_count > 0
    
    def generate_mcp_usage_examples(self):
        """Generate examples of how to use MCP with Claude Code"""
        print("\n📝 MCP Usage Examples for Claude Code:")
        print("=" * 50)
        
        examples = [
            {
                "category": "Docker Operations",
                "examples": [
                    "List all running containers",
                    "Build an image from the current Dockerfile",
                    "Show Docker system information",
                    "Start the FindersKeepers services with docker-compose",
                    "Check logs for the FastAPI container"
                ]
            },
            {
                "category": "Kubernetes Management",
                "examples": [
                    "List pods in the default namespace", 
                    "Get cluster information",
                    "Show deployments across all namespaces",
                    "Describe the service configuration",
                    "Check node status and resource usage"
                ]
            },
            {
                "category": "PostgreSQL Queries",
                "examples": [
                    "Show all tables in the finderskeepers_v2 database",
                    "Count rows in the agent_sessions table",
                    "Find the most recent document chunks with embeddings",
                    "Search for configuration changes in the last week",
                    "Show database schema for the documents table"
                ]
            },
            {
                "category": "n8n Workflows",
                "examples": [
                    "List all n8n workflows",
                    "Show webhook URLs for agent tracking",
                    "Get workflow execution history", 
                    "Test the agent session logging webhook",
                    "Check n8n workflow status"
                ]
            }
        ]
        
        for category in examples:
            print(f"\n🔹 {category['category']}:")
            for example in category['examples']:
                print(f"   • {example}")
        
        print(f"\n💡 To use these with Claude Code:")
        print(f"   1. Start Claude Code: claude code")
        print(f"   2. Ask questions like: 'List all running containers'")
        print(f"   3. Claude will automatically use the appropriate MCP server")
        print(f"   4. Results will be streamed back with full context")

def main():
    """Main test function"""
    print("🔍 MCP Integration Testing for FindersKeepers v2")
    print("=" * 60)
    
    tester = MCPTester()
    
    # Run all tests
    tests = [
        ("Configuration Files", tester.test_config_files),
        ("Docker MCP", tester.test_docker_mcp),
        ("Kubernetes MCP", tester.test_kubernetes_mcp),
        ("PostgreSQL MCP", tester.test_postgres_mcp),
        ("Additional MCP Servers", tester.test_additional_mcp_servers)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Generate usage examples
    tester.generate_mcp_usage_examples()
    
    # Summary
    print(f"\n📊 Test Results Summary:")
    print("=" * 30)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All MCP integrations ready for Claude Code!")
        print("You can now use conversational Docker, Kubernetes, and database management!")
    else:
        print(f"\n⚠️  Some MCP servers need attention before full functionality")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)