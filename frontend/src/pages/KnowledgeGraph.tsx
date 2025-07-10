// FindersKeepers v2 - Knowledge Graph Visualization Page

import React from 'react';
import {
  Box,
  Typography,
  Grid,
  TextField,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Tooltip,
  Paper,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  AccountTree as GraphIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  ReactFlowProvider,
} from '@xyflow/react';
import type { Node, Edge, NodeTypes } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { neo4jService } from '../services/neo4jService';
import type { Neo4jNode, Neo4jRelationship } from '../services/neo4jService';

interface KnowledgeGraphNode extends Node {
  data: {
    label: string;
    type: string;
    properties: Record<string, any>;
    size: number;
  };
}

interface KnowledgeGraphEdge extends Edge {
  data: {
    relationship: string;
    properties: Record<string, any>;
  };
}

// Custom Node Components
const DocumentNode = ({ data }: { data: any }) => (
  <Box
    sx={{
      p: 2,
      bgcolor: 'primary.light',
      color: 'primary.contrastText',
      borderRadius: 2,
      minWidth: 120,
      textAlign: 'center',
      border: '2px solid',
      borderColor: 'primary.main',
    }}
  >
    <Typography variant="body2" fontWeight="bold">
      {data.label}
    </Typography>
    <Typography variant="caption">
      Document
    </Typography>
  </Box>
);

const SessionNode = ({ data }: { data: any }) => (
  <Box
    sx={{
      p: 2,
      bgcolor: 'secondary.light',
      color: 'secondary.contrastText',
      borderRadius: 2,
      minWidth: 120,
      textAlign: 'center',
      border: '2px solid',
      borderColor: 'secondary.main',
    }}
  >
    <Typography variant="body2" fontWeight="bold">
      {data.label}
    </Typography>
    <Typography variant="caption">
      Session
    </Typography>
  </Box>
);

const ProjectNode = ({ data }: { data: any }) => (
  <Box
    sx={{
      p: 2,
      bgcolor: 'success.light',
      color: 'success.contrastText',
      borderRadius: 2,
      minWidth: 120,
      textAlign: 'center',
      border: '2px solid',
      borderColor: 'success.main',
    }}
  >
    <Typography variant="body2" fontWeight="bold">
      {data.label}
    </Typography>
    <Typography variant="caption">
      Project
    </Typography>
  </Box>
);

const nodeTypes: NodeTypes = {
  document: DocumentNode,
  session: SessionNode,
  project: ProjectNode,
};

export default function KnowledgeGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState<KnowledgeGraphNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<KnowledgeGraphEdge>([]);
  const [loading, setLoading] = React.useState(true);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedNodeType, setSelectedNodeType] = React.useState('all');
  const [selectedNode, setSelectedNode] = React.useState<Neo4jNode | null>(null);
  const [graphStats, setGraphStats] = React.useState({
    totalNodes: 0,
    totalEdges: 0,
    nodeTypes: {} as Record<string, number>,
  });

  React.useEffect(() => {
    loadGraphData();
  }, []);

  const loadGraphData = async () => {
    try {
      setLoading(true);
      
      // Load graph data from Neo4j
      const graphData = await neo4jService.getGraphData(100);
      
      if (graphData.nodes && graphData.relationships) {
        // Convert Neo4j data to React Flow format
        const flowNodes: KnowledgeGraphNode[] = graphData.nodes.map((node: Neo4jNode) => {
          const nodeType = node.labels.includes('Document') ? 'document' : 
                          node.labels.includes('Session') ? 'session' : 
                          node.labels.includes('Project') ? 'project' : 'entity';
          
          return {
            id: node.id,
            type: nodeType,
            position: {
              x: Math.random() * 600,
              y: Math.random() * 400,
            },
            data: {
              label: node.properties.title || node.properties.name || node.properties.session_id || `${nodeType}_${node.id}`,
              type: nodeType,
              properties: node.properties,
              size: 1, // We could calculate this based on relationship count
            },
          };
        });

        const flowEdges: KnowledgeGraphEdge[] = graphData.relationships.map((rel: Neo4jRelationship) => ({
          id: rel.id,
          source: rel.startNode,
          target: rel.endNode,
          type: 'default',
          animated: rel.type === 'CONTAINS' || rel.type === 'RELATES_TO',
          data: {
            relationship: rel.type,
            properties: rel.properties,
          },
          label: rel.type,
        }));

        setNodes(flowNodes);
        setEdges(flowEdges);

        // Calculate stats
        const nodeTypeCounts = flowNodes.reduce((acc, node) => {
          acc[node.data.type] = (acc[node.data.type] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);

        setGraphStats({
          totalNodes: flowNodes.length,
          totalEdges: flowEdges.length,
          nodeTypes: nodeTypeCounts,
        });
      }
    } catch (error) {
      console.error('Failed to load graph data:', error);
      
      // Mock data for development
      const mockNodes: KnowledgeGraphNode[] = [
        {
          id: '1',
          type: 'project',
          position: { x: 300, y: 200 },
          data: {
            label: 'FindersKeepers v2',
            type: 'project',
            properties: { description: 'AI Knowledge Hub' },
            size: 5,
          },
        },
        {
          id: '2',
          type: 'document',
          position: { x: 100, y: 100 },
          data: {
            label: 'FastAPI Setup',
            type: 'document',
            properties: { format: 'markdown' },
            size: 3,
          },
        },
        {
          id: '3',
          type: 'session',
          position: { x: 500, y: 100 },
          data: {
            label: 'GUI Development',
            type: 'session',
            properties: { agent: 'claude' },
            size: 2,
          },
        },
        {
          id: '4',
          type: 'document',
          position: { x: 200, y: 300 },
          data: {
            label: 'React Components',
            type: 'document',
            properties: { format: 'typescript' },
            size: 4,
          },
        },
      ];

      const mockEdges: KnowledgeGraphEdge[] = [
        {
          id: '1-2',
          source: '1',
          target: '2',
          type: 'default',
          data: { relationship: 'CONTAINS', properties: {} },
          label: 'CONTAINS',
        },
        {
          id: '1-3',
          source: '1',
          target: '3',
          type: 'default',
          data: { relationship: 'RELATES_TO', properties: {} },
          label: 'RELATES_TO',
        },
        {
          id: '3-4',
          source: '3',
          target: '4',
          type: 'default',
          data: { relationship: 'CREATED', properties: {} },
          label: 'CREATED',
        },
      ];

      setNodes(mockNodes);
      setEdges(mockEdges);
      setGraphStats({
        totalNodes: 4,
        totalEdges: 3,
        nodeTypes: { project: 1, document: 2, session: 1 },
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    try {
      setLoading(true);
      
      // Search documents using Neo4j service
      const searchResults = await neo4jService.searchDocuments(searchQuery, 20);
      
      if (searchResults.length > 0) {
        // Convert search results to graph format
        const searchNodes: KnowledgeGraphNode[] = searchResults.map((doc: any) => ({
          id: doc.id,
          type: 'document',
          position: {
            x: Math.random() * 600,
            y: Math.random() * 400,
          },
          data: {
            label: doc.title || `Document ${doc.id}`,
            type: 'document',
            properties: {
              title: doc.title,
              content: doc.content,
              project: doc.project,
              docType: doc.docType,
              createdAt: doc.createdAt,
            },
            size: 1,
          },
        }));

        // Get relationships for search results
        const searchEdges: KnowledgeGraphEdge[] = [];
        for (const doc of searchResults.slice(0, 5)) { // Limit to first 5 for performance
          try {
            const relationshipData = await neo4jService.getDocumentRelationships(doc.id);
            relationshipData.relationships.forEach((rel: Neo4jRelationship) => {
              searchEdges.push({
                id: rel.id,
                source: rel.startNode,
                target: rel.endNode,
                type: 'default',
                animated: rel.type === 'CONTAINS' || rel.type === 'RELATES_TO',
                data: {
                  relationship: rel.type,
                  properties: rel.properties,
                },
                label: rel.type,
              });
            });
          } catch (relError) {
            console.warn('Failed to load relationships for document:', doc.id, relError);
          }
        }

        setNodes(searchNodes);
        setEdges(searchEdges);
        
        // Update stats
        setGraphStats({
          totalNodes: searchNodes.length,
          totalEdges: searchEdges.length,
          nodeTypes: { document: searchNodes.length },
        });
      } else {
        // No search results found
        setNodes([]);
        setEdges([]);
        setGraphStats({
          totalNodes: 0,
          totalEdges: 0,
          nodeTypes: {},
        });
      }
    } catch (error) {
      console.error('Search failed:', error);
      
      // Fallback to full graph data on search error
      loadGraphData();
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = (_event: React.MouseEvent, node: Node) => {
    const graphNode: Neo4jNode = {
      id: node.id,
      labels: [node.data?.type || 'entity'],
      properties: {
        name: (node.data?.label as string) || node.id,
        title: (node.data?.label as string) || node.id,
        ...(node.data?.properties as Record<string, any>) || {},
      },
    };
    setSelectedNode(graphNode);
  };

  const getNodeTypeColor = (type: string) => {
    switch (type) {
      case 'document': return 'primary';
      case 'session': return 'secondary';
      case 'project': return 'success';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
          Loading knowledge graph...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header and Controls */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Grid container spacing={2} alignItems="center">
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="h5" component="h1" sx={{ display: 'flex', alignItems: 'center' }}>
              <GraphIcon sx={{ mr: 1 }} />
              Knowledge Graph
            </Typography>
          </Grid>
          
          <Grid size={{ xs: 12, md: 6 }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                size="small"
                placeholder="Search knowledge graph..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                sx={{ flexGrow: 1 }}
              />
              <Button
                variant="contained"
                startIcon={<SearchIcon />}
                onClick={handleSearch}
              >
                Search
              </Button>
            </Box>
          </Grid>

          <Grid size={{ xs: 12, md: 2 }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Node Type</InputLabel>
                <Select
                  value={selectedNodeType}
                  label="Node Type"
                  onChange={(e) => setSelectedNodeType(e.target.value)}
                >
                  <MenuItem value="all">All Types</MenuItem>
                  <MenuItem value="document">Documents</MenuItem>
                  <MenuItem value="session">Sessions</MenuItem>
                  <MenuItem value="project">Projects</MenuItem>
                </Select>
              </FormControl>
              
              <Tooltip title="Refresh graph">
                <IconButton onClick={loadGraphData}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Grid>
        </Grid>

        {/* Stats */}
        <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Chip
            label={`${graphStats.totalNodes} Nodes`}
            variant="outlined"
            size="small"
          />
          <Chip
            label={`${graphStats.totalEdges} Connections`}
            variant="outlined"
            size="small"
          />
          {Object.entries(graphStats.nodeTypes).map(([type, count]) => (
            <Chip
              key={type}
              label={`${count} ${type}s`}
              color={getNodeTypeColor(type)}
              size="small"
            />
          ))}
        </Box>
      </Box>

      {/* Graph and Details */}
      <Box sx={{ display: 'flex', flexGrow: 1 }}>
        {/* Graph Visualization */}
        <Box sx={{ flexGrow: 1, position: 'relative' }}>
          <ReactFlowProvider>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={handleNodeClick}
              nodeTypes={nodeTypes}
              connectionMode={ConnectionMode.Loose}
              fitView
              attributionPosition="bottom-left"
            >
              <Background />
              <Controls />
            </ReactFlow>
          </ReactFlowProvider>
        </Box>

        {/* Details Panel */}
        {selectedNode && (
          <Paper sx={{ width: 300, p: 2, m: 1 }}>
            <Typography variant="h6" gutterBottom>
              Node Details
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2">Name</Typography>
              <Typography variant="body2">
                {selectedNode.properties.name || selectedNode.properties.title || selectedNode.id}
              </Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2">Type</Typography>
              <Chip
                label={selectedNode.labels[0] || 'entity'}
                color={getNodeTypeColor(selectedNode.labels[0] || 'entity')}
                size="small"
              />
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2">Labels</Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {selectedNode.labels.map((label, index) => (
                  <Chip
                    key={index}
                    label={label}
                    size="small"
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>

            {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2">Properties</Typography>
                <List dense>
                  {Object.entries(selectedNode.properties).map(([key, value]) => (
                    <ListItem key={key} sx={{ px: 0 }}>
                      <ListItemText
                        primary={key}
                        secondary={String(value)}
                        secondaryTypographyProps={{
                          sx: { 
                            maxWidth: '200px', 
                            overflow: 'hidden', 
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}

            <Button
              fullWidth
              variant="outlined"
              startIcon={<ViewIcon />}
              onClick={() => {
                // Navigate to detailed view or explore relationships
                console.log('View details for:', selectedNode);
              }}
            >
              View Details
            </Button>
          </Paper>
        )}
      </Box>
    </Box>
  );
}