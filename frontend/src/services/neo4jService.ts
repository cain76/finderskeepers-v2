import neo4j, { Driver, Session, Result } from 'neo4j-driver';

export interface Neo4jNode {
  id: string;
  labels: string[];
  properties: Record<string, any>;
}

export interface Neo4jRelationship {
  id: string;
  type: string;
  startNode: string;
  endNode: string;
  properties: Record<string, any>;
}

export interface GraphData {
  nodes: Neo4jNode[];
  relationships: Neo4jRelationship[];
}

export interface DocumentNode {
  id: string;
  title: string;
  content: string;
  project: string;
  createdAt: string;
  docType: string;
  embedding?: number[];
}

export interface SessionNode {
  id: string;
  sessionId: string;
  agentType: string;
  project: string;
  startTime: string;
  endTime?: string;
  context: Record<string, any>;
}

class Neo4jService {
  private driver: Driver | null = null;
  private readonly uri: string;
  private readonly username: string;
  private readonly password: string;

  constructor() {
    // Use environment variables or defaults for Neo4j connection
    this.uri = import.meta.env.VITE_NEO4J_URI || 'bolt://localhost:7687';
    this.username = import.meta.env.VITE_NEO4J_USER || 'neo4j';
    this.password = import.meta.env.VITE_NEO4J_PASSWORD || 'changeme_neo4j_password';
  }

  async connect(): Promise<void> {
    try {
      this.driver = neo4j.driver(this.uri, neo4j.auth.basic(this.username, this.password));
      
      // Test connection
      await this.driver.verifyConnectivity();
      console.log('Connected to Neo4j database');
    } catch (error) {
      console.error('Failed to connect to Neo4j:', error);
      throw new Error('Neo4j connection failed');
    }
  }

  async disconnect(): Promise<void> {
    if (this.driver) {
      await this.driver.close();
      this.driver = null;
      console.log('Disconnected from Neo4j database');
    }
  }

  private async runQuery<T = any>(cypher: string, parameters: Record<string, any> = {}): Promise<T[]> {
    if (!this.driver) {
      await this.connect();
    }

    const session: Session = this.driver!.session();
    
    try {
      const result: Result = await session.run(cypher, parameters);
      return result.records.map(record => record.toObject() as T);
    } catch (error) {
      console.error('Neo4j query error:', error);
      throw error;
    } finally {
      await session.close();
    }
  }

  // Get all documents in the knowledge graph
  async getAllDocuments(): Promise<DocumentNode[]> {
    const cypher = `
      MATCH (d:Document)
      RETURN d.id as id, d.title as title, d.content as content, 
             d.project as project, d.created_at as createdAt, d.doc_type as docType
      ORDER BY d.created_at DESC
    `;
    
    return await this.runQuery<DocumentNode>(cypher);
  }

  // Get all agent sessions
  async getAllSessions(): Promise<SessionNode[]> {
    const cypher = `
      MATCH (s:Session)
      RETURN s.session_id as sessionId, s.agent_type as agentType, 
             s.project as project, s.start_time as startTime, 
             s.end_time as endTime, s.context as context
      ORDER BY s.start_time DESC
    `;
    
    return await this.runQuery<SessionNode>(cypher);
  }

  // Get documents related to a specific project
  async getDocumentsByProject(project: string): Promise<DocumentNode[]> {
    const cypher = `
      MATCH (d:Document)
      WHERE d.project = $project
      RETURN d.id as id, d.title as title, d.content as content, 
             d.project as project, d.created_at as createdAt, d.doc_type as docType
      ORDER BY d.created_at DESC
    `;
    
    return await this.runQuery<DocumentNode>(cypher, { project });
  }

  // Get relationship graph data for visualization
  async getGraphData(limit: number = 100): Promise<GraphData> {
    const cypher = `
      MATCH (n)-[r]->(m)
      RETURN n, r, m
      LIMIT $limit
    `;
    
    const results = await this.runQuery(cypher, { limit });
    
    const nodes: Neo4jNode[] = [];
    const relationships: Neo4jRelationship[] = [];
    const nodeIds = new Set<string>();

    results.forEach(record => {
      const startNode = record.n;
      const relationship = record.r;
      const endNode = record.m;

      // Add nodes if not already added
      if (!nodeIds.has(startNode.identity.toString())) {
        nodes.push({
          id: startNode.identity.toString(),
          labels: startNode.labels,
          properties: startNode.properties
        });
        nodeIds.add(startNode.identity.toString());
      }

      if (!nodeIds.has(endNode.identity.toString())) {
        nodes.push({
          id: endNode.identity.toString(),
          labels: endNode.labels,
          properties: endNode.properties
        });
        nodeIds.add(endNode.identity.toString());
      }

      // Add relationship
      relationships.push({
        id: relationship.identity.toString(),
        type: relationship.type,
        startNode: startNode.identity.toString(),
        endNode: endNode.identity.toString(),
        properties: relationship.properties
      });
    });

    return { nodes, relationships };
  }

  // Search documents by content
  async searchDocuments(query: string, limit: number = 10): Promise<DocumentNode[]> {
    const cypher = `
      MATCH (d:Document)
      WHERE d.content CONTAINS $query OR d.title CONTAINS $query
      RETURN d.id as id, d.title as title, d.content as content, 
             d.project as project, d.created_at as createdAt, d.doc_type as docType
      ORDER BY d.created_at DESC
      LIMIT $limit
    `;
    
    return await this.runQuery<DocumentNode>(cypher, { query, limit });
  }

  // Get document relationships
  async getDocumentRelationships(documentId: string): Promise<GraphData> {
    const cypher = `
      MATCH (d:Document {id: $documentId})-[r]-(related)
      RETURN d, r, related
    `;
    
    const results = await this.runQuery(cypher, { documentId });
    
    const nodes: Neo4jNode[] = [];
    const relationships: Neo4jRelationship[] = [];
    const nodeIds = new Set<string>();

    results.forEach(record => {
      const docNode = record.d;
      const relationship = record.r;
      const relatedNode = record.related;

      // Add document node
      if (!nodeIds.has(docNode.identity.toString())) {
        nodes.push({
          id: docNode.identity.toString(),
          labels: docNode.labels,
          properties: docNode.properties
        });
        nodeIds.add(docNode.identity.toString());
      }

      // Add related node
      if (!nodeIds.has(relatedNode.identity.toString())) {
        nodes.push({
          id: relatedNode.identity.toString(),
          labels: relatedNode.labels,
          properties: relatedNode.properties
        });
        nodeIds.add(relatedNode.identity.toString());
      }

      // Add relationship
      relationships.push({
        id: relationship.identity.toString(),
        type: relationship.type,
        startNode: docNode.identity.toString(),
        endNode: relatedNode.identity.toString(),
        properties: relationship.properties
      });
    });

    return { nodes, relationships };
  }

  // Get project statistics
  async getProjectStats(): Promise<{
    totalDocuments: number;
    totalSessions: number;
    projectCounts: Record<string, number>;
  }> {
    const documentCountQuery = `
      MATCH (d:Document)
      RETURN count(d) as totalDocuments
    `;
    
    const sessionCountQuery = `
      MATCH (s:Session)
      RETURN count(s) as totalSessions
    `;
    
    const projectCountQuery = `
      MATCH (d:Document)
      RETURN d.project as project, count(d) as count
      ORDER BY count DESC
    `;

    const [docResult, sessionResult, projectResult] = await Promise.all([
      this.runQuery(documentCountQuery),
      this.runQuery(sessionCountQuery),
      this.runQuery(projectCountQuery)
    ]);

    const projectCounts: Record<string, number> = {};
    projectResult.forEach(record => {
      if (record.project) {
        projectCounts[record.project] = record.count;
      }
    });

    return {
      totalDocuments: docResult[0]?.totalDocuments || 0,
      totalSessions: sessionResult[0]?.totalSessions || 0,
      projectCounts
    };
  }
}

// Export a singleton instance
export const neo4jService = new Neo4jService();
export default neo4jService;