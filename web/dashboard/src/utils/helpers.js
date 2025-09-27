/**
 * SPIDER Framework - Helper Utilities
 * 
 * General utility functions for common operations.
 */

/**
 * Deep clone an object
 * @param {*} obj - Object to clone
 * @returns {*} Cloned object
 */
export const deepClone = (obj) => {
  try {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj.getTime());
    if (obj instanceof Array) return obj.map(item => deepClone(item));
    if (typeof obj === 'object') {
      const clonedObj = {};
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          clonedObj[key] = deepClone(obj[key]);
        }
      }
      return clonedObj;
    }
    return obj;
  } catch (error) {
    console.error('Error deep cloning object:', error);
    return obj;
  }
};

/**
 * Check if value is empty
 * @param {*} value - Value to check
 * @returns {boolean} True if empty
 */
export const isEmpty = (value) => {
  try {
    if (value === null || value === undefined) return true;
    if (typeof value === 'string') return value.trim().length === 0;
    if (Array.isArray(value)) return value.length === 0;
    if (typeof value === 'object') return Object.keys(value).length === 0;
    return false;
  } catch (error) {
    console.error('Error checking if value is empty:', error);
    return true;
  }
};

/**
 * Check if value is not empty
 * @param {*} value - Value to check
 * @returns {boolean} True if not empty
 */
export const isNotEmpty = (value) => {
  return !isEmpty(value);
};

/**
 * Get nested property value safely
 * @param {Object} obj - Object to get property from
 * @param {string} path - Property path (e.g., 'user.profile.name')
 * @param {*} defaultValue - Default value if property not found
 * @returns {*} Property value or default
 */
export const getNestedProperty = (obj, path, defaultValue = undefined) => {
  try {
    if (typeof obj !== 'object' || obj === null) return defaultValue;
    
    const keys = path.split('.');
    let current = obj;
    
    for (const key of keys) {
      if (current === null || current === undefined || !(key in current)) {
        return defaultValue;
      }
      current = current[key];
    }
    
    return current;
  } catch (error) {
    console.error('Error getting nested property:', error);
    return defaultValue;
  }
};

/**
 * Set nested property value safely
 * @param {Object} obj - Object to set property on
 * @param {string} path - Property path (e.g., 'user.profile.name')
 * @param {*} value - Value to set
 * @returns {Object} Modified object
 */
export const setNestedProperty = (obj, path, value) => {
  try {
    if (typeof obj !== 'object' || obj === null) return obj;
    
    const keys = path.split('.');
    const lastKey = keys.pop();
    let current = obj;
    
    for (const key of keys) {
      if (!(key in current) || typeof current[key] !== 'object' || current[key] === null) {
        current[key] = {};
      }
      current = current[key];
    }
    
    current[lastKey] = value;
    return obj;
  } catch (error) {
    console.error('Error setting nested property:', error);
    return obj;
  }
};

/**
 * Debounce function execution
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export const debounce = (func, delay) => {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
};

/**
 * Throttle function execution
 * @param {Function} func - Function to throttle
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Throttled function
 */
export const throttle = (func, delay) => {
  let lastCall = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      return func.apply(this, args);
    }
  };
};

/**
 * Generate unique ID
 * @param {string} prefix - Prefix for the ID
 * @returns {string} Unique ID
 */
export const generateId = (prefix = 'id') => {
  try {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substr(2, 5);
    return `${prefix}_${timestamp}_${random}`;
  } catch (error) {
    console.error('Error generating ID:', error);
    return `${prefix}_${Date.now()}`;
  }
};

/**
 * Sleep for specified duration
 * @param {number} ms - Duration in milliseconds
 * @returns {Promise} Promise that resolves after duration
 */
export const sleep = (ms) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * Retry function execution
 * @param {Function} func - Function to retry
 * @param {number} maxAttempts - Maximum number of attempts
 * @param {number} delay - Delay between attempts in milliseconds
 * @returns {Promise} Promise that resolves with function result
 */
export const retry = async (func, maxAttempts = 3, delay = 1000) => {
  try {
    let lastError;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await func();
      } catch (error) {
        lastError = error;
        if (attempt < maxAttempts) {
          await sleep(delay * attempt);
        }
      }
    }
    
    throw lastError;
  } catch (error) {
    console.error('Error in retry function:', error);
    throw error;
  }
};

/**
 * Group array items by key
 * @param {Array} array - Array to group
 * @param {string|Function} key - Key to group by
 * @returns {Object} Grouped object
 */
export const groupBy = (array, key) => {
  try {
    if (!Array.isArray(array)) return {};
    
    return array.reduce((groups, item) => {
      const groupKey = typeof key === 'function' ? key(item) : item[key];
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(item);
      return groups;
    }, {});
  } catch (error) {
    console.error('Error grouping array:', error);
    return {};
  }
};

/**
 * Sort array by key
 * @param {Array} array - Array to sort
 * @param {string|Function} key - Key to sort by
 * @param {string} direction - Sort direction ('asc' or 'desc')
 * @returns {Array} Sorted array
 */
export const sortBy = (array, key, direction = 'asc') => {
  try {
    if (!Array.isArray(array)) return [];
    
    return [...array].sort((a, b) => {
      const aValue = typeof key === 'function' ? key(a) : a[key];
      const bValue = typeof key === 'function' ? key(b) : b[key];
      
      if (aValue < bValue) return direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return direction === 'asc' ? 1 : -1;
      return 0;
    });
  } catch (error) {
    console.error('Error sorting array:', error);
    return array;
  }
};

/**
 * Filter array by condition
 * @param {Array} array - Array to filter
 * @param {Function} condition - Filter condition function
 * @returns {Array} Filtered array
 */
export const filterBy = (array, condition) => {
  try {
    if (!Array.isArray(array)) return [];
    
    return array.filter(condition);
  } catch (error) {
    console.error('Error filtering array:', error);
    return array;
  }
};

/**
 * Find item in array by condition
 * @param {Array} array - Array to search
 * @param {Function} condition - Search condition function
 * @returns {*} Found item or undefined
 */
export const findBy = (array, condition) => {
  try {
    if (!Array.isArray(array)) return undefined;
    
    return array.find(condition);
  } catch (error) {
    console.error('Error finding item in array:', error);
    return undefined;
  }
};

/**
 * Remove duplicates from array
 * @param {Array} array - Array to deduplicate
 * @param {string|Function} key - Key to deduplicate by
 * @returns {Array} Deduplicated array
 */
export const uniqueBy = (array, key) => {
  try {
    if (!Array.isArray(array)) return [];
    
    const seen = new Set();
    return array.filter(item => {
      const value = typeof key === 'function' ? key(item) : item[key];
      if (seen.has(value)) {
        return false;
      }
      seen.add(value);
      return true;
    });
  } catch (error) {
    console.error('Error deduplicating array:', error);
    return array;
  }
};

/**
 * Chunk array into smaller arrays
 * @param {Array} array - Array to chunk
 * @param {number} size - Chunk size
 * @returns {Array} Array of chunks
 */
export const chunk = (array, size) => {
  try {
    if (!Array.isArray(array) || size <= 0) return [];
    
    const chunks = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  } catch (error) {
    console.error('Error chunking array:', error);
    return [];
  }
};

/**
 * Flatten nested array
 * @param {Array} array - Array to flatten
 * @param {number} depth - Flattening depth
 * @returns {Array} Flattened array
 */
export const flatten = (array, depth = 1) => {
  try {
    if (!Array.isArray(array)) return [];
    
    return array.flat(depth);
  } catch (error) {
    console.error('Error flattening array:', error);
    return array;
  }
};

/**
 * Merge objects deeply
 * @param {Object} target - Target object
 * @param {...Object} sources - Source objects
 * @returns {Object} Merged object
 */
export const deepMerge = (target, ...sources) => {
  try {
    if (!sources.length) return target;
    const source = sources.shift();
    
    if (isObject(target) && isObject(source)) {
      for (const key in source) {
        if (isObject(source[key])) {
          if (!target[key]) Object.assign(target, { [key]: {} });
          deepMerge(target[key], source[key]);
        } else {
          Object.assign(target, { [key]: source[key] });
        }
      }
    }
    
    return deepMerge(target, ...sources);
  } catch (error) {
    console.error('Error merging objects:', error);
    return target;
  }
};

/**
 * Check if value is object
 * @param {*} value - Value to check
 * @returns {boolean} True if object
 */
const isObject = (value) => {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
};

/**
 * Pick specific properties from object
 * @param {Object} obj - Object to pick from
 * @param {Array} keys - Keys to pick
 * @returns {Object} Object with picked properties
 */
export const pick = (obj, keys) => {
  try {
    if (typeof obj !== 'object' || obj === null) return {};
    
    const result = {};
    for (const key of keys) {
      if (key in obj) {
        result[key] = obj[key];
      }
    }
    return result;
  } catch (error) {
    console.error('Error picking properties:', error);
    return {};
  }
};

/**
 * Omit specific properties from object
 * @param {Object} obj - Object to omit from
 * @param {Array} keys - Keys to omit
 * @returns {Object} Object without omitted properties
 */
export const omit = (obj, keys) => {
  try {
    if (typeof obj !== 'object' || obj === null) return {};
    
    const result = { ...obj };
    for (const key of keys) {
      delete result[key];
    }
    return result;
  } catch (error) {
    console.error('Error omitting properties:', error);
    return obj;
  }
};
