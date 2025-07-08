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
import { apiService } from '@/services/api';
import type { VectorSearchResult, SearchQuery } from '@/types';

interface SearchFilters {
  minSimilarity: number;
  maxResults: number;
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
  const [results, setResults] = React.useState<VectorSearchResult[]>([]);
  const [searchTime, setSearchTime] = React.useState<number>(0);
  const [filters, setFilters] = React.useState<SearchFilters>({
    minSimilarity: 0.5,
    maxResults: 20,
    documentTypes: [],
    projects: [],
    dateRange: {
      start: '',
      end: '',
    },
  });
  const [showAdvanced, setShowAdvanced] = React.useState(false);
  const [semanticSearch, setSemanticSearch] = React.useState(true);

  // Perform vector search
  const performSearch = async () => {
    if (!query.trim()) return;

    try {
      setLoading(true);
      const startTime = Date.now();

      const searchParams: SearchQuery = {
        query: query.trim(),
        limit: filters.maxResults,
        threshold: filters.minSimilarity,
        filters: {
          document_types: filters.documentTypes.length > 0 ? filters.documentTypes : undefined,
          projects: filters.projects.length > 0 ? filters.projects : undefined,
          date_range: filters.dateRange.start && filters.dateRange.end 
            ? { start: filters.dateRange.start, end: filters.dateRange.end }
            : undefined,
        },
      };

      let response;
      if (semanticSearch) {
        response = await apiService.semanticSearch(query.trim(), filters.maxResults);
      } else {
        response = await apiService.vectorSearch(searchParams);
      }

      const endTime = Date.now();
      setSearchTime(endTime - startTime);

      if (response.success && response.data) {
        setResults(response.data);
      } else {
        setResults([]);
      }
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
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
    setSearchTime(0);
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
        <Chip
          icon={<VectorIcon />}
          label={`${results.length} results`}
          variant="outlined"
        />
      </Box>

      {/* Search Form */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Grid container spacing={2} alignItems="center">
              <Grid size={{ xs: 12, md: 8 }}>
                <TextField
                  fullWidth
                  variant="outlined"
                  placeholder="Search documents by meaning, not just keywords..."
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
                  startIcon={<FilterIcon />}
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  sx={{ height: 56 }}
                >
                  Filters
                </Button>
              </Grid>
            </Grid>
          </form>

          {/* Search Type Toggle */}
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center' }}>
            <FormControlLabel
              control={
                <Switch
                  checked={semanticSearch}
                  onChange={(e) => setSemanticSearch(e.target.checked)}
                />
              }
              label="Semantic Search (AI-powered)"
            />
            <Typography variant="body2" color="textSecondary" sx={{ ml: 2 }}>
              {semanticSearch 
                ? 'Search by meaning using AI embeddings' 
                : 'Traditional vector similarity search'
              }
            </Typography>
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
                <React.Fragment key={result.document_id || index}>
                  <ListItem sx={{ flexDirection: 'column', alignItems: 'stretch', py: 2 }}>
                    {/* Document Header */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <DocumentIcon sx={{ mr: 1, color: 'primary.main' }} />
                        <Typography variant="subtitle1" fontWeight="medium">
                          {result.metadata?.source_file || 'Untitled Document'}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          icon={<SimilarityIcon />}
                          label={formatSimilarity(result.similarity_score)}
                          color={getSimilarityColor(result.similarity_score) as any}
                          size="small"
                        />
                        {result.metadata?.project && (
                          <Chip
                            label={result.metadata.project}
                            variant="outlined"
                            size="small"
                          />
                        )}
                      </Box>
                    </Box>

                    {/* Document Content */}
                    <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                      <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                        {highlightText(result.content, query)}
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
                  {index < results.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* No Results */}
      {!loading && query && results.length === 0 && (
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
      {!loading && !query && results.length === 0 && (
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
                onClick={() => setQuery('How to configure Docker')}
              >
                "How to configure Docker"
              </Button>
              <Button
                variant="outlined"
                onClick={() => setQuery('API authentication methods')}
              >
                "API authentication methods"
              </Button>
              <Button
                variant="outlined"
                onClick={() => setQuery('troubleshooting guide')}
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