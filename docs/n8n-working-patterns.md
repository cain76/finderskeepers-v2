# n8n Working Patterns Reference

## Working Workflows - Proven Templates

### Agent Session Logger (WORKING)
File: `Agent Session Logger Actually Corrected.json`
- Webhook path: `agent-logger`
- Unique session_id generation: `{{ $now || $randomString(12) }}`
- Context handling: `{{ $json.body.context }}` with type "object"
- PostgreSQL: `mappingMode: "defineBelow"` with single `=` expressions
- FastAPI: Uses `JSON.stringify()` for context object

### Agent Action Tracker (WORKING) 
File: `Agent Action Tracker BOOOM.json`
- Webhook path: `agent-actions`
- Action_id generation: `{{ $json.body.action_id || $now + '_action_' + $randomString(8) }}`
- Foreign key: session_id must reference existing agent_sessions.session_id
- PostgreSQL: Mixed single/double equals (lines 88-89 had double equals bug - fixed!)
- FastAPI: Uses `JSON.stringify()` for details and files_affected arrays

## Critical n8n Expression Parser Understanding

### How n8n Equals Signs Work:
1. **First `=`**: Expression flag (tells n8n "this is code, not literal text")  
2. **Second `=`**: Start of actual expression syntax

**Examples:**
- `"value"` → Literal string "value"
- `="value"` → Expression that evaluates to "value"  
- `=={{ $json.field }}` → Expression that evaluates `{{ $json.field }}`

### The PostgreSQL Node Fix:
**WRONG:**
```json
"action_id": "={{ $json.action_id }}"   // ❌ Missing expression flag
```
**CORRECT:**
```json  
"action_id": "=={{ $json.action_id }}"  // ✅ Proper expression syntax!
```

**Key Insight**: Some n8n node fields require the double equals pattern while others work with single. PostgreSQL mapping fields specifically need `=={{ }}` syntax.

## Successful Agent Session Logger Pattern

Based on the working Agent Session Logger workflow, here are the proven patterns:

### Transform Node (Set) Pattern
```json
{
  "assignments": {
    "assignments": [
      {
        "id": "field_name",
        "name": "field_name", 
        "value": "={{ $json.body.field_name || 'default_value' }}",
        "type": "string|object|boolean"
      }
    ]
  }
}
```

### PostgreSQL Node Pattern
```json
{
  "schema": "public",
  "table": "table_name",
  "columns": {
    "mappingMode": "defineBelow",
    "value": {
      "field1": "={{ $json.field1 }}",
      "field2": "={{ $json.field2 }}"
    }
  }
}
```

### HTTP Request (FastAPI) Pattern
```json
{
  "method": "POST",
  "url": "http://fastapi/api/endpoint",
  "sendBody": true,
  "specifyBody": "json",
  "jsonBody": "={\n    \"field1\": \"{{ $('Transform Node Name').item.json.field1 }}\",\n    \"object_field\": {{ JSON.stringify($('Transform Node Name').item.json.object_field) }}\n}"
}
```

### Key Success Factors
1. **Webhook data access**: Use `$json.body.field_name` in Transform node
2. **Object handling**: Set type as "object" in Transform, use `JSON.stringify()` in HTTP request
3. **Node references**: Use `$('Transform Node Name').item.json.field` in subsequent nodes
4. **PostgreSQL mapping**: Use `mappingMode: "defineBelow"` with value object
5. **Unique IDs**: Use `$now || $randomString(12)` for unique identifiers