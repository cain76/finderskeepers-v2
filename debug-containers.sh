#!/bin/bash
# debug-containers.sh
# Check what's actually running and network connectivity

echo "🔍 Debugging FindersKeepers Container Setup"
echo "==========================================="

echo ""
echo "1. Container Status Check..."
echo "Docker containers with 'fk2' in name:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(fk2|finderskeepers)" || echo "No containers found with 'fk2' prefix"

echo ""
echo "All Docker containers:"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "2. PostgreSQL Container Check..."
if docker ps -q -f name=fk2_postgres > /dev/null; then
    echo "✅ fk2_postgres container is running"
    
    # Check PostgreSQL is actually responding
    if docker exec fk2_postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo "✅ PostgreSQL service is ready"
        
        # Check if our database exists
        echo "Checking databases..."
        docker exec fk2_postgres psql -U postgres -l
        
    else
        echo "❌ PostgreSQL service is not ready"
        echo "PostgreSQL logs:"
        docker logs fk2_postgres --tail=10
    fi
else
    echo "❌ fk2_postgres container is not running"
    echo "Looking for any postgres containers..."
    docker ps | grep postgres || echo "No postgres containers found"
fi

echo ""
echo "3. n8n Container Check..."
if docker ps -q -f name=fk2_n8n > /dev/null; then
    echo "✅ fk2_n8n container is running"
    
    echo "Recent n8n logs (last 20 lines):"
    docker logs fk2_n8n --tail=20
    
else
    echo "❌ fk2_n8n container is not running"
    echo "Looking for any n8n containers..."
    docker ps | grep n8n || echo "No n8n containers found"
fi

echo ""
echo "4. Docker Network Inspection..."

# Find networks both containers are on
if docker ps -q -f name=fk2_postgres > /dev/null && docker ps -q -f name=fk2_n8n > /dev/null; then
    echo "n8n networks:"
    docker inspect fk2_n8n | jq -r '.[0].NetworkSettings.Networks | keys[]' 2>/dev/null
    
    echo "PostgreSQL networks:"
    docker inspect fk2_postgres | jq -r '.[0].NetworkSettings.Networks | keys[]' 2>/dev/null
    
    # Test connectivity from n8n to postgres
    echo ""
    echo "Testing network connectivity from n8n to postgres..."
    if docker exec fk2_n8n sh -c "nc -z fk2_postgres 5432" 2>/dev/null; then
        echo "✅ n8n can reach fk2_postgres:5432"
    else
        echo "❌ n8n cannot reach fk2_postgres:5432"
        echo "This is the root cause of the database connection issue!"
    fi
else
    echo "Cannot test networking - one or both containers not running"
fi

echo ""
echo "5. Database Connection Test..."

# Try to connect to database with various connection strings
DB_CONTAINERS=("fk2_postgres" "postgres" "finderskeepers_postgres" "finderskeepers-postgres")
DB_NAMES=("finderskeepers_v2" "finderskeepers" "postgres")
DB_USERS=("finderskeepers" "postgres")

for container in "${DB_CONTAINERS[@]}"; do
    if docker ps -q -f name=$container > /dev/null; then
        echo "Found container: $container"
        
        for db_name in "${DB_NAMES[@]}"; do
            for db_user in "${DB_USERS[@]}"; do
                echo "  Testing: $db_user@$container/$db_name"
                if docker exec $container psql -U $db_user -d $db_name -c "SELECT 1;" > /dev/null 2>&1; then
                    echo "  ✅ Connection successful: $db_user@$container/$db_name"
                    
                    # Check for our required tables
                    echo "  Checking for required tables..."
                    docker exec $container psql -U $db_user -d $db_name -c "
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('agent_sessions', 'agent_actions', 'conversation_messages')
                    ORDER BY table_name;"
                    break 2
                else
                    echo "  ❌ Failed: $db_user@$container/$db_name"
                fi
            done
        done
    fi
done

echo ""
echo "6. Suggested Next Steps..."
echo "========================"

if ! docker ps -q -f name=fk2_postgres > /dev/null; then
    echo "❌ PostgreSQL container not running - start it first"
    echo "   Check your docker-compose.yml and run: docker-compose up -d"
elif ! docker exec fk2_n8n sh -c "nc -z fk2_postgres 5432" 2>/dev/null; then
    echo "❌ Network connectivity issue between containers"
    echo "   1. Check both containers are on same network"
    echo "   2. Restart containers: docker-compose restart"
    echo "   3. Check docker-compose.yml network configuration"
else
    echo "✅ Containers are running and can communicate"
    echo "   The issue is likely PostgreSQL credentials in n8n"
    echo "   Run: ./fix-n8n-postgres-credentials.sh"
fi