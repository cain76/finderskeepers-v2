# Document Ingestion Issues - Diagnostic Report
*Generated: 2025-07-11*

## 🎯 **ROOT CAUSE SUMMARY**

Based on detailed analysis of logs, code, and docker containers, here are the core issues causing document ingestion problems:

## 🔴 **Critical Issues Identified**

### **Issue #1: FastAPI Container Not Running**
- **Status**: Container failed to start
- **Evidence**: `docker ps` shows no `fk2_fastapi` container running
- **Impact**: Document ingestion API completely unavailable
- **Fix**: Rebuild container with proper dependencies

### **Issue #2: EasyOCR Missing System Dependencies**
- **Status**: Container builds but OCR fails at runtime
- **Evidence**: `WARNING:root:EasyOCR not available: libGL.so.1: cannot open shared object file`
- **Root Cause**: Missing OpenGL libraries in Docker container
- **Impact**: Documents requiring OCR processing (PDFs with images, scanned docs) fail
- **Fix Applied**: Added required packages to Dockerfile:
  ```dockerfile
  libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
  ```

### **Issue #3: WebSocket Protocol Mismatch**
- **Status**: Frontend/Backend communication broken
- **Evidence**: 
  ```
  INFO: 172.18.0.1:42048 - "WebSocket /socket.io/?EIO=4&transport=websocket" 403
  INFO: connection rejected (403 Forbidden)
  ```
- **Root Cause**: Frontend attempting Socket.IO connections (`/socket.io/`) but backend only has plain WebSocket (`/ws/{client_id}`)
- **Impact**: Real-time progress tracking fails, causing "Failed after 3 retries" messages
- **Fix Needed**: Either implement Socket.IO server or change frontend to use plain WebSocket

### **Issue #4: Fake Progress Tracking**
- **Status**: Progress tracking using simulated timers
- **Evidence**: 
  ```javascript
  // Start progress tracking
  const progressInterval = setInterval(() => {
    setUploadProgress(prev => prev.map((item, i) => 
      i === index && item.progress < 90 
        ? { ...item, progress: Math.min(90, item.progress + Math.random() * 15) }
        : item
    ));
  }, 500);
  ```
- **Impact**: Users see fake progress that doesn't reflect actual processing status
- **Fix Needed**: Implement real WebSocket-based progress tracking

### **Issue #5: Multiple Upload Duplicates**
- **Status**: Single file upload triggers multiple API calls
- **Evidence**: 
  ```
  INFO: 172.18.0.1:57034 - "POST /api/v1/ingestion/single HTTP/1.1" 200 OK
  INFO: 172.18.0.1:57034 - "POST /api/v1/ingestion/single HTTP/1.1" 200 OK  
  INFO: 172.18.0.1:57034 - "POST /api/v1/ingestion/single HTTP/1.1" 200 OK
  INFO: 172.18.0.1:57034 - "POST /api/v1/ingestion/single HTTP/1.1" 200 OK
  ```
- **Root Cause**: Retry logic in frontend combined with async/await issues
- **Impact**: Document count jumps by multiple documents instead of one
- **Fix Needed**: Prevent retry logic when upload actually succeeds

## 🟡 **Secondary Issues**

### **Issue #6: Container Build Performance**
- **Status**: Docker builds timing out due to large dependencies
- **Evidence**: Build taking 10+ minutes, timing out at 600s
- **Impact**: Development workflow slow, container updates delayed
- **Recommendation**: Use multi-stage builds, optimize dependency layers

### **Issue #7: Frontend Upload State Management**
- **Status**: Upload state not properly managed between retries
- **Evidence**: Files showing "Failed after 3 retries" even when backend shows 200 OK
- **Impact**: User sees failures when uploads actually succeed
- **Fix Needed**: Better state synchronization between frontend and backend

## 🔧 **IMMEDIATE FIXES APPLIED**

1. ✅ **Added EasyOCR Dependencies to Dockerfile**
   - Added OpenGL libraries required for EasyOCR
   - Container will now support OCR processing of images and PDFs

2. ✅ **Identified WebSocket Protocol Mismatch**
   - Documented exact issue: Socket.IO vs plain WebSocket
   - Ready to implement solution when container is rebuilt

## 🚀 **PRIORITY FIX SEQUENCE**

### **Phase 1: Get System Running (Immediate)**
1. Complete FastAPI container rebuild with EasyOCR dependencies
2. Start all services with `docker compose up -d`
3. Verify basic document ingestion works (without OCR/progress tracking)

### **Phase 2: Fix Core Upload Issues (Next 30 min)**
1. Fix WebSocket protocol mismatch:
   - **Option A**: Add Socket.IO to FastAPI backend
   - **Option B**: Change frontend to use plain WebSocket
   - **Recommendation**: Option B (simpler, fewer dependencies)

2. Fix multiple upload issue:
   - Add upload deduplication logic
   - Prevent retry when upload actually succeeds
   - Better error handling to distinguish real failures from timeout issues

### **Phase 3: Implement Real Progress Tracking (Next 60 min)**
1. Replace fake timer-based progress with real WebSocket updates
2. Backend sends actual processing progress events
3. Frontend receives and displays real-time status

### **Phase 4: Optimize Performance (Later)**
1. Multi-stage Docker builds for faster rebuilds
2. Optimize dependency installation
3. Add upload resumption capabilities

## 📊 **CURRENT SERVICE STATUS**

| Service | Status | Port | Notes |
|---------|--------|------|-------|
| PostgreSQL | ✅ Running | 5432 | Database healthy |
| Neo4j | ✅ Running | 7474/7687 | Graph DB healthy |  
| Qdrant | ✅ Running | 6333 | Vector DB healthy |
| Redis | ✅ Running | 6379 | Cache healthy |
| Ollama | ✅ Running | 11434 | Local LLM healthy |
| n8n | ✅ Running | 5678 | Workflow engine healthy |
| Frontend | ✅ Running | 3000 | React app healthy |
| **FastAPI** | ❌ **Not Running** | 8000 | **CONTAINER REBUILD NEEDED** |

## 🔬 **TECHNICAL DETAILS**

### **WebSocket Fix - Option B (Recommended)**
Change frontend from Socket.IO to plain WebSocket:

```javascript
// Replace Socket.IO connection
const socket = new WebSocket(`ws://localhost:8000/ws/${clientId}`);

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'upload_progress') {
    setUploadProgress(prev => prev.map((item, i) => 
      i === data.fileIndex ? { ...item, progress: data.progress } : item
    ));
  }
};
```

### **Backend WebSocket Progress Updates**
```python
# In FastAPI ingestion endpoint
await websocket.send_text(json.dumps({
  "type": "upload_progress",
  "fileIndex": file_index,
  "progress": current_progress,
  "status": "processing"
}))
```

### **Upload Deduplication Logic**
```javascript
// Prevent duplicate uploads
const uploadInProgress = useRef(new Set());

const uploadSingleFile = async (file, index) => {
  const fileKey = `${file.name}-${file.size}-${file.lastModified}`;
  
  if (uploadInProgress.current.has(fileKey)) {
    console.log(`Upload already in progress for ${file.name}`);
    return;
  }
  
  uploadInProgress.current.add(fileKey);
  
  try {
    // ... actual upload logic
  } finally {
    uploadInProgress.current.delete(fileKey);
  }
};
```

## 🎯 **SUCCESS CRITERIA**

When fixes are complete, verify:
- [ ] FastAPI container runs successfully
- [ ] Single file upload creates exactly one document
- [ ] Progress tracking shows real processing status
- [ ] OCR processing works for image-based documents
- [ ] No WebSocket 403 errors in logs
- [ ] Upload retry logic only triggers on actual failures
- [ ] Document count increments correctly

## 📝 **NEXT STEPS FOR DEVELOPER**

1. **Monitor current Docker build** - Let it complete or restart if needed
2. **Test basic upload** once FastAPI is running
3. **Implement WebSocket fix** using Option B (plain WebSocket)
4. **Add upload deduplication** to prevent multiple API calls
5. **Replace fake progress** with real WebSocket-based tracking

The system architecture is sound - these are implementation details that can be fixed systematically without major changes to the core design.