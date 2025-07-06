# n8n Workflow Automation Guide for FindersKeepers v2

## Overview

n8n is a fair-code workflow automation platform that combines visual building with custom code capabilities. This guide covers everything needed to effectively use n8n for the FindersKeepers v2 project.

## Core Concepts

### Architecture
- **Visual Workflow Builder**: Drag-and-drop interface for creating automation flows
- **Node-Based System**: Each step in a workflow is represented by a node
- **JSON-Based Storage**: Workflows are stored and transmitted as JSON objects
- **REST API**: Full CRUD operations available via authenticated API calls
- **Self-Hosted**: Running locally in Docker container with full control

### Node Types
1. **Trigger Nodes**: Start workflows
   - Webhook: HTTP endpoint triggers
   - Cron: Scheduled execution
   - Manual: User-initiated
   - Error Trigger: Handles workflow failures

2. **Regular Nodes**: Process and transform data
   - HTTP Request: Call external APIs
   - Set: Transform/clean data
   - IF: Conditional logic
   - Function: Custom JavaScript
   - Loop Over Items: Batch processing

3. **Integration Nodes**: Third-party services
   - Database connectors
   - Communication tools (Discord, Slack)
   - Storage services
   - AI/ML services

4. **Response Nodes**: Send outputs
   - Respond to Webhook: HTTP responses
   - Email: Send notifications
   - File Write: Save to filesystem

## API Operations

### Authentication
```bash
# All API calls require X-N8N-API-KEY header
curl -H "X-N8N-API-KEY: your-api-key" http://localhost:5678/api/v1/workflows
```

### Workflow Management
```bash
# List workflows
GET /api/v1/workflows

# Create workflow
POST /api/v1/workflows
Content-Type: application/json
{
  "name": "Workflow Name",
  "settings": {},
  "nodes": [...],
  "connections": {...}
}

# Activate workflow
POST /api/v1/workflows/{id}/activate

# Update workflow
PATCH /api/v1/workflows/{id}

# Delete workflow
DELETE /api/v1/workflows/{id}
```

### Workflow JSON Structure
```json
{
  "name": "string",
  "settings": {},
  "nodes": [
    {
      "parameters": {},
      "id": "unique-id",
      "name": "Node Name",
      "type": "n8n-nodes-base.nodetype",
      "typeVersion": 1,
      "position": [x, y]
    }
  ],
  "connections": {
    "Source Node": {
      "main": [
        [
          {
            "node": "Target Node",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "active": false
}
```

## Data Flow & Expressions

### Data Passing
- Nodes pass JSON data through connections
- Each node receives input from previous nodes
- Output becomes input for connected nodes

### Expression Syntax
```javascript
// Reference current node data
{{ $json.fieldName }}

// Reference specific node data
{{ $node["Node Name"].json.fieldName }}

// Built-in variables
{{ $now }}                    // Current timestamp
{{ $execution.id }}           // Unique execution ID
{{ $execution.resumeUrl }}    // Webhook resume URL

// Array operations
{{ $json.items.length }}      // Array length
{{ $json.items[0].field }}    // First item field
```

### Common Patterns
```javascript
// Transform data in Set node
{
  "timestamp": "{{ $now }}",
  "processedData": "{{ $json.rawData.toUpperCase() }}",
  "userInfo": {
    "id": "{{ $json.user.id }}",
    "name": "{{ $json.user.firstName }} {{ $json.user.lastName }}"
  }
}

// Conditional logic in IF node
{{ $json.status === "active" && $json.score > 85 }}

// Loop processing
// Use Loop Over Items node for batch operations
```

## Security & Credentials

### Credential Management
- Store sensitive data in n8n credential system
- Reference credentials in nodes by ID/name
- Support for multiple authentication methods:
  - API Keys
  - Basic Auth
  - OAuth2
  - JWT
  - Custom headers

### Webhook Security
```json
{
  "parameters": {
    "authentication": "basicAuth",
    "httpMethod": "POST",
    "path": "secure-endpoint"
  }
}
```

## Error Handling

### Error Workflows
- Create dedicated error handling workflows
- Use Error Trigger node to catch failures
- Automatic execution data passing
- Centralized notification system

```json
{
  "nodes": [
    {
      "type": "n8n-nodes-base.errorTrigger",
      "name": "Error Trigger"
    },
    {
      "type": "n8n-nodes-base.slack",
      "name": "Alert Team",
      "parameters": {
        "text": "Workflow {{ $node['Error Trigger'].json.workflow.name }} failed"
      }
    }
  ]
}
```

### Stop And Error Node
- Manually trigger workflow failure
- Useful for validation and testing
- Passes control to error workflow

## Rate Limiting & Performance

### Batch Processing Pattern
```
1. Loop Over Items (batch size: 10)
2. HTTP Request (process batch)
3. Wait (delay: 1000ms)
4. Loop back to step 1
```

### Best Practices
- Use appropriate delays between API calls
- Implement exponential backoff for retries
- Monitor execution times and optimize bottlenecks
- Use pagination for large datasets

## FindersKeepers v2 Integration

### Architecture Integration
- Use HTTP Request nodes to call FastAPI endpoints
- Maintain API layer rather than direct database access
- Leverage existing authentication and validation
- Build on established data models

### Key Endpoints
```bash
# Agent session tracking
POST /api/diary/sessions
POST /api/diary/actions

# Knowledge management
POST /api/knowledge/query
POST /api/docs/ingest

# Configuration tracking
POST /api/config/log-change
GET /api/config/history
```

### Recommended Workflows

1. **Agent Activity Logger**
   - Webhook → Validate → FastAPI Call → Response
   - Automatic session and action tracking

2. **Document Processing Pipeline**
   - File Upload → AI Processing → Vector Storage → Metadata Update

3. **Knowledge Query Handler**
   - Natural Language Input → Vector Search → Context Assembly → AI Response

4. **System Health Monitor**
   - Scheduled Checks → Service Status → Alert on Failures

5. **Configuration Sync**
   - Config Change Detection → Validation → Application → Audit Log

## Best Practices

### Workflow Design
1. Start simple: Trigger → Process → Respond
2. Add error handling early
3. Use descriptive node names
4. Keep workflows focused on single responsibilities
5. Document complex logic in Function nodes

### Data Management
1. Clean data early in the pipeline
2. Use Set nodes for transformations
3. Validate inputs before processing
4. Include timestamps and execution IDs
5. Handle edge cases explicitly

### Security
1. Never hardcode secrets in workflows
2. Use credential management system
3. Implement webhook authentication
4. Log security events appropriately
5. Regular credential rotation

### Performance
1. Minimize external API calls
2. Use caching where appropriate
3. Implement proper error boundaries
4. Monitor execution metrics
5. Optimize data transformations

### Maintenance
1. Version control workflow exports
2. Document business logic
3. Test workflows thoroughly
4. Monitor execution success rates
5. Regular workflow audits

## Debugging & Monitoring

### Execution Logs
- View detailed execution data
- Track node-level performance
- Debug data transformations
- Monitor error patterns

### Custom Logging
```javascript
// In Function node
import { LoggerProxy as Logger } from 'n8n-workflow';

Logger.info('Processing user data', {
  userId: items[0].json.userId,
  workflowId: workflow.id
});
```

### Health Checks
- Monitor workflow execution rates
- Track API response times
- Alert on consecutive failures
- Performance trend analysis

This guide provides the foundation for building robust, maintainable automation workflows that integrate seamlessly with the FindersKeepers v2 architecture.