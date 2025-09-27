import axios from 'axios';
import { User, LoginData, TokenRefresh, PasswordChange, UserUpdate } from '@/types/auth';
import { APIResponse } from '@/types/api';
import { apiClient } from './apiClient';

class AuthService {
  async login(data: LoginData): Promise<APIResponse> {
    const response = await apiClient.post('/auth/login', data);
    return response.data;
  }

  async logout(): Promise<APIResponse> {
    const response = await apiClient.post('/auth/logout');
    return response.data;
  }

  async refreshToken(refreshToken: string): Promise<APIResponse> {
    const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/auth/me');
    return response.data.data;
  }

  async updateProfile(data: UserUpdate): Promise<APIResponse> {
    const response = await apiClient.put('/auth/me', data);
    return response.data;
  }

  async changePassword(data: PasswordChange): Promise<APIResponse> {
    const response = await apiClient.post('/auth/change-password', data);
    return response.data;
  }

  async resetPassword(email: string): Promise<APIResponse> {
    const response = await apiClient.post('/auth/reset-password', { email });
    return response.data;
  }

  async confirmPasswordReset(token: string, newPassword: string): Promise<APIResponse> {
    const response = await apiClient.post('/auth/reset-password/confirm', {
      token,
      new_password: newPassword,
    });
    return response.data;
  }

  async getUserSessions(): Promise<any[]> {
    const response = await apiClient.get('/auth/sessions');
    return response.data.data;
  }

  async revokeSession(sessionId: string): Promise<APIResponse> {
    const response = await apiClient.delete(`/auth/sessions/${sessionId}`);
    return response.data;
  }
}

export const authService = new AuthService();
