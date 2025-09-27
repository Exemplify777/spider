import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const SystemPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        System
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          System administration interface coming soon...
        </Typography>
      </Paper>
    </Box>
  );
};

export default SystemPage;
