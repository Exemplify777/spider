/**
 * SPIDER Framework - Authentication Utilities
 * 
 * Utility functions for authentication and authorization.
 */

const AUTH_TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_INFO_KEY = 'user_info';

/**
 * Get authentication token from localStorage
 * @returns {string|null} Authentication token
 */
export const getAuthToken = () => {
  try {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  } catch (error) {
    console.error('Error getting auth token:', error);
    return null;
  }
};

/**
 * Set authentication token in localStorage
 * @param {string} token - Authentication token
 */
export const setAuthToken = (token) => {
  try {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  } catch (error) {
    console.error('Error setting auth token:', error);
  }
};

/**
 * Clear authentication token from localStorage
 */
export const clearAuthToken = () => {
  try {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  } catch (error) {
    console.error('Error clearing auth token:', error);
  }
};

/**
 * Get refresh token from localStorage
 * @returns {string|null} Refresh token
 */
export const getRefreshToken = () => {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch (error) {
    console.error('Error getting refresh token:', error);
    return null;
  }
};

/**
 * Set refresh token in localStorage
 * @param {string} token - Refresh token
 */
export const setRefreshToken = (token) => {
  try {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  } catch (error) {
    console.error('Error setting refresh token:', error);
  }
};

/**
 * Clear refresh token from localStorage
 */
export const clearRefreshToken = () => {
  try {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  } catch (error) {
    console.error('Error clearing refresh token:', error);
  }
};

/**
 * Check if user is authenticated
 * @returns {boolean} True if authenticated
 */
export const isAuthenticated = () => {
  const token = getAuthToken();
  if (!token) return false;
  
  try {
    // Check if token is expired
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    return payload.exp > currentTime;
  } catch (error) {
    console.error('Error checking authentication:', error);
    return false;
  }
};

/**
 * Get user information from localStorage
 * @returns {Object|null} User information
 */
export const getUserInfo = () => {
  try {
    const userInfo = localStorage.getItem(USER_INFO_KEY);
    return userInfo ? JSON.parse(userInfo) : null;
  } catch (error) {
    console.error('Error getting user info:', error);
    return null;
  }
};

/**
 * Set user information in localStorage
 * @param {Object} userInfo - User information
 */
export const setUserInfo = (userInfo) => {
  try {
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
  } catch (error) {
    console.error('Error setting user info:', error);
  }
};

/**
 * Clear user information from localStorage
 */
export const clearUserInfo = () => {
  try {
    localStorage.removeItem(USER_INFO_KEY);
  } catch (error) {
    console.error('Error clearing user info:', error);
  }
};

/**
 * Check if user has specific permission
 * @param {string} permission - Permission to check
 * @returns {boolean} True if user has permission
 */
export const hasPermission = (permission) => {
  try {
    const userInfo = getUserInfo();
    if (!userInfo || !userInfo.permissions) return false;
    
    return userInfo.permissions.includes(permission);
  } catch (error) {
    console.error('Error checking permission:', error);
    return false;
  }
};

/**
 * Check if user has specific role
 * @param {string} role - Role to check
 * @returns {boolean} True if user has role
 */
export const hasRole = (role) => {
  try {
    const userInfo = getUserInfo();
    if (!userInfo || !userInfo.roles) return false;
    
    return userInfo.roles.includes(role);
  } catch (error) {
    console.error('Error checking role:', error);
    return false;
  }
};

/**
 * Get user roles
 * @returns {Array} Array of user roles
 */
export const getUserRoles = () => {
  try {
    const userInfo = getUserInfo();
    return userInfo ? userInfo.roles || [] : [];
  } catch (error) {
    console.error('Error getting user roles:', error);
    return [];
  }
};

/**
 * Get user permissions
 * @returns {Array} Array of user permissions
 */
export const getUserPermissions = () => {
  try {
    const userInfo = getUserInfo();
    return userInfo ? userInfo.permissions || [] : [];
  } catch (error) {
    console.error('Error getting user permissions:', error);
    return [];
  }
};

/**
 * Validate authentication token
 * @param {string} token - Token to validate
 * @returns {boolean} True if valid
 */
export const validateToken = (token) => {
  try {
    if (!token) return false;
    
    const parts = token.split('.');
    if (parts.length !== 3) return false;
    
    const payload = JSON.parse(atob(parts[1]));
    const currentTime = Date.now() / 1000;
    
    return payload.exp > currentTime;
  } catch (error) {
    console.error('Error validating token:', error);
    return false;
  }
};

/**
 * Refresh authentication token
 * @returns {Promise<boolean>} True if refresh successful
 */
export const refreshToken = async () => {
  try {
    const refreshTokenValue = getRefreshToken();
    if (!refreshTokenValue) return false;
    
    // Make API request to refresh token
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshTokenValue }),
    });
    
    if (response.ok) {
      const data = await response.json();
      setAuthToken(data.access_token);
      if (data.refresh_token) {
        setRefreshToken(data.refresh_token);
      }
      return true;
    }
    
    return false;
  } catch (error) {
    console.error('Error refreshing token:', error);
    return false;
  }
};

/**
 * Logout user and clear all authentication data
 */
export const logoutUser = () => {
  try {
    clearAuthToken();
    clearRefreshToken();
    clearUserInfo();
  } catch (error) {
    console.error('Error logging out user:', error);
  }
};

/**
 * Login user and set authentication data
 * @param {string} token - Authentication token
 * @param {string} refreshToken - Refresh token
 * @param {Object} userInfo - User information
 */
export const loginUser = (token, refreshToken, userInfo) => {
  try {
    setAuthToken(token);
    if (refreshToken) {
      setRefreshToken(refreshToken);
    }
    setUserInfo(userInfo);
  } catch (error) {
    console.error('Error logging in user:', error);
  }
};

/**
 * Check if user is admin
 * @returns {boolean} True if user is admin
 */
export const isAdmin = () => {
  return hasRole('admin') || hasRole('super_admin');
};

/**
 * Check if user is super admin
 * @returns {boolean} True if user is super admin
 */
export const isSuperAdmin = () => {
  return hasRole('super_admin');
};

/**
 * Check if user can access resource
 * @param {string} resource - Resource to access
 * @param {string} action - Action to perform
 * @returns {boolean} True if user can access resource
 */
export const canAccessResource = (resource, action) => {
  try {
    const userInfo = getUserInfo();
    if (!userInfo || !userInfo.permissions) return false;
    
    const permission = `${resource}:${action}`;
    return userInfo.permissions.includes(permission);
  } catch (error) {
    console.error('Error checking resource access:', error);
    return false;
  }
};

/**
 * Get user display name
 * @returns {string} User display name
 */
export const getUserDisplayName = () => {
  try {
    const userInfo = getUserInfo();
    if (!userInfo) return 'Guest';
    
    if (userInfo.display_name) {
      return userInfo.display_name;
    }
    
    if (userInfo.first_name && userInfo.last_name) {
      return `${userInfo.first_name} ${userInfo.last_name}`;
    }
    
    if (userInfo.username) {
      return userInfo.username;
    }
    
    if (userInfo.email) {
      return userInfo.email;
    }
    
    return 'User';
  } catch (error) {
    console.error('Error getting user display name:', error);
    return 'Guest';
  }
};

/**
 * Check if user is logged in
 * @returns {boolean} True if user is logged in
 */
export const isLoggedIn = () => {
  return isAuthenticated() && getUserInfo() !== null;
};
