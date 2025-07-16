# 🚀 Session Continuity Quick Reference

## Essential Commands

### Starting Your Day
```bash
# Run this FIRST when you start Claude Code
mcp__fk-knowledge__resume_session()
```

### Ending Your Day
```bash
# Run this when you're done working
mcp__fk-knowledge__endsession(reason="work_complete")
```

## Command Reference

### Resume Session
```bash
# Standard resume (recommended)
mcp__fk-knowledge__resume_session()

# Quick summary (uses cache)
mcp__fk-knowledge__resume_session(quick_summary=true)

# Full context (bypasses cache)
mcp__fk-knowledge__resume_session(quick_summary=false)

# Resume specific project
mcp__fk-knowledge__resume_session(project="my-project")

# Resume without auto-initializing new session
mcp__fk-knowledge__resume_session(auto_initialize=false)
```

### End Session
```bash
# Standard end
mcp__fk-knowledge__endsession()

# End with specific reason
mcp__fk-knowledge__endsession(reason="debugging_complete")

# End with extended timeout
mcp__fk-knowledge__endsession(completion_timeout=60)

# End without exporting context
mcp__fk-knowledge__endsession(export_context=false)

# End without preparing resume
mcp__fk-knowledge__endsession(prepare_resume=false)
```

## What You Get

### Resume Session Output
- 📊 **Session Analysis**: Success rate, action counts, completion status
- 📝 **Recent Work**: Last actions, files modified, achievements
- 🎯 **Next Steps**: Intelligent recommendations for continuation
- ⚠️ **Warnings**: Issues that need attention
- 🆕 **New Session**: Automatically initialized with full context

### End Session Output
- ✅ **Data Persistence**: Context exported, resume prepared, database updated
- 📊 **Session Summary**: Total actions, success rate, files modified
- 🧹 **Cleanup Status**: All resources properly cleaned up
- 🔄 **Next Session Ready**: Resume information cached for tomorrow

## Workflow Examples

### Daily Development
```bash
# Morning
mcp__fk-knowledge__resume_session()
# ... work throughout the day ...
# Evening
mcp__fk-knowledge__endsession(reason="end_of_day")
```

### Debugging Session
```bash
# Start debugging
mcp__fk-knowledge__resume_session(quick_summary=true)
# ... debug issues ...
# End debugging
mcp__fk-knowledge__endsession(reason="debugging_complete")
```

### Feature Development
```bash
# Start feature work
mcp__fk-knowledge__resume_session()
# ... implement feature ...
# End feature work
mcp__fk-knowledge__endsession(reason="feature_complete")
```

## Troubleshooting

### If Resume Fails
- System automatically falls back to fresh session
- Check database connections are healthy
- Verify MCP Knowledge Server is running

### If End Session Hangs
- Default timeout is 30 seconds
- Increase with `completion_timeout=60`
- Check for stuck database operations

### If Context is Missing
- Try `quick_summary=false` for full database lookup
- Check Redis cache status
- Verify session was properly terminated

## Key Benefits
- 🧠 **Perfect Memory**: Never lose context between sessions
- 🎯 **Smart Resumption**: Always know where you left off
- 📚 **Searchable History**: All sessions preserved and searchable
- 🔄 **Seamless Workflow**: Smooth transitions between work sessions

## Files Location
- **Main Implementation**: `services/mcp-knowledge-server/src/knowledge_server.py`
- **Full Documentation**: `docs/SESSION_CONTINUITY_SYSTEM.md`
- **Test Suite**: `tests/test_session_continuity.py`

---

*The final piece of the FindersKeepers v2 puzzle! 🧩✨*