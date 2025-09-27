import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const ConfigurationPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Configuration
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Configuration management interface coming soon...
        </Typography>
      </Paper>
    </Box>
  );
};

export default ConfigurationPage;
