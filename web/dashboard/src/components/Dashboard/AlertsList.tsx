import React from 'react';
import { Card, CardContent, Typography, List, ListItem, Chip, Box } from '@mui/material';
import { Alert as AlertIcon } from '@mui/icons-material';

interface AlertsListProps {
  alerts: any[];
}

const AlertsList: React.FC<AlertsListProps> = ({ alerts }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Active Alerts
        </Typography>
        {alerts.length > 0 ? (
          <List>
            {alerts.map((alert, index) => (
              <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                <Box display="flex" alignItems="center" width="100%" mb={1}>
                  <AlertIcon sx={{ mr: 1, color: 'warning.main' }} />
                  <Typography variant="body1" sx={{ flexGrow: 1 }}>
                    {alert.message || alert.title}
                  </Typography>
                  <Chip
                    label={alert.severity || 'Unknown'}
                    color={getSeverityColor(alert.severity) as any}
                    size="small"
                  />
                </Box>
                <Typography variant="body2" color="textSecondary">
                  {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : ''}
                </Typography>
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="textSecondary">
            No active alerts
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default AlertsList;
