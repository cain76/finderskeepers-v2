"""
Neo4j Knowledge Graph Client for MCP Knowledge Server
Handles graph queries, entity relationships, and knowledge exploration
"""

import asyncio
import logging
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import Neo4j driver
try:
    from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not available")

logger = logging.getLogger(__name__)

class Neo4jClient:
    """Async Neo4j client for knowledge graph operations"""
    
    def __init__(self):
        self.driver: Optional[AsyncDriver] = None
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "fk2025neo4j")
        
    async def connect(self):
        """Initialize connection to Neo4j"""
        if not NEO4J_AVAILABLE:
            logger.error("Neo4j driver not available")
            return
            
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                keep_alive=True
            )
            
            # Test connection
            async with self.driver.session() as session:
                result = await session.run("RETURN 'Connected to Neo4j' as message")
                record = await result.single()
                logger.info(f"Neo4j: {record['message']}")
                
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None
            
    async def disconnect(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
            self.driver = None
            
    async def extract_keywords(self, question: str) -> List[str]:
        """
        Extract meaningful keywords from a natural language question
        
        Args:
            question: Natural language question
            
        Returns:
            List of extracted keywords
        """
        # Simple keyword extraction - can be enhanced with NLP
        # Remove common stop words and extract meaningful terms
        stop_words = {
            "what", "who", "where", "when", "why", "how", "is", "are", "was", "were",
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "about", "between", "find", "show", "list", "get"
        }
        
        # Clean and split the question
        words = re.findall(r'\b[a-zA-Z]{3,}\b', question.lower())
        keywords = [word for word in words if word not in stop_words]
        
        # Return unique keywords
        return list(set(keywords))
    
    async def query_entities_and_relationships(
        self,
        keywords: List[str],
        entity_types: Optional[List[str]] = None,
        max_depth: int = 2,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Query entities and relationships based on keywords
        
        Args:
            keywords: Keywords to search for
            entity_types: Types of entities to focus on
            max_depth: Maximum traversal depth
            limit: Maximum number of results
            
        Returns:
            Dictionary with entities and relationships
        """
        if not self.driver or not keywords:
            return {"entities": [], "relationships": []}
            
        try:
            async with self.driver.session() as session:
                # Build keyword matching pattern
                keyword_conditions = []
                for i, keyword in enumerate(keywords[:5]):  # Limit to 5 keywords
                    keyword_conditions.append(f"toLower(n.name) CONTAINS toLower($keyword{i})")
                
                keyword_clause = " OR ".join(keyword_conditions)
                
                # Build entity type filter
                type_clause = ""
                if entity_types:
                    type_labels = ":".join(entity_types)
                    type_clause = f" AND (n:{type_labels})"
                
                # Query for entities
                entity_query = f"""
                    MATCH (n)
                    WHERE ({keyword_clause}){type_clause}
                    RETURN n, labels(n) as types
                    LIMIT $limit
                """
                
                # Build parameters
                params = {f"keyword{i}": keyword for i, keyword in enumerate(keywords[:5])}
                params["limit"] = limit
                
                # Execute entity query
                entity_result = await session.run(entity_query, params)
                entities = []
                entity_ids = set()
                
                async for record in entity_result:
                    node = record["n"]
                    node_id = node.element_id
                    entity_ids.add(node_id)
                    
                    entities.append({
                        "id": node_id,
                        "name": node.get("name", "Unknown"),
                        "type": record["types"][0] if record["types"] else "Unknown",
                        "properties": dict(node)
                    })
                
                # Query for relationships between found entities
                relationships = []
                if entity_ids and max_depth > 0:
                    # Get relationships between entities (up to max_depth)
                    rel_query = f"""
                        MATCH (n)-[r]->(m)
                        WHERE elementId(n) IN $entity_ids OR elementId(m) IN $entity_ids
                        RETURN n, r, m, type(r) as rel_type
                        LIMIT {limit * 2}
                    """
                    
                    rel_result = await session.run(rel_query, {"entity_ids": list(entity_ids)})
                    
                    async for record in rel_result:
                        source_node = record["n"]
                        target_node = record["m"]
                        relationship = record["r"]
                        
                        relationships.append({
                            "source_id": source_node.element_id,
                            "source_name": source_node.get("name", "Unknown"),
                            "target_id": target_node.element_id,
                            "target_name": target_node.get("name", "Unknown"),
                            "relationship_type": record["rel_type"],
                            "properties": dict(relationship)
                        })
                
                return {
                    "entities": entities,
                    "relationships": relationships,
                    "query_info": {
                        "keywords_used": keywords,
                        "entity_types_filter": entity_types,
                        "max_depth": max_depth
                    }
                }
                
        except Exception as e:
            logger.error(f"Entity and relationship query failed: {e}")
            return {"entities": [], "relationships": [], "error": str(e)}
    
    async def get_project_entities(self, project: str, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Get entities associated with a specific project
        
        Args:
            project: Project name
            limit: Maximum number of entities
            
        Returns:
            List of project entities
        """
        if not self.driver:
            return []
            
        try:
            async with self.driver.session() as session:
                query = """
                    MATCH (p:Project {name: $project})-[:HAS_ENTITY]->(e)
                    RETURN e, labels(e) as types
                    UNION
                    MATCH (d:Document)-[:BELONGS_TO]->(p:Project {name: $project})
                    MATCH (d)-[:MENTIONS]->(e:Entity)
                    RETURN e, labels(e) as types
                    LIMIT $limit
                """
                
                result = await session.run(query, {"project": project, "limit": limit})
                entities = []
                
                async for record in result:
                    node = record["e"]
                    entities.append({
                        "id": node.element_id,
                        "name": node.get("name", "Unknown"),
                        "type": record["types"][0] if record["types"] else "Entity",
                        "properties": dict(node)
                    })
                
                return entities
                
        except Exception as e:
            logger.error(f"Failed to get project entities: {e}")
            return []
    
    async def find_entity_connections(
        self,
        entity_name: str,
        connection_types: Optional[List[str]] = None,
        max_depth: int = 2,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Find connections for a specific entity
        
        Args:
            entity_name: Name of the entity to explore
            connection_types: Types of relationships to follow
            max_depth: Maximum traversal depth
            limit: Maximum number of connections
            
        Returns:
            Dictionary with entity connections
        """
        if not self.driver:
            return {"connections": []}
            
        try:
            async with self.driver.session() as session:
                # Build relationship type filter
                rel_filter = ""
                if connection_types:
                    rel_types = "|".join(connection_types)
                    rel_filter = f":{rel_types}"
                
                query = f"""
                    MATCH (start {{name: $entity_name}})
                    MATCH (start)-[r{rel_filter}*1..{max_depth}]-(connected)
                    WHERE connected <> start
                    RETURN DISTINCT connected, 
                           labels(connected) as types,
                           length([rel in r | rel]) as distance
                    ORDER BY distance, connected.name
                    LIMIT $limit
                """
                
                result = await session.run(query, {
                    "entity_name": entity_name,
                    "limit": limit
                })
                
                connections = []
                async for record in result:
                    node = record["connected"]
                    connections.append({
                        "entity": {
                            "id": node.element_id,
                            "name": node.get("name", "Unknown"),
                            "type": record["types"][0] if record["types"] else "Unknown",
                            "properties": dict(node)
                        },
                        "distance": record["distance"]
                    })
                
                return {
                    "entity_name": entity_name,
                    "connections": connections,
                    "total_found": len(connections)
                }
                
        except Exception as e:
            logger.error(f"Failed to find entity connections: {e}")
            return {"connections": [], "error": str(e)}
    
    async def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the knowledge graph
        
        Returns:
            Graph statistics dictionary
        """
        if not self.driver:
            return {"healthy": False}
            
        try:
            async with self.driver.session() as session:
                # Get node count
                node_result = await session.run("MATCH (n) RETURN count(n) as node_count")
                node_record = await node_result.single()
                node_count = node_record["node_count"] if node_record else 0
                
                # Get relationship count
                rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_record = await rel_result.single()
                rel_count = rel_record["rel_count"] if rel_record else 0
                
                # Get node types (labels)
                label_result = await session.run("""
                    CALL db.labels() YIELD label
                    RETURN collect(label) as labels
                """)
                label_record = await label_result.single()
                node_types = label_record["labels"] if label_record else []
                
                # Calculate graph density (simplified)
                max_possible_edges = node_count * (node_count - 1) if node_count > 1 else 1
                density = rel_count / max_possible_edges if max_possible_edges > 0 else 0
                
                # Estimate traversal speed (simplified)
                traversal_speed = min(1000, node_count * 10) if node_count > 0 else 0
                
                return {
                    "healthy": True,
                    "total_nodes": node_count,
                    "total_relationships": rel_count,
                    "node_types": node_types,
                    "density": density,
                    "traversal_speed": traversal_speed,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get graph stats: {e}")
            return {"healthy": False, "error": str(e)}
    
    async def search_entities_by_type(
        self,
        entity_type: str,
        search_term: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for entities by type and optional search term
        
        Args:
            entity_type: Type/label of entities to search
            search_term: Optional search term for entity names
            limit: Maximum number of results
            
        Returns:
            List of matching entities
        """
        if not self.driver:
            return []
            
        try:
            async with self.driver.session() as session:
                if search_term:
                    query = f"""
                        MATCH (n:{entity_type})
                        WHERE toLower(n.name) CONTAINS toLower($search_term)
                        RETURN n, labels(n) as types
                        ORDER BY n.name
                        LIMIT $limit
                    """
                    params = {"search_term": search_term, "limit": limit}
                else:
                    query = f"""
                        MATCH (n:{entity_type})
                        RETURN n, labels(n) as types
                        ORDER BY n.name
                        LIMIT $limit
                    """
                    params = {"limit": limit}
                
                result = await session.run(query, params)
                entities = []
                
                async for record in result:
                    node = record["n"]
                    entities.append({
                        "id": node.element_id,
                        "name": node.get("name", "Unknown"),
                        "type": entity_type,
                        "properties": dict(node)
                    })
                
                return entities
                
        except Exception as e:
            logger.error(f"Entity type search failed: {e}")
            return []
    
    async def get_entity_neighborhood(
        self,
        entity_id: str,
        radius: int = 1,
        limit: int = 15
    ) -> Dict[str, Any]:
        """
        Get the neighborhood around a specific entity
        
        Args:
            entity_id: Element ID of the entity
            radius: How many hops to explore
            limit: Maximum number of neighbors
            
        Returns:
            Dictionary with neighborhood information
        """
        if not self.driver:
            return {"neighbors": []}
            
        try:
            async with self.driver.session() as session:
                query = f"""
                    MATCH (center)
                    WHERE elementId(center) = $entity_id
                    MATCH (center)-[r*1..{radius}]-(neighbor)
                    WHERE neighbor <> center
                    RETURN DISTINCT neighbor, 
                           labels(neighbor) as types,
                           length([rel in r | rel]) as distance
                    ORDER BY distance, neighbor.name
                    LIMIT $limit
                """
                
                result = await session.run(query, {
                    "entity_id": entity_id,
                    "limit": limit
                })
                
                neighbors = []
                async for record in result:
                    node = record["neighbor"]
                    neighbors.append({
                        "id": node.element_id,
                        "name": node.get("name", "Unknown"),
                        "type": record["types"][0] if record["types"] else "Unknown",
                        "distance": record["distance"],
                        "properties": dict(node)
                    })
                
                return {
                    "entity_id": entity_id,
                    "neighbors": neighbors,
                    "radius": radius,
                    "total_found": len(neighbors)
                }
                
        except Exception as e:
            logger.error(f"Failed to get entity neighborhood: {e}")
            return {"neighbors": [], "error": str(e)}
    
    async def health_check(self) -> bool:
        """
        Check if Neo4j is healthy and responding
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.driver:
            return False
            
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as health")
                record = await result.single()
                return record["health"] == 1
                
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False