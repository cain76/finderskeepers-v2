# Neo4j TypeScript Integration Guide
**Date**: 07-09-2025  
**Source**: https://dev.to/adamcowley/using-typescript-with-neo4j-478c  
**Author**: Adam Cowley  
**Project**: FindersKeepers v2 - Neo4j Knowledge Graph Integration  

## Overview

This guide covers using TypeScript with Neo4j JavaScript Driver v5.2.0+ for type-safe database operations. Essential for integrating Neo4j knowledge graph functionality into React TypeScript applications.

## Key Features

### TypeScript Support in Neo4j Driver 5.2.0+
- Interface definitions for query result types
- Type-checking for record keys and properties
- IntelliSense support for Node and Relationship properties
- Compile-time validation of Cypher query results

### Core Types

```typescript
import neo4j, { Node, Relationship, Integer } from 'neo4j-driver'

// Person node type definition
interface PersonProperties {
  tmdbId: string;
  name: string;
  born: number; // Year of birth
}
type Person = Node<Integer, PersonProperties>

// Movie node type definition
type Movie = Node<Integer, {
  tmdbId: string;
  title: string;
  rating: number;
}>

// Relationship type definition
type ActedIn = Relationship<Integer, {
  roles: string[];
}>

// Query result interface
interface PersonActedInMovie {
  p: Person;
  r: ActedIn;
  m: Movie;
}
```

### Type-Safe Query Execution

```typescript
async function findActors() {
  const driver = neo4j.driver(
    'neo4j://localhost:7687',
    neo4j.auth.basic('neo4j', 'password')
  )
  
  const session = driver.session()
  
  try {
    // Type-safe query execution
    const res = await session.executeRead(tx => tx.run<PersonActedInMovie>(`
      MATCH (p:Person)-[r:ACTED_IN]->(m:Movie {title: $title})
      RETURN p, r, m
    `, { title: 'Pulp Fiction' }))
    
    // TypeScript knows the structure of each record
    const people = res.records.map(row => row.get('p'))
    
    return people
  } finally {
    await session.close()
  }
}
```

## Benefits for FindersKeepers v2

### 1. Type Safety
- Compile-time validation of query results
- IntelliSense support for node/relationship properties
- Prevention of runtime errors from typos

### 2. Developer Experience
- Auto-completion for record keys (`p`, `r`, `m`)
- Property suggestions for nodes and relationships
- Type checking for property access

### 3. Error Prevention
```typescript
// This will cause a TypeScript error
const people = res.records.map(row => row.get('something'))
// Error: This record has no field with key 'something'

// This will also cause a TypeScript error
const names: string[] = people.map(person => person.properties.born)
// Error: Type 'number[]' is not assignable to type 'string[]'
```

## Implementation for FindersKeepers v2

### Required Package
```bash
npm install neo4j-driver
npm install @types/neo4j-driver # If needed
```

### Driver Configuration
```typescript
import neo4j from 'neo4j-driver'

const driver = neo4j.driver(
  'bolt://fk2_neo4j:7687',
  neo4j.auth.basic('neo4j', 'fk2025neo4j')
)
```

### Knowledge Graph Types
```typescript
// Agent session node
type AgentSession = Node<Integer, {
  sessionId: string;
  agentType: string;
  startTime: string;
  endTime?: string;
  project?: string;
}>

// Document node
type Document = Node<Integer, {
  title: string;
  content: string;
  project: string;
  docType: string;
  createdAt: string;
}>

// Knowledge relationship
type REFERENCES = Relationship<Integer, {
  relevance: number;
  context: string;
}>
```

### Query Interface Examples
```typescript
interface SessionDocumentQuery {
  session: AgentSession;
  doc: Document;
  relationship: REFERENCES;
}

interface KnowledgeGraphQuery {
  entities: Node<Integer, any>[];
  relationships: Relationship<Integer, any>[];
}
```

## Best Practices

1. **Always define interfaces for query results**
2. **Use specific property types instead of `any`**
3. **Handle Integer types properly (Neo4j uses 64-bit integers)**
4. **Close sessions in finally blocks**
5. **Use executeRead/executeWrite for transaction management**

## Resources

- [Neo4j JavaScript Driver Manual](https://neo4j.com/docs/javascript-manual/current/)
- [Building Neo4j Applications with TypeScript Course](https://graphacademy.neo4j.com/courses/app-typescript/)
- [Neo4j GraphAcademy](https://graphacademy.neo4j.com/)

## Next Steps for FindersKeepers v2

1. Install neo4j-driver package
2. Define TypeScript interfaces for knowledge graph entities
3. Implement type-safe query functions
4. Integrate with React components using these types
5. Add to frontend package.json dependencies