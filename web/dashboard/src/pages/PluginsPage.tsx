import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const PluginsPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Plugins
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Plugin management interface coming soon...
        </Typography>
      </Paper>
    </Box>
  );
};

export default PluginsPage;
