import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const UsersPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Users
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          User management interface coming soon...
        </Typography>
      </Paper>
    </Box>
  );
};

export default UsersPage;
