import React from 'react';
import { Card, CardContent, Typography, Box, Avatar, Chip } from '@mui/material';
import { SystemStatus } from '@/types/api';

interface SystemStatusCardProps {
  status?: SystemStatus;
  title: string;
  icon: React.ReactNode;
}

const SystemStatusCard: React.FC<SystemStatusCardProps> = ({
  status,
  title,
  icon,
}) => {
  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'operational': return 'success';
      case 'degraded': return 'warning';
      case 'down': return 'error';
      default: return 'default';
    }
  };

  const getStatusText = (status?: string) => {
    switch (status) {
      case 'operational': return 'Operational';
      case 'degraded': return 'Degraded';
      case 'down': return 'Down';
      default: return 'Unknown';
    }
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Chip
              label={getStatusText(status?.status)}
              color={getStatusColor(status?.status) as any}
              size="small"
              sx={{ mb: 1 }}
            />
            <Typography variant="h6" component="div">
              {status?.uptime ? `${Math.floor(status.uptime / 3600)}h ${Math.floor((status.uptime % 3600) / 60)}m` : 'N/A'}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Uptime
            </Typography>
          </Box>
          <Avatar
            sx={{
              backgroundColor: status?.status === 'operational' ? '#4caf50' : 
                              status?.status === 'degraded' ? '#ff9800' : '#f44336',
              width: 56,
              height: 56,
            }}
          >
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SystemStatusCard;
