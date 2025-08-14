import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import MenuIcon from '@mui/icons-material/Menu';
import { Link } from 'react-router-dom';

// Navigation component renders an AppBar and a side drawer containing
// links to each of the major pages in the application. The drawer
// state is managed locally using React state. When a list item is
// clicked, the drawer is closed and the user is navigated to the
// appropriate route.
function Navigation() {
  const [open, setOpen] = React.useState(false);

  const toggleDrawer = (state) => () => {
    setOpen(state);
  };

  // List of navigation items with the label and the corresponding path.
  const navItems = [
    { text: 'Home', path: '/' },
    { text: 'Monitoring', path: '/monitoring' },
    { text: 'Admin Panel', path: '/admin' },
    { text: 'Processing Stats', path: '/stats' },
    { text: 'Queue Maintenance', path: '/queue' },
    { text: 'Bulk Embedding', path: '/bulk' },
  ];

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            sx={{ mr: 2 }}
            onClick={toggleDrawer(true)}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            FindersKeepers v2
          </Typography>
        </Toolbar>
      </AppBar>
      <Drawer anchor="left" open={open} onClose={toggleDrawer(false)}>
        <List sx={{ width: 250 }}>
          {navItems.map((item) => (
            <ListItem key={item.text} disablePadding onClick={toggleDrawer(false)}>
              <ListItemButton component={Link} to={item.path}>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Drawer>
    </>
  );
}

export default Navigation;