/**
 * SPIDER Framework - Formatting Utilities
 * 
 * Utility functions for formatting data and text.
 */

/**
 * Format date to readable string
 * @param {Date|string|number} date - Date to format
 * @param {Object} options - Formatting options
 * @returns {string} Formatted date string
 */
export const formatDate = (date, options = {}) => {
  try {
    const dateObj = new Date(date);
    if (isNaN(dateObj.getTime())) return 'Invalid Date';
    
    const defaultOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZoneName: 'short',
    };
    
    const formatOptions = { ...defaultOptions, ...options };
    return dateObj.toLocaleDateString('en-US', formatOptions);
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Invalid Date';
  }
};

/**
 * Format date to relative time (e.g., "2 hours ago")
 * @param {Date|string|number} date - Date to format
 * @returns {string} Relative time string
 */
export const formatRelativeTime = (date) => {
  try {
    const dateObj = new Date(date);
    if (isNaN(dateObj.getTime())) return 'Invalid Date';
    
    const now = new Date();
    const diffInSeconds = Math.floor((now - dateObj) / 1000);
    
    if (diffInSeconds < 60) {
      return 'Just now';
    }
    
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) {
      return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
    }
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) {
      return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
    }
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) {
      return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
    }
    
    const diffInWeeks = Math.floor(diffInDays / 7);
    if (diffInWeeks < 4) {
      return `${diffInWeeks} week${diffInWeeks > 1 ? 's' : ''} ago`;
    }
    
    const diffInMonths = Math.floor(diffInDays / 30);
    if (diffInMonths < 12) {
      return `${diffInMonths} month${diffInMonths > 1 ? 's' : ''} ago`;
    }
    
    const diffInYears = Math.floor(diffInDays / 365);
    return `${diffInYears} year${diffInYears > 1 ? 's' : ''} ago`;
  } catch (error) {
    console.error('Error formatting relative time:', error);
    return 'Invalid Date';
  }
};

/**
 * Format number with commas
 * @param {number} number - Number to format
 * @returns {string} Formatted number string
 */
export const formatNumber = (number) => {
  try {
    if (typeof number !== 'number' || isNaN(number)) return '0';
    return number.toLocaleString();
  } catch (error) {
    console.error('Error formatting number:', error);
    return '0';
  }
};

/**
 * Format currency
 * @param {number} amount - Amount to format
 * @param {string} currency - Currency code
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (amount, currency = 'USD') => {
  try {
    if (typeof amount !== 'number' || isNaN(amount)) return '$0.00';
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  } catch (error) {
    console.error('Error formatting currency:', error);
    return '$0.00';
  }
};

/**
 * Format percentage
 * @param {number} value - Value to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage string
 */
export const formatPercentage = (value, decimals = 2) => {
  try {
    if (typeof value !== 'number' || isNaN(value)) return '0%';
    
    return `${(value * 100).toFixed(decimals)}%`;
  } catch (error) {
    console.error('Error formatting percentage:', error);
    return '0%';
  }
};

/**
 * Format file size
 * @param {number} bytes - Size in bytes
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted file size string
 */
export const formatFileSize = (bytes, decimals = 2) => {
  try {
    if (typeof bytes !== 'number' || isNaN(bytes) || bytes < 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
  } catch (error) {
    console.error('Error formatting file size:', error);
    return '0 B';
  }
};

/**
 * Format duration in seconds to readable string
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration string
 */
export const formatDuration = (seconds) => {
  try {
    if (typeof seconds !== 'number' || isNaN(seconds) || seconds < 0) return '0s';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  } catch (error) {
    console.error('Error formatting duration:', error);
    return '0s';
  }
};

/**
 * Format text to title case
 * @param {string} text - Text to format
 * @returns {string} Title case text
 */
export const formatTitleCase = (text) => {
  try {
    if (typeof text !== 'string') return '';
    
    return text.replace(/\w\S*/g, (txt) => 
      txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()
    );
  } catch (error) {
    console.error('Error formatting title case:', error);
    return '';
  }
};

/**
 * Format text to sentence case
 * @param {string} text - Text to format
 * @returns {string} Sentence case text
 */
export const formatSentenceCase = (text) => {
  try {
    if (typeof text !== 'string') return '';
    
    return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
  } catch (error) {
    console.error('Error formatting sentence case:', error);
    return '';
  }
};

/**
 * Format text to camel case
 * @param {string} text - Text to format
 * @returns {string} Camel case text
 */
export const formatCamelCase = (text) => {
  try {
    if (typeof text !== 'string') return '';
    
    return text.replace(/(?:^\w|[A-Z]|\b\w)/g, (word, index) => {
      return index === 0 ? word.toLowerCase() : word.toUpperCase();
    }).replace(/\s+/g, '');
  } catch (error) {
    console.error('Error formatting camel case:', error);
    return '';
  }
};

/**
 * Format text to kebab case
 * @param {string} text - Text to format
 * @returns {string} Kebab case text
 */
export const formatKebabCase = (text) => {
  try {
    if (typeof text !== 'string') return '';
    
    return text
      .replace(/([a-z])([A-Z])/g, '$1-$2')
      .replace(/[\s_]+/g, '-')
      .toLowerCase();
  } catch (error) {
    console.error('Error formatting kebab case:', error);
    return '';
  }
};

/**
 * Format text to snake case
 * @param {string} text - Text to format
 * @returns {string} Snake case text
 */
export const formatSnakeCase = (text) => {
  try {
    if (typeof text !== 'string') return '';
    
    return text
      .replace(/([a-z])([A-Z])/g, '$1_$2')
      .replace(/[\s-]+/g, '_')
      .toLowerCase();
  } catch (error) {
    console.error('Error formatting snake case:', error);
    return '';
  }
};

/**
 * Format text to truncate with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
export const formatTruncate = (text, maxLength = 50) => {
  try {
    if (typeof text !== 'string') return '';
    if (text.length <= maxLength) return text;
    
    return text.substring(0, maxLength) + '...';
  } catch (error) {
    console.error('Error formatting truncate:', error);
    return '';
  }
};

/**
 * Format text to capitalize first letter
 * @param {string} text - Text to format
 * @returns {string} Capitalized text
 */
export const formatCapitalize = (text) => {
  try {
    if (typeof text !== 'string') return '';
    if (text.length === 0) return '';
    
    return text.charAt(0).toUpperCase() + text.slice(1);
  } catch (error) {
    console.error('Error formatting capitalize:', error);
    return '';
  }
};

/**
 * Format text to remove extra whitespace
 * @param {string} text - Text to format
 * @returns {string} Cleaned text
 */
export const formatCleanWhitespace = (text) => {
  try {
    if (typeof text !== 'string') return '';
    
    return text.replace(/\s+/g, ' ').trim();
  } catch (error) {
    console.error('Error formatting clean whitespace:', error);
    return '';
  }
};

/**
 * Format text to remove HTML tags
 * @param {string} text - Text to format
 * @returns {string} Cleaned text
 */
export const formatStripHtml = (text) => {
  try {
    if (typeof text !== 'string') return '';
    
    return text.replace(/<[^>]*>/g, '');
  } catch (error) {
    console.error('Error formatting strip HTML:', error);
    return '';
  }
};

/**
 * Format text to escape HTML
 * @param {string} text - Text to format
 * @returns {string} Escaped text
 */
export const formatEscapeHtml = (text) => {
  try {
    if (typeof text !== 'string') return '';
    
    const htmlEscapeMap = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    };
    
    return text.replace(/[&<>"']/g, (char) => htmlEscapeMap[char]);
  } catch (error) {
    console.error('Error formatting escape HTML:', error);
    return '';
  }
};
