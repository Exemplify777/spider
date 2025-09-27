import { apiClient } from './apiClient';
import { DashboardMetrics, SystemStatus, PerformanceMetrics } from '@/types/api';

class DashboardService {
  async getDashboardMetrics(timeRange: string = '24h'): Promise<DashboardMetrics> {
    const response = await apiClient.get(`/dashboard/metrics?time_range=${timeRange}`);
    return response.data.data;
  }

  async getSystemStatus(): Promise<SystemStatus> {
    const response = await apiClient.get('/dashboard/system-status');
    return response.data.data;
  }

  async getPerformanceMetrics(timeRange: string = '1h'): Promise<PerformanceMetrics> {
    const response = await apiClient.get(`/dashboard/performance?time_range=${timeRange}`);
    return response.data.data;
  }

  async getWidgets(): Promise<any[]> {
    const response = await apiClient.get('/dashboard/widgets');
    return response.data.data;
  }

  async createWidget(widget: any): Promise<any> {
    const response = await apiClient.post('/dashboard/widgets', widget);
    return response.data.data;
  }

  async updateWidget(widgetId: string, widget: any): Promise<any> {
    const response = await apiClient.put(`/dashboard/widgets/${widgetId}`, widget);
    return response.data.data;
  }

  async deleteWidget(widgetId: string): Promise<void> {
    await apiClient.delete(`/dashboard/widgets/${widgetId}`);
  }

  async getLayouts(): Promise<any[]> {
    const response = await apiClient.get('/dashboard/layouts');
    return response.data.data;
  }

  async createLayout(layout: any): Promise<any> {
    const response = await apiClient.post('/dashboard/layouts', layout);
    return response.data.data;
  }

  async updateLayout(layoutId: string, layout: any): Promise<any> {
    const response = await apiClient.put(`/dashboard/layouts/${layoutId}`, layout);
    return response.data.data;
  }

  async deleteLayout(layoutId: string): Promise<void> {
    await apiClient.delete(`/dashboard/layouts/${layoutId}`);
  }

  async getRecentActivities(limit: number = 20): Promise<any[]> {
    const response = await apiClient.get(`/dashboard/activities?limit=${limit}`);
    return response.data.data;
  }

  async getAlerts(status?: string, severity?: string, limit: number = 50): Promise<any[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (severity) params.append('severity', severity);
    params.append('limit', limit.toString());
    
    const response = await apiClient.get(`/dashboard/alerts?${params.toString()}`);
    return response.data.data;
  }

  async resolveAlert(alertId: string): Promise<void> {
    await apiClient.post(`/dashboard/alerts/${alertId}/resolve`);
  }
}

export const dashboardService = new DashboardService();
