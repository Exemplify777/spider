import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, LoginData, TokenData } from '@/types/auth';
import { APIResponse } from '@/types/api';
import { authService } from '@/services/authService';
import { tokenService } from '@/services/tokenService';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginData) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const isAuthenticated = !!user;

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = tokenService.getToken();
        if (token) {
          const userData = await authService.getCurrentUser();
          setUser(userData);
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        tokenService.clearToken();
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (data: LoginData): Promise<void> => {
    try {
      setLoading(true);
      const response: APIResponse = await authService.login(data);
      
      if (response.success && response.data) {
        const { access_token, user: userData } = response.data;
        tokenService.setToken(access_token);
        setUser(userData);
      } else {
        throw new Error(response.message || 'Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      tokenService.clearToken();
      setUser(null);
    }
  };

  const refreshToken = async (): Promise<void> => {
    try {
      const refreshTokenValue = tokenService.getRefreshToken();
      if (!refreshTokenValue) {
        throw new Error('No refresh token available');
      }

      const response: APIResponse = await authService.refreshToken(refreshTokenValue);
      
      if (response.success && response.data) {
        const { access_token } = response.data;
        tokenService.setToken(access_token);
      } else {
        throw new Error('Token refresh failed');
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      logout();
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    login,
    logout,
    refreshToken,
    isAuthenticated,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
