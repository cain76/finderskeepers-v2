// FindersKeepers v2 - Vector Search Page

import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  TextField,
  Button,
  LinearProgress,
  List,
  ListItem,
  Chip,
  IconButton,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider,
  FormControlLabel,
  Switch,
  Alert,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  ExpandMore as ExpandMoreIcon,
  Description as DocumentIcon,
  Lightbulb as VectorIcon,
  TrendingUp as SimilarityIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { qdrantService } from '../services/qdrantService';
import { mcpKnowledgeService } from '../services/mcpKnowledgeService';
import type { QdrantSearchResult, QdrantCollection, QdrantPoint } from '../services/qdrantService';
import type { McpSearchResult, McpSearchResponse } from '../services/mcpKnowledgeService';

interface SearchFilters {
  minSimilarity: number;
  maxResults: number;
  selectedCollection: string;
  documentTypes: string[];
  projects: string[];
  dateRange: {
    start: string;
    end: string;
  };
}

export default function VectorSearch() {
  const [query, setQuery] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState<QdrantSearchResult[]>([]);
  const [mcpResults, setMcpResults] = React.useState<McpSearchResult[]>([]);
  const [searchTime, setSearchTime] = React.useState<number>(0);
  const [collections, setCollections] = React.useState<QdrantCollection[]>([]);
  const [points, setPoints] = React.useState<QdrantPoint[]>([]);
  const [useMcpSearch, setUseMcpSearch] = React.useState(true); // Use MCP by default
  const [filters, setFilters] = React.useState<SearchFilters>({
    minSimilarity: 0.7,
    maxResults: 20,
    selectedCollection: 'finderskeepers_documents',
    documentTypes: [],
    projects: [],
    dateRange: {
      start: '',
      end: '',
    },
  });
  const [showAdvanced, setShowAdvanced] = React.useState(false);
  const [browseMode, setBrowseMode] = React.useState(false);
  const [collectionStats, setCollectionStats] = React.useState<{
    totalCollections: number;
    totalPoints: number;
    collections: Array<{
      name: string;
      pointsCount: number;
      vectorsCount: number;
    }>;
  }>({
    totalCollections: 0,
    totalPoints: 0,
    collections: []
  });

  // Load collections and statistics on mount
  React.useEffect(() => {
    const loadCollections = async () => {
      try {
        if (useMcpSearch) {
          // Use MCP Knowledge service
          const [collectionsData, statsData] = await Promise.all([
            mcpKnowledgeService.getCollections(),
            mcpKnowledgeService.getCollectionStats()
          ]);
          
          setCollections(collectionsData);
          setCollectionStats(statsData);
          
          // Set first collection as default if available
          if (collectionsData.length > 0) {
            setFilters(prev => ({ ...prev, selectedCollection: collectionsData[0].name }));
          }
        } else {
          // Use direct Qdrant service (fallback)
          const [collectionsData, statsData] = await Promise.all([
            qdrantService.getCollections(),
            qdrantService.getCollectionStats()
          ]);
          
          setCollections(collectionsData);
          setCollectionStats(statsData);
          
          // Set first collection as default if available
          if (collectionsData.length > 0) {
            setFilters(prev => ({ ...prev, selectedCollection: collectionsData[0].name }));
          }
        }
      } catch (error) {
        console.error('Failed to load collections:', error);
      }
    };
    
    loadCollections();
  }, [useMcpSearch]);

  // Browse collection points
  const browseCollection = async (collectionName: string) => {
    try {
      setLoading(true);
      const startTime = Date.now();
      
      const collectionPoints = await qdrantService.getPoints(collectionName, filters.maxResults);
      
      const endTime = Date.now();
      setSearchTime(endTime - startTime);
      
      setPoints(collectionPoints);
      setBrowseMode(true);
      setResults([]);
    } catch (error) {
      console.error('Failed to browse collection:', error);
      setPoints([]);
    } finally {
      setLoading(false);
    }
  };

  // Perform vector search
  const performSearch = async () => {
    if (!query.trim()) return;

    try {
      setLoading(true);
      setBrowseMode(false);
      setPoints([]);
      setResults([]);
      setMcpResults([]);
      const startTime = Date.now();

      if (useMcpSearch) {
        // Use MCP Knowledge service for real vector search
        console.log('Performing MCP Knowledge search:', query);
        
        const mcpResponse = await mcpKnowledgeService.searchDocuments({
          query: query.trim(),
          limit: filters.maxResults,
          min_score: filters.minSimilarity,
          project: filters.selectedCollection === 'all' ? undefined : filters.selectedCollection
        });
        
        console.log('MCP search response:', mcpResponse);
        setMcpResults(mcpResponse.results);
        
      } else {
        // Fallback to direct Qdrant (will show placeholder message)
        console.warn('Text search requires backend API integration');
        await browseCollection(filters.selectedCollection);
      }
      
      const endTime = Date.now();
      setSearchTime(endTime - startTime);

    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
      setMcpResults([]);
    } finally {
      setLoading(false);
    }
  };

  // Handle search submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch();
  };

  // Clear search
  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setMcpResults([]);
    setSearchTime(0);
    setBrowseMode(false);
    setPoints([]);
  };

  // Get similarity color based on score
  const getSimilarityColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  // Format similarity score
  const formatSimilarity = (score: number) => {
    return (score * 100).toFixed(1) + '%';
  };

  // Highlight search terms in text
  const highlightText = (text: string, searchQuery: string) => {
    if (!searchQuery.trim()) return text;
    
    const regex = new RegExp(`(${searchQuery.trim().split(' ').join('|')})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => {
      if (regex.test(part)) {
        return <mark key={index} style={{ backgroundColor: '#ffeb3b', padding: '0 2px' }}>{part}</mark>;
      }
      return part;
    });
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Vector Search
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            icon={<VectorIcon />}
            label={`${collectionStats.totalCollections} collections`}
            variant="outlined"
          />
          <Chip
            label={`${collectionStats.totalPoints} total points`}
            variant="outlined"
          />
          <Chip
            label={browseMode ? `${points.length} points` : useMcpSearch ? `${mcpResults.length} MCP results` : `${results.length} results`}
            variant="outlined"
          />
          <FormControlLabel
            control={
              <Switch
                checked={useMcpSearch}
                onChange={(e) => setUseMcpSearch(e.target.checked)}
                color="primary"
              />
            }
            label="Use MCP Search"
          />
        </Box>
      </Box>

      {/* Search Form */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Grid container spacing={2} alignItems="center">
              <Grid size={{ xs: 12, md: 4 }}>
                <FormControl fullWidth variant="outlined">
                  <InputLabel>Collection</InputLabel>
                  <Select
                    value={filters.selectedCollection}
                    onChange={(e) => setFilters(prev => ({ ...prev, selectedCollection: e.target.value }))}
                    label="Collection"
                    disabled={loading}
                  >
                    {collections.map((collection) => (
                      <MenuItem key={collection.name} value={collection.name}>
                        {collection.name} ({collection.pointsCount} points)
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <TextField
                  fullWidth
                  variant="outlined"
                  placeholder="Search documents by meaning..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={loading}
                  InputProps={{
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'action.active' }} />,
                    endAdornment: query && (
                      <IconButton onClick={clearSearch} size="small">
                        <ClearIcon />
                      </IconButton>
                    ),
                  }}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 2 }}>
                <Button
                  fullWidth
                  variant="contained"
                  type="submit"
                  disabled={loading || !query.trim()}
                  sx={{ height: 56 }}
                >
                  Search
                </Button>
              </Grid>
              <Grid size={{ xs: 12, md: 2 }}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={() => browseCollection(filters.selectedCollection)}
                  disabled={loading}
                  sx={{ height: 56 }}
                >
                  Browse
                </Button>
              </Grid>
            </Grid>
          </form>

          {/* Collection Stats */}
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" color="textSecondary">
              {browseMode ? 'Browsing collection points' : 'Vector search in selected collection'}
            </Typography>
            {collections.find(c => c.name === filters.selectedCollection) && (
              <Typography variant="body2" color="textSecondary">
                Selected: {filters.selectedCollection} ({collections.find(c => c.name === filters.selectedCollection)?.pointsCount || 0} points)
              </Typography>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Advanced Filters */}
      {showAdvanced && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Advanced Search Filters
            </Typography>
            
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Minimum Similarity Score
                </Typography>
                <Slider
                  value={filters.minSimilarity}
                  onChange={(_, value) => setFilters(prev => ({ ...prev, minSimilarity: value as number }))}
                  min={0}
                  max={1}
                  step={0.05}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => formatSimilarity(value)}
                  sx={{ mt: 2 }}
                />
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Maximum Results
                </Typography>
                <Slider
                  value={filters.maxResults}
                  onChange={(_, value) => setFilters(prev => ({ ...prev, maxResults: value as number }))}
                  min={5}
                  max={100}
                  step={5}
                  valueLabelDisplay="auto"
                  sx={{ mt: 2 }}
                />
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Start Date"
                  type="date"
                  value={filters.dateRange.start}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    dateRange: { ...prev.dateRange, start: e.target.value } 
                  }))}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="End Date"
                  type="date"
                  value={filters.dateRange.end}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    dateRange: { ...prev.dateRange, end: e.target.value } 
                  }))}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Loading */}
      {loading && (
        <Box sx={{ width: '100%', mb: 2 }}>
          <LinearProgress />
          <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
            Searching vector database...
          </Typography>
        </Box>
      )}

      {/* Search Results */}
      {results.length > 0 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Search Results ({results.length})
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Found in {searchTime}ms
              </Typography>
            </Box>

            <List>
              {results.map((result, index) => (
                <React.Fragment key={result.id || index}>
                  <ListItem sx={{ flexDirection: 'column', alignItems: 'stretch', py: 2 }}>
                    {/* Document Header */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <DocumentIcon sx={{ mr: 1, color: 'primary.main' }} />
                        <Typography variant="subtitle1" fontWeight="medium">
                          {result.payload?.title || result.payload?.source_file || `Document ${result.id}`}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          icon={<SimilarityIcon />}
                          label={formatSimilarity(result.score)}
                          color={getSimilarityColor(result.score) as any}
                          size="small"
                        />
                        {result.payload?.project && (
                          <Chip
                            label={result.payload.project}
                            variant="outlined"
                            size="small"
                          />
                        )}
                      </Box>
                    </Box>

                    {/* Document Content */}
                    <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                      <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                        {highlightText(result.payload?.content || 'No content available', query)}
                      </Typography>
                    </Paper>

                    {/* Document Metadata */}
                    {result.payload && Object.keys(result.payload).length > 0 && (
                      <Accordion sx={{ mt: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography variant="body2" color="textSecondary">
                            Document Metadata
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Grid container spacing={1}>
                            {Object.entries(result.payload).map(([key, value]) => (
                              <Grid size={{ xs: 12, sm: 6 }} key={key}>
                                <Typography variant="caption" color="textSecondary">
                                  {key.replace(/_/g, ' ').toUpperCase()}
                                </Typography>
                                <Typography variant="body2">
                                  {String(value)}
                                </Typography>
                              </Grid>
                            ))}
                          </Grid>
                        </AccordionDetails>
                      </Accordion>
                    )}
                  </ListItem>
                  {index < results.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* MCP Search Results */}
      {mcpResults.length > 0 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                MCP Knowledge Search Results ({mcpResults.length})
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Found in {searchTime}ms
              </Typography>
            </Box>

            <List>
              {mcpResults.map((result, index) => (
                <React.Fragment key={result.document_id || index}>
                  <ListItem sx={{ flexDirection: 'column', alignItems: 'stretch', py: 2 }}>
                    {/* Document Header */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <DocumentIcon sx={{ mr: 1, color: 'primary.main' }} />
                        <Typography variant="subtitle1" fontWeight="medium">
                          {result.metadata?.title || result.metadata?.source_file || `Document ${result.document_id}`}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          icon={<SimilarityIcon />}
                          label={formatSimilarity(result.score)}
                          color={getSimilarityColor(result.score) as any}
                          size="small"
                        />
                        {result.metadata?.project && (
                          <Chip
                            label={result.metadata.project}
                            variant="outlined"
                            size="small"
                          />
                        )}
                        <Chip
                          label="MCP"
                          color="secondary"
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    </Box>

                    {/* Document Content */}
                    <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                      <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                        {highlightText(result.content || 'No content available', query)}
                      </Typography>
                    </Paper>

                    {/* Document Metadata */}
                    {result.metadata && Object.keys(result.metadata).length > 0 && (
                      <Accordion sx={{ mt: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography variant="body2" color="textSecondary">
                            Document Metadata
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Grid container spacing={1}>
                            {Object.entries(result.metadata).map(([key, value]) => (
                              <Grid size={{ xs: 12, sm: 6 }} key={key}>
                                <Typography variant="caption" color="textSecondary">
                                  {key.replace(/_/g, ' ').toUpperCase()}
                                </Typography>
                                <Typography variant="body2">
                                  {String(value)}
                                </Typography>
                              </Grid>
                            ))}
                          </Grid>
                        </AccordionDetails>
                      </Accordion>
                    )}
                  </ListItem>
                  {index < mcpResults.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Browse Points */}
      {browseMode && points.length > 0 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Collection Points ({points.length})
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Loaded in {searchTime}ms
              </Typography>
            </Box>

            <List>
              {points.map((point, index) => (
                <React.Fragment key={point.id || index}>
                  <ListItem sx={{ flexDirection: 'column', alignItems: 'stretch', py: 2 }}>
                    {/* Point Header */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <VectorIcon sx={{ mr: 1, color: 'primary.main' }} />
                        <Typography variant="subtitle1" fontWeight="medium">
                          {point.payload?.title || point.payload?.source_file || `Point ${point.id}`}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={`ID: ${point.id}`}
                          variant="outlined"
                          size="small"
                        />
                        {point.payload?.project && (
                          <Chip
                            label={point.payload.project}
                            variant="outlined"
                            size="small"
                          />
                        )}
                      </Box>
                    </Box>

                    {/* Point Content */}
                    <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                      <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                        {point.payload?.content || 'No content available'}
                      </Typography>
                    </Paper>

                    {/* Point Metadata */}
                    {point.payload && Object.keys(point.payload).length > 0 && (
                      <Accordion sx={{ mt: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography variant="body2" color="textSecondary">
                            Point Metadata
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Grid container spacing={1}>
                            {Object.entries(point.payload).map(([key, value]) => (
                              <Grid size={{ xs: 12, sm: 6 }} key={key}>
                                <Typography variant="caption" color="textSecondary">
                                  {key.replace(/_/g, ' ').toUpperCase()}
                                </Typography>
                                <Typography variant="body2">
                                  {String(value)}
                                </Typography>
                              </Grid>
                            ))}
                          </Grid>
                        </AccordionDetails>
                      </Accordion>
                    )}
                  </ListItem>
                  {index < points.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* No Results */}
      {!loading && query && results.length === 0 && mcpResults.length === 0 && !browseMode && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No documents found matching your search query. Try:
          <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
            <li>Using different keywords or phrases</li>
            <li>Lowering the similarity threshold in advanced filters</li>
            <li>Enabling semantic search for AI-powered matching</li>
            <li>Checking if documents are properly indexed</li>
          </ul>
        </Alert>
      )}

      {/* Empty State */}
      {!loading && !query && results.length === 0 && mcpResults.length === 0 && !browseMode && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <VectorIcon sx={{ fontSize: 64, color: 'grey.300', mb: 2 }} />
            <Typography variant="h6" color="textSecondary" gutterBottom>
              AI-Powered Document Search
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 3, maxWidth: 500, mx: 'auto' }}>
              Search your knowledge base using natural language. Our vector search understands 
              context and meaning, not just keywords. Try searching for concepts, questions, 
              or descriptions.
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="outlined"
                onClick={() => {
                  setQuery('How to configure Docker');
                  // Trigger search automatically
                  setTimeout(() => performSearch(), 100);
                }}
              >
                "How to configure Docker"
              </Button>
              <Button
                variant="outlined"
                onClick={() => {
                  setQuery('API authentication methods');
                  // Trigger search automatically
                  setTimeout(() => performSearch(), 100);
                }}
              >
                "API authentication methods"
              </Button>
              <Button
                variant="outlined"
                onClick={() => {
                  setQuery('troubleshooting guide');
                  // Trigger search automatically
                  setTimeout(() => performSearch(), 100);
                }}
              >
                "troubleshooting guide"
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}