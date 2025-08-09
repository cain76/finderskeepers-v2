# FindersKeepers v2 - Automatic Background Processing

## Quick Deployment Guide

The FindersKeepers v2 system includes **automatic document processing** that starts immediately when you deploy the stack. No manual configuration or intervention required!

## 🚀 Deployment Instructions

### On a New Machine:

```bash
# 1. Clone the repository
git clone <repository-url>
cd finderskeepers-v2

# 2. Start all services
docker-compose down  # Clean any existing containers
docker-compose up -d # Start in detached mode

# 3. That's it! Background processing starts automatically
```

## ⚙️ How It Works

When you run `docker-compose up -d`, the background processor will:

1. **Wait 30 seconds** for all services to initialize
2. **Process 10 documents** every 5 minutes automatically
3. **Retry failed documents** up to 3 times
4. **Log all activity** to the FastAPI container logs

## 📊 Monitoring

### Check Processing Status:
```bash
# View recent processing activity
docker logs fk2_fastapi --tail 50 | grep -E "Processing|Batch|📄|✅"

# Watch live processing
docker logs -f fk2_fastapi | grep -E "Processing|Batch"

# Check processing statistics
curl http://localhost:8000/api/v1/stats
```

### Sample Output:
```
INFO: 🔍 Checking for unprocessed documents (batch size: 10)
INFO: 📄 Processing document: customer-incident-management-policy.md...
INFO: ✅ Processed: customer-incident-management-policy.md
INFO: 📈 Batch complete: 10 documents processed successfully
```

## 🔧 Configuration

The background processor is configured via environment variables in `docker-compose.yml`:

```yaml
# Background Document Processor Settings
- FK2_ENABLE_BACKGROUND_PROCESSING=true    # Enable/disable processing
- FK2_PROCESSING_INTERVAL_MINUTES=5        # Process every N minutes
- FK2_PROCESSING_BATCH_SIZE=10             # Documents per batch
- FK2_PROCESSING_MAX_RETRIES=3             # Retry attempts for failures
- FK2_PROCESSING_START_DELAY_SECONDS=30    # Initial startup delay
```

## 🛑 Disable Processing (if needed)

To temporarily disable automatic processing:

1. Edit `docker-compose.yml`
2. Set `FK2_ENABLE_BACKGROUND_PROCESSING=false`
3. Restart: `docker-compose restart fk2_fastapi`

## 🎯 Key Features

- **Zero Configuration**: Works out of the box
- **Smart Scheduling**: Processes in batches to avoid overload
- **Error Handling**: Automatic retry for failed documents
- **Resource Efficient**: Uses existing Ollama/Qdrant services
- **Observable**: Comprehensive logging for troubleshooting

## 📝 Notes for bitcain

- Optimized for your RTX 2080 Ti with CUDA toolkit
- Uses local Ollama (llama3.2:3b) for embeddings
- Stores vectors in Qdrant with 1024 dimensions
- Processes documents from PostgreSQL queue
- Updates Neo4j knowledge graph automatically

## 🐛 Troubleshooting

If processing isn't working:

```bash
# 1. Check if enabled
docker exec fk2_fastapi env | grep FK2_ENABLE

# 2. Check scheduler status
docker logs fk2_fastapi | grep "Scheduler started"

# 3. Check for errors
docker logs fk2_fastapi | grep ERROR

# 4. Restart the service
docker-compose restart fk2_fastapi
```

---

**No manual setup required!** Just `docker-compose up -d` and the system handles everything automatically.
