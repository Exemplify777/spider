import React from 'react';
import { Card, CardContent, Typography, Box, Avatar } from '@mui/material';

interface MetricCardProps {
  title: string;
  value: number | string;
  unit?: string;
  icon: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: number;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  icon,
  color = 'primary',
  trend,
  trendValue,
}) => {
  const getColorValue = () => {
    switch (color) {
      case 'success': return '#4caf50';
      case 'warning': return '#ff9800';
      case 'error': return '#f44336';
      case 'info': return '#2196f3';
      case 'secondary': return '#9c27b0';
      default: return '#1976d2';
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
            <Typography variant="h4" component="div">
              {typeof value === 'number' ? value.toLocaleString() : value}
              {unit && (
                <Typography component="span" variant="body2" color="textSecondary" sx={{ ml: 1 }}>
                  {unit}
                </Typography>
              )}
            </Typography>
            {trend && trendValue && (
              <Typography
                variant="body2"
                color={trend === 'up' ? 'success.main' : trend === 'down' ? 'error.main' : 'text.secondary'}
                sx={{ mt: 1 }}
              >
                {trend === 'up' ? '↗' : trend === 'down' ? '↘' : '→'} {trendValue}%
              </Typography>
            )}
          </Box>
          <Avatar
            sx={{
              backgroundColor: getColorValue(),
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

export default MetricCard;
