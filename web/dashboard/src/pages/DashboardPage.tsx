import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Computer as SystemIcon,
  Speed as PerformanceIcon,
  Extension as PluginsIcon,
  Warning as AlertIcon,
} from '@mui/icons-material';
import { useWebSocket } from '@/hooks/useWebSocket';
import { DashboardMetrics, SystemStatus } from '@/types/api';
import { dashboardService } from '@/services/dashboardService';
import MetricCard from '@/components/Dashboard/MetricCard';
import SystemStatusCard from '@/components/Dashboard/SystemStatusCard';
import RecentActivities from '@/components/Dashboard/RecentActivities';
import AlertsList from '@/components/Dashboard/AlertsList';

const DashboardPage: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const { isConnected, subscribe, unsubscribe } = useWebSocket();

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        const data = await dashboardService.getDashboardMetrics();
        setMetrics(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  useEffect(() => {
    const handleMetricsUpdate = (data: any) => {
      setMetrics(prev => ({
        ...prev,
        system_health: data.system_health || prev?.system_health,
        performance_metrics: data.performance_metrics || prev?.performance_metrics,
      }));
    };

    subscribe('metrics_update', handleMetricsUpdate);

    return () => {
      unsubscribe('metrics_update', handleMetricsUpdate);
    };
  }, [subscribe, unsubscribe]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Chip
          label={isConnected ? 'Connected' : 'Disconnected'}
          color={isConnected ? 'success' : 'error'}
          size="small"
        />
      </Box>

      <Grid container spacing={3}>
        {/* System Status */}
        <Grid item xs={12} md={6} lg={3}>
          <SystemStatusCard
            status={metrics?.system_health}
            title="System Status"
            icon={<SystemIcon />}
          />
        </Grid>

        {/* Performance Metrics */}
        <Grid item xs={12} md={6} lg={3}>
          <MetricCard
            title="Performance"
            value={metrics?.performance_metrics?.response_time || 0}
            unit="ms"
            icon={<PerformanceIcon />}
            color="primary"
          />
        </Grid>

        {/* Active Plugins */}
        <Grid item xs={12} md={6} lg={3}>
          <MetricCard
            title="Active Plugins"
            value={metrics?.active_plugins?.length || 0}
            icon={<PluginsIcon />}
            color="secondary"
          />
        </Grid>

        {/* Alerts */}
        <Grid item xs={12} md={6} lg={3}>
          <MetricCard
            title="Active Alerts"
            value={metrics?.alerts?.length || 0}
            icon={<AlertIcon />}
            color="warning"
          />
        </Grid>

        {/* System Health Details */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              {metrics?.system_health && (
                <Box>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2">CPU Usage</Typography>
                    <Typography variant="body2">
                      {metrics.system_health.cpu_usage.toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2">Memory Usage</Typography>
                    <Typography variant="body2">
                      {metrics.system_health.memory_usage.toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2">Active Sessions</Typography>
                    <Typography variant="body2">
                      {metrics.system_health.active_sessions}
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2">Total Requests</Typography>
                    <Typography variant="body2">
                      {metrics.system_health.total_requests.toLocaleString()}
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2">Error Rate</Typography>
                    <Typography variant="body2">
                      {(metrics.system_health.error_rate * 100).toFixed(2)}%
                    </Typography>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activities */}
        <Grid item xs={12} md={6}>
          <RecentActivities activities={metrics?.recent_activities || []} />
        </Grid>

        {/* Alerts */}
        <Grid item xs={12}>
          <AlertsList alerts={metrics?.alerts || []} />
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;
