// FindersKeepers v2 - Documents Management Page

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  IconButton,
  Tooltip,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Pagination,
  Alert,
} from '@mui/material';
import {
  Description as DocumentIcon,
  Upload as UploadIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  CloudUpload as CloudUploadIcon,
  TextSnippet as TextIcon,
  Image as ImageIcon,
  PictureAsPdf as PdfIcon,
  Code as CodeIcon,
  DataObject as JsonIcon,
} from '@mui/icons-material';
import { apiService } from '@/services/api';
import type { Document } from '@/types';

interface DocumentFilter {
  format?: string;
  project?: string;
  dateRange?: string;
  tags?: string[];
}

export default function Documents() {
  const [documents, setDocuments] = React.useState<Document[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [filter, setFilter] = React.useState<DocumentFilter>({});
  const [uploadDialogOpen, setUploadDialogOpen] = React.useState(false);
  const [selectedFiles, setSelectedFiles] = React.useState<FileList | null>(null);
  const [page, setPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const [stats, setStats] = React.useState({
    total: 0,
    totalSize: 0,
    formats: {} as Record<string, number>,
    projects: {} as Record<string, number>,
  });

  React.useEffect(() => {
    loadDocuments();
  }, [page, filter, searchQuery]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      
      const response = await apiService.getDocuments({
        page,
        limit: 20,
        search: searchQuery || undefined,
        format: filter.format,
        project: filter.project,
        tags: filter.tags,
      });

      if (response.success && response.data) {
        setDocuments(response.data.documents || []);
        setTotalPages(response.data.total_pages || 1);
        setStats(response.data.stats || stats);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
      
      // Mock data for development
      const mockDocuments: Document[] = [
        {
          id: '1',
          title: 'FastAPI Setup Guide',
          content: 'Comprehensive guide for setting up FastAPI...',
          format: 'markdown',
          project: 'finderskeepers-v2',
          tags: ['guide', 'backend', 'python'],
          file_path: '/docs/fastapi-setup.md',
          file_size: 15420,
          created_at: '2025-07-08T10:00:00Z',
          updated_at: '2025-07-08T10:00:00Z',
          metadata: {
            author: 'claude',
            version: '1.0',
          },
        },
        {
          id: '2',
          title: 'React Component Architecture',
          content: 'Design patterns for React components...',
          format: 'markdown',
          project: 'finderskeepers-v2',
          tags: ['frontend', 'react', 'architecture'],
          file_path: '/docs/react-architecture.md',
          file_size: 23150,
          created_at: '2025-07-07T15:30:00Z',
          updated_at: '2025-07-08T09:15:00Z',
          metadata: {
            author: 'claude',
            version: '2.1',
          },
        },
        {
          id: '3',
          title: 'Database Schema Design',
          content: 'PostgreSQL and Neo4j schema documentation...',
          format: 'markdown',
          project: 'finderskeepers-v2',
          tags: ['database', 'schema', 'postgresql', 'neo4j'],
          file_path: '/docs/database-schema.md',
          file_size: 18900,
          created_at: '2025-07-06T11:20:00Z',
          updated_at: '2025-07-07T14:45:00Z',
          metadata: {
            author: 'claude',
            version: '1.5',
          },
        },
        {
          id: '4',
          title: 'API Configuration',
          content: '{\n  "api_version": "v1",\n  "endpoints": [...]\n}',
          format: 'json',
          project: 'finderskeepers-v2',
          tags: ['config', 'api'],
          file_path: '/config/api.json',
          file_size: 5670,
          created_at: '2025-07-05T16:10:00Z',
          updated_at: '2025-07-06T12:30:00Z',
          metadata: {
            type: 'configuration',
          },
        },
      ];

      setDocuments(mockDocuments);
      setStats({
        total: 4,
        totalSize: 63140,
        formats: { markdown: 3, json: 1 },
        projects: { 'finderskeepers-v2': 4 },
      });
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    loadDocuments();
  };

  const handleFileUpload = async () => {
    if (!selectedFiles) return;

    try {
      setLoading(true);
      
      for (const file of Array.from(selectedFiles)) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('project', 'finderskeepers-v2');
        
        await apiService.uploadDocument(formData);
      }
      
      setUploadDialogOpen(false);
      setSelectedFiles(null);
      loadDocuments();
    } catch (error) {
      console.error('Failed to upload documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    try {
      await apiService.deleteDocument(documentId);
      loadDocuments();
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  };

  const getFileIcon = (format: string) => {
    switch (format.toLowerCase()) {
      case 'pdf':
        return <PdfIcon color="error" />;
      case 'markdown':
      case 'md':
        return <TextIcon color="primary" />;
      case 'json':
        return <JsonIcon color="warning" />;
      case 'javascript':
      case 'typescript':
      case 'python':
        return <CodeIcon color="success" />;
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif':
        return <ImageIcon color="info" />;
      default:
        return <DocumentIcon color="action" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center' }}>
          <DocumentIcon sx={{ mr: 1 }} />
          Documents
        </Typography>
        <Button
          variant="contained"
          startIcon={<UploadIcon />}
          onClick={() => setUploadDialogOpen(true)}
        >
          Upload Documents
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Total Documents
              </Typography>
              <Typography variant="h4">{stats.total}</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Total Size
              </Typography>
              <Typography variant="h4">{formatFileSize(stats.totalSize)}</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Formats
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
                {Object.entries(stats.formats).map(([format, count]) => (
                  <Chip key={format} label={`${format} (${count})`} size="small" />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Projects
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
                {Object.entries(stats.projects).map(([project, count]) => (
                  <Chip key={project} label={`${project} (${count})`} size="small" color="primary" />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid size={{ xs: 12, md: 4 }}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                InputProps={{
                  endAdornment: (
                    <IconButton onClick={handleSearch}>
                      <SearchIcon />
                    </IconButton>
                  ),
                }}
              />
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Format</InputLabel>
                <Select
                  value={filter.format || ''}
                  label="Format"
                  onChange={(e) => setFilter({ ...filter, format: e.target.value || undefined })}
                >
                  <MenuItem value="">All Formats</MenuItem>
                  <MenuItem value="markdown">Markdown</MenuItem>
                  <MenuItem value="json">JSON</MenuItem>
                  <MenuItem value="pdf">PDF</MenuItem>
                  <MenuItem value="text">Text</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Project</InputLabel>
                <Select
                  value={filter.project || ''}
                  label="Project"
                  onChange={(e) => setFilter({ ...filter, project: e.target.value || undefined })}
                >
                  <MenuItem value="">All Projects</MenuItem>
                  <MenuItem value="finderskeepers-v2">FindersKeepers v2</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid size={{ xs: 12, md: 4 }}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<FilterIcon />}
                  onClick={loadDocuments}
                >
                  Apply Filters
                </Button>
                <Tooltip title="Refresh documents">
                  <IconButton onClick={loadDocuments}>
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Documents Table */}
      <Card>
        <CardContent>
          {loading && <LinearProgress sx={{ mb: 2 }} />}
          
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Document</TableCell>
                  <TableCell>Format</TableCell>
                  <TableCell>Project</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Modified</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {documents.map((doc) => (
                  <TableRow key={doc.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {getFileIcon(doc.format)}
                        <Box sx={{ ml: 2 }}>
                          <Typography variant="subtitle2">{doc.title}</Typography>
                          <Typography variant="caption" color="textSecondary">
                            {doc.file_path}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip label={doc.format} size="small" />
                    </TableCell>
                    <TableCell>
                      <Chip label={doc.project} size="small" color="primary" />
                    </TableCell>
                    <TableCell>{formatFileSize(doc.file_size)}</TableCell>
                    <TableCell>{formatDate(doc.updated_at)}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="View document">
                          <IconButton size="small">
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit document">
                          <IconButton size="small">
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete document">
                          <IconButton 
                            size="small" 
                            color="error"
                            onClick={() => handleDeleteDocument(doc.id)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {documents.length === 0 && !loading && (
            <Alert severity="info" sx={{ mt: 2 }}>
              No documents found. Upload some documents to get started.
            </Alert>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, newPage) => setPage(newPage)}
                color="primary"
              />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Upload Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Upload Documents</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <input
              type="file"
              multiple
              onChange={(e) => setSelectedFiles(e.target.files)}
              style={{ display: 'none' }}
              id="file-upload"
              accept=".md,.txt,.json,.pdf,.doc,.docx"
            />
            <label htmlFor="file-upload">
              <Button
                variant="outlined"
                component="span"
                startIcon={<CloudUploadIcon />}
                fullWidth
                sx={{ mb: 2 }}
              >
                Choose Files
              </Button>
            </label>
            
            {selectedFiles && (
              <List dense>
                {Array.from(selectedFiles).map((file, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      {getFileIcon(file.name.split('.').pop() || '')}
                    </ListItemIcon>
                    <ListItemText
                      primary={file.name}
                      secondary={formatFileSize(file.size)}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleFileUpload}
            variant="contained"
            disabled={!selectedFiles}
          >
            Upload
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}