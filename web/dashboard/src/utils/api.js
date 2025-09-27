/**
 * SPIDER Framework - API Utilities
 * 
 * Utility functions for making API requests and handling responses.
 */

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = parseInt(process.env.REACT_APP_API_TIMEOUT) || 30000;
const API_RETRY_ATTEMPTS = parseInt(process.env.REACT_APP_API_RETRY_ATTEMPTS) || 3;
const API_RETRY_DELAY = parseInt(process.env.REACT_APP_API_RETRY_DELAY) || 1000;

/**
 * Get API headers with authentication token
 * @returns {Object} Headers object
 */
export const getApiHeaders = () => {
  const token = localStorage.getItem('auth_token');
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

/**
 * Build full API URL
 * @param {string} endpoint - API endpoint
 * @returns {string} Full API URL
 */
export const buildApiUrl = (endpoint) => {
  const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
};

/**
 * Make API request with retry logic
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Request options
 * @param {number} attempt - Current attempt number
 * @returns {Promise} API response
 */
export const makeApiRequest = async (endpoint, options = {}, attempt = 1) => {
  try {
    const url = buildApiUrl(endpoint);
    const defaultOptions = {
      method: 'GET',
      headers: getApiHeaders(),
      timeout: API_TIMEOUT,
    };
    
    const requestOptions = { ...defaultOptions, ...options };
    
    const response = await fetch(url, requestOptions);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return {
      success: true,
      data,
      status: response.status,
    };
  } catch (error) {
    if (attempt < API_RETRY_ATTEMPTS && isRetryableError(error)) {
      const delay = API_RETRY_DELAY * Math.pow(2, attempt - 1);
      await new Promise(resolve => setTimeout(resolve, delay));
      return makeApiRequest(endpoint, options, attempt + 1);
    }
    
    return {
      success: false,
      error: error.message,
      status: error.status || 500,
    };
  }
};

/**
 * Check if error is retryable
 * @param {Error} error - Error object
 * @returns {boolean} True if retryable
 */
const isRetryableError = (error) => {
  const retryableStatusCodes = [408, 429, 500, 502, 503, 504];
  return retryableStatusCodes.includes(error.status) || 
         error.message.includes('timeout') ||
         error.message.includes('network');
};

/**
 * Handle API response
 * @param {Object} response - API response
 * @returns {Object} Processed response
 */
export const handleApiResponse = (response) => {
  if (response.success) {
    return {
      success: true,
      data: response.data,
      status: response.status,
    };
  }
  
  return {
    success: false,
    error: response.error || 'Unknown error occurred',
    status: response.status || 500,
  };
};

/**
 * Format API error for display
 * @param {Object} error - Error object
 * @returns {string} Formatted error message
 */
export const formatApiError = (error) => {
  if (typeof error === 'string') {
    return error;
  }
  
  if (error.message) {
    return error.message;
  }
  
  if (error.error) {
    return error.error;
  }
  
  return 'An unknown error occurred';
};

/**
 * Parse API response data
 * @param {Object} response - API response
 * @returns {*} Parsed data
 */
export const parseApiResponse = (response) => {
  try {
    if (response.success && response.data) {
      return response.data;
    }
    return null;
  } catch (error) {
    console.error('Error parsing API response:', error);
    return null;
  }
};

/**
 * Validate API response
 * @param {Object} response - API response
 * @returns {boolean} True if valid
 */
export const validateApiResponse = (response) => {
  return response && 
         typeof response === 'object' && 
         'success' in response &&
         'data' in response;
};

/**
 * Get API timeout configuration
 * @returns {number} Timeout in milliseconds
 */
export const getApiTimeout = () => {
  return API_TIMEOUT;
};

/**
 * Get API retry configuration
 * @returns {Object} Retry configuration
 */
export const getApiRetryConfig = () => {
  return {
    attempts: API_RETRY_ATTEMPTS,
    delay: API_RETRY_DELAY,
  };
};

/**
 * Make GET request
 * @param {string} endpoint - API endpoint
 * @param {Object} params - Query parameters
 * @returns {Promise} API response
 */
export const apiGet = async (endpoint, params = {}) => {
  const queryString = new URLSearchParams(params).toString();
  const url = queryString ? `${endpoint}?${queryString}` : endpoint;
  
  return makeApiRequest(url, { method: 'GET' });
};

/**
 * Make POST request
 * @param {string} endpoint - API endpoint
 * @param {Object} data - Request data
 * @returns {Promise} API response
 */
export const apiPost = async (endpoint, data = {}) => {
  return makeApiRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

/**
 * Make PUT request
 * @param {string} endpoint - API endpoint
 * @param {Object} data - Request data
 * @returns {Promise} API response
 */
export const apiPut = async (endpoint, data = {}) => {
  return makeApiRequest(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
};

/**
 * Make DELETE request
 * @param {string} endpoint - API endpoint
 * @returns {Promise} API response
 */
export const apiDelete = async (endpoint) => {
  return makeApiRequest(endpoint, { method: 'DELETE' });
};

/**
 * Make PATCH request
 * @param {string} endpoint - API endpoint
 * @param {Object} data - Request data
 * @returns {Promise} API response
 */
export const apiPatch = async (endpoint, data = {}) => {
  return makeApiRequest(endpoint, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
};
