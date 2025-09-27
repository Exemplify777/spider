import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const MonitoringPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Monitoring
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Monitoring dashboard coming soon...
        </Typography>
      </Paper>
    </Box>
  );
};

export default MonitoringPage;
