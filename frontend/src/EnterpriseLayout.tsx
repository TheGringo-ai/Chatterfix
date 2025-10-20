
import React from 'react';
import { Box, AppBar, Toolbar, Typography, Drawer, List } from '@mui/material';
import { Outlet } from 'react-router-dom';
import { Navigation } from './Navigation';
import { UserMenu } from './UserMenu';
import { TenantSelector } from './TenantSelector';
import { NotificationCenter } from './NotificationCenter';

const drawerWidth = 280;

export const EnterpriseLayout: React.FC = () => {
  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: theme => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            ChatterFix Enterprise CMMS
          </Typography>
          <TenantSelector />
          <NotificationCenter />
          <UserMenu />
        </Toolbar>
      </AppBar>
      
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        <Toolbar />
        <Navigation />
      </Drawer>
      
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
};
