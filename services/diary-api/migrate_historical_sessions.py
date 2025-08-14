#!/usr/bin/env python3
"""
Phase 4.6.1: Historical Session Data Migration
FindersKeepers v2 - Critical Gap Resolution

This script migrates the 19 existing agent sessions and 15 actions from PostgreSQL
into the Neo4j knowledge graph and Qdrant vector store, enabling MCP knowledge queries
to return results and achieving "complete knowledge dominance".

CRITICAL: This addresses the gap where session data exists but isn't searchable.
"""

import asyncio
import json
import logging
import os
import httpx
from typing import List, Dict, Any
from datetime import datetime
import asyncpg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionDataMigrator:
    """Migrates historical session data to knowledge stores"""
    
    def __init__(self):
        # Database connections (using Docker container names)
        self.postgres_url = "postgresql://finderskeepers:fk2025secure@postgres:5432/finderskeepers_v2"
        self.fastapi_url = "http://fastapi:80"  # FastAPI runs on port 80 inside container
        
        # Migration stats
        self.stats = {
            "sessions_processed": 0,
            "actions_processed": 0,
            "documents_created": 0,
            "errors": []
        }
    
    async def migrate_all_sessions(self):
        """Main migration function - processes all historical data"""
        logger.info("🚀 Starting Phase 4.6.1: Historical Session Data Migration")
        logger.info("🎯 OBJECTIVE: Unlock knowledge dominance by making 19 sessions searchable")
        
        try:
            # Step 1: Extract session data from PostgreSQL
            sessions = await self.extract_sessions_from_postgres()
            actions = await self.extract_actions_from_postgres()
            
            logger.info(f"📊 Found {len(sessions)} sessions and {len(actions)} actions to migrate")
            
            # Step 2: Process sessions through ingestion pipeline
            for session in sessions:
                try:
                    await self.process_session_to_knowledge_graph(session, actions)
                    self.stats["sessions_processed"] += 1
                    logger.info(f"✅ Migrated session: {session['session_id']}")
                except Exception as e:
                    error_msg = f"❌ Failed to migrate session {session['session_id']}: {e}"
                    logger.error(error_msg)
                    self.stats["errors"].append(error_msg)
            
            # Step 3: Report migration results
            await self.report_migration_results()
            
        except Exception as e:
            logger.error(f"💥 Migration failed: {e}")
            raise
    
    async def extract_sessions_from_postgres(self) -> List[Dict[str, Any]]:
        """Extract all agent sessions from PostgreSQL"""
        logger.info("🔍 Extracting sessions from PostgreSQL...")
        
        try:
            conn = await asyncpg.connect(self.postgres_url)
            
            rows = await conn.fetch("""
                SELECT 
                    session_id,
                    agent_type,
                    user_id,
                    project,
                    start_time,
                    end_time,
                    context
                FROM agent_sessions
                ORDER BY start_time DESC
            """)
            
            sessions = [dict(row) for row in rows]
            
            await conn.close()
            
            logger.info(f"📦 Extracted {len(sessions)} sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"❌ Failed to extract sessions: {e}")
            raise
    
    async def extract_actions_from_postgres(self) -> List[Dict[str, Any]]:
        """Extract all agent actions from PostgreSQL"""
        logger.info("🔍 Extracting actions from PostgreSQL...")
        
        try:
            conn = await asyncpg.connect(self.postgres_url)
            
            rows = await conn.fetch("""
                SELECT 
                    action_id,
                    session_id,
                    timestamp,
                    action_type,
                    description,
                    details,
                    files_affected,
                    success
                FROM agent_actions
                ORDER BY timestamp DESC
            """)
            
            actions = [dict(row) for row in rows]
            
            await conn.close()
            
            logger.info(f"⚡ Extracted {len(actions)} actions")
            return actions
            
        except Exception as e:
            logger.error(f"❌ Failed to extract actions: {e}")
            raise
    
    async def process_session_to_knowledge_graph(self, session: Dict[str, Any], all_actions: List[Dict[str, Any]]):
        """Convert session + actions into knowledge graph document"""
        
        # Get actions for this session
        session_actions = [a for a in all_actions if a['session_id'] == session['session_id']]
        
        # Create comprehensive session document
        session_doc = self.create_session_document(session, session_actions)
        
        # Send to ingestion API for processing
        await self.ingest_session_document(session_doc)
        
        self.stats["actions_processed"] += len(session_actions)
        self.stats["documents_created"] += 1
    
    def create_session_document(self, session: Dict[str, Any], actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a comprehensive document from session + actions"""
        
        # Build session narrative
        narrative_parts = [
            f"Agent Session: {session['session_id']}",
            f"Agent Type: {session['agent_type']}",
            f"Project: {session.get('project', 'unknown')}",
            f"Started: {session['start_time']}",
            f"User: {session.get('user_id', 'unknown')}"
        ]
        
        if session.get('context'):
            try:
                context = json.loads(session['context']) if isinstance(session['context'], str) else session['context']
                narrative_parts.append(f"Context: {json.dumps(context, indent=2)}")
            except:
                narrative_parts.append(f"Context: {session['context']}")
        
        # Add actions to narrative
        if actions:
            narrative_parts.append("\nSession Actions:")
            for action in sorted(actions, key=lambda x: x['timestamp']):
                action_text = [
                    f"- {action['timestamp']}: {action['action_type']}",
                    f"  Description: {action['description']}",
                    f"  Success: {action['success']}"
                ]
                
                if action.get('files_affected'):
                    try:
                        files = json.loads(action['files_affected']) if isinstance(action['files_affected'], str) else action['files_affected']
                        if files:
                            action_text.append(f"  Files: {', '.join(files)}")
                    except:
                        action_text.append(f"  Files: {action['files_affected']}")
                
                if action.get('details'):
                    try:
                        details = json.loads(action['details']) if isinstance(action['details'], str) else action['details']
                        action_text.append(f"  Details: {json.dumps(details, indent=4)}")
                    except:
                        action_text.append(f"  Details: {action['details']}")
                
                narrative_parts.append("\n".join(action_text))
        
        # Create document for ingestion
        document = {
            "title": f"Agent Session: {session['session_id']} ({session['agent_type']})",
            "content": "\n\n".join(narrative_parts),
            "project": session.get('project', 'finderskeepers-v2'),
            "doc_type": "agent_session",
            "tags": [
                "agent_session",
                session['agent_type'],
                f"project_{session.get('project', 'unknown')}",
                "historical_migration"
            ],
            "metadata": {
                "session_id": session['session_id'],
                "agent_type": session['agent_type'],
                "start_time": session['start_time'].isoformat() if session['start_time'] else None,
                "end_time": session['end_time'].isoformat() if session['end_time'] else None,
                "action_count": len(actions),
                "migration_timestamp": datetime.utcnow().isoformat(),
                "migration_phase": "4.6.1"
            }
        }
        
        return document
    
    async def ingest_session_document(self, document: Dict[str, Any]):
        """Send session document to ingestion API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.fastapi_url}/api/docs/ingest",
                    json=document
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"📝 Ingested session document: {result.get('document_id')}")
                
        except Exception as e:
            logger.error(f"❌ Failed to ingest session document: {e}")
            raise
    
    async def report_migration_results(self):
        """Report final migration statistics"""
        logger.info("📊 PHASE 4.6.1 MIGRATION COMPLETE!")
        logger.info("=" * 50)
        logger.info(f"✅ Sessions Processed: {self.stats['sessions_processed']}")
        logger.info(f"⚡ Actions Processed: {self.stats['actions_processed']}")
        logger.info(f"📝 Documents Created: {self.stats['documents_created']}")
        logger.info(f"❌ Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            logger.info("\n🔍 Error Details:")
            for error in self.stats['errors']:
                logger.info(f"  - {error}")
        
        logger.info("=" * 50)
        logger.info("🎯 KNOWLEDGE DOMINANCE STATUS: Session data now searchable via MCP!")
        logger.info("🚀 Ready for Phase 4.6.2: Real-Time Session Ingestion Pipeline")

async def main():
    """Run the migration"""
    migrator = SessionDataMigrator()
    await migrator.migrate_all_sessions()

if __name__ == "__main__":
    asyncio.run(main())