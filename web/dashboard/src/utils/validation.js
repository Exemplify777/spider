/**
 * SPIDER Framework - Validation Utilities
 * 
 * Utility functions for data validation.
 */

/**
 * Validate email address format
 * @param {string} email - Email to validate
 * @returns {boolean} True if valid
 */
export const validateEmail = (email) => {
  try {
    if (typeof email !== 'string') return false;
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  } catch (error) {
    console.error('Error validating email:', error);
    return false;
  }
};

/**
 * Validate password strength
 * @param {string} password - Password to validate
 * @param {Object} options - Validation options
 * @returns {Object} Validation result
 */
export const validatePassword = (password, options = {}) => {
  try {
    const {
      minLength = 8,
      requireUppercase = true,
      requireLowercase = true,
      requireNumbers = true,
      requireSpecialChars = true,
    } = options;
    
    const result = {
      valid: true,
      errors: [],
    };
    
    if (typeof password !== 'string') {
      result.valid = false;
      result.errors.push('Password must be a string');
      return result;
    }
    
    if (password.length < minLength) {
      result.valid = false;
      result.errors.push(`Password must be at least ${minLength} characters long`);
    }
    
    if (requireUppercase && !/[A-Z]/.test(password)) {
      result.valid = false;
      result.errors.push('Password must contain at least one uppercase letter');
    }
    
    if (requireLowercase && !/[a-z]/.test(password)) {
      result.valid = false;
      result.errors.push('Password must contain at least one lowercase letter');
    }
    
    if (requireNumbers && !/\d/.test(password)) {
      result.valid = false;
      result.errors.push('Password must contain at least one number');
    }
    
    if (requireSpecialChars && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      result.valid = false;
      result.errors.push('Password must contain at least one special character');
    }
    
    return result;
  } catch (error) {
    console.error('Error validating password:', error);
    return {
      valid: false,
      errors: ['Validation error occurred'],
    };
  }
};

/**
 * Validate URL format
 * @param {string} url - URL to validate
 * @returns {boolean} True if valid
 */
export const validateUrl = (url) => {
  try {
    if (typeof url !== 'string') return false;
    
    const urlRegex = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/;
    return urlRegex.test(url);
  } catch (error) {
    console.error('Error validating URL:', error);
    return false;
  }
};

/**
 * Validate phone number format
 * @param {string} phone - Phone number to validate
 * @returns {boolean} True if valid
 */
export const validatePhone = (phone) => {
  try {
    if (typeof phone !== 'string') return false;
    
    // Remove all non-digit characters
    const digits = phone.replace(/\D/g, '');
    
    // Check if it's a valid length (7-15 digits)
    return digits.length >= 7 && digits.length <= 15;
  } catch (error) {
    console.error('Error validating phone:', error);
    return false;
  }
};

/**
 * Validate username format
 * @param {string} username - Username to validate
 * @param {Object} options - Validation options
 * @returns {Object} Validation result
 */
export const validateUsername = (username, options = {}) => {
  try {
    const {
      minLength = 3,
      maxLength = 20,
      allowUnderscores = true,
      allowHyphens = true,
    } = options;
    
    const result = {
      valid: true,
      errors: [],
    };
    
    if (typeof username !== 'string') {
      result.valid = false;
      result.errors.push('Username must be a string');
      return result;
    }
    
    if (username.length < minLength) {
      result.valid = false;
      result.errors.push(`Username must be at least ${minLength} characters long`);
    }
    
    if (username.length > maxLength) {
      result.valid = false;
      result.errors.push(`Username must be no more than ${maxLength} characters long`);
    }
    
    let allowedChars = 'a-zA-Z0-9';
    if (allowUnderscores) allowedChars += '_';
    if (allowHyphens) allowedChars += '-';
    
    const usernameRegex = new RegExp(`^[${allowedChars}]+$`);
    if (!usernameRegex.test(username)) {
      result.valid = false;
      result.errors.push('Username can only contain letters, numbers, underscores, and hyphens');
    }
    
    if (!/^[a-zA-Z]/.test(username)) {
      result.valid = false;
      result.errors.push('Username must start with a letter');
    }
    
    return result;
  } catch (error) {
    console.error('Error validating username:', error);
    return {
      valid: false,
      errors: ['Validation error occurred'],
    };
  }
};

/**
 * Validate JSON string
 * @param {string} jsonString - JSON string to validate
 * @returns {Object} Validation result
 */
export const validateJson = (jsonString) => {
  try {
    if (typeof jsonString !== 'string') {
      return {
        valid: false,
        errors: ['Input must be a string'],
      };
    }
    
    JSON.parse(jsonString);
    return {
      valid: true,
      errors: [],
    };
  } catch (error) {
    return {
      valid: false,
      errors: [`Invalid JSON: ${error.message}`],
    };
  }
};

/**
 * Validate required fields
 * @param {Object} data - Data object to validate
 * @param {Array} requiredFields - Array of required field names
 * @returns {Object} Validation result
 */
export const validateRequiredFields = (data, requiredFields) => {
  try {
    const result = {
      valid: true,
      errors: [],
    };
    
    if (typeof data !== 'object' || data === null) {
      result.valid = false;
      result.errors.push('Data must be an object');
      return result;
    }
    
    for (const field of requiredFields) {
      if (!(field in data) || data[field] === null || data[field] === undefined || data[field] === '') {
        result.valid = false;
        result.errors.push(`Required field '${field}' is missing or empty`);
      }
    }
    
    return result;
  } catch (error) {
    console.error('Error validating required fields:', error);
    return {
      valid: false,
      errors: ['Validation error occurred'],
    };
  }
};

/**
 * Validate data types
 * @param {Object} data - Data object to validate
 * @param {Object} fieldTypes - Object mapping field names to expected types
 * @returns {Object} Validation result
 */
export const validateDataTypes = (data, fieldTypes) => {
  try {
    const result = {
      valid: true,
      errors: [],
    };
    
    if (typeof data !== 'object' || data === null) {
      result.valid = false;
      result.errors.push('Data must be an object');
      return result;
    }
    
    for (const [field, expectedType] of Object.entries(fieldTypes)) {
      if (field in data) {
        const actualType = typeof data[field];
        if (actualType !== expectedType) {
          result.valid = false;
          result.errors.push(`Field '${field}' must be of type ${expectedType}, got ${actualType}`);
        }
      }
    }
    
    return result;
  } catch (error) {
    console.error('Error validating data types:', error);
    return {
      valid: false,
      errors: ['Validation error occurred'],
    };
  }
};

/**
 * Validate string length
 * @param {string} value - String to validate
 * @param {Object} options - Validation options
 * @returns {Object} Validation result
 */
export const validateStringLength = (value, options = {}) => {
  try {
    const {
      minLength = 0,
      maxLength = null,
    } = options;
    
    const result = {
      valid: true,
      errors: [],
    };
    
    if (typeof value !== 'string') {
      result.valid = false;
      result.errors.push('Value must be a string');
      return result;
    }
    
    if (value.length < minLength) {
      result.valid = false;
      result.errors.push(`String must be at least ${minLength} characters long`);
    }
    
    if (maxLength !== null && value.length > maxLength) {
      result.valid = false;
      result.errors.push(`String must be no more than ${maxLength} characters long`);
    }
    
    return result;
  } catch (error) {
    console.error('Error validating string length:', error);
    return {
      valid: false,
      errors: ['Validation error occurred'],
    };
  }
};

/**
 * Validate numeric range
 * @param {number} value - Number to validate
 * @param {Object} options - Validation options
 * @returns {Object} Validation result
 */
export const validateNumericRange = (value, options = {}) => {
  try {
    const {
      min = null,
      max = null,
    } = options;
    
    const result = {
      valid: true,
      errors: [],
    };
    
    if (typeof value !== 'number' || isNaN(value)) {
      result.valid = false;
      result.errors.push('Value must be a number');
      return result;
    }
    
    if (min !== null && value < min) {
      result.valid = false;
      result.errors.push(`Value must be at least ${min}`);
    }
    
    if (max !== null && value > max) {
      result.valid = false;
      result.errors.push(`Value must be no more than ${max}`);
    }
    
    return result;
  } catch (error) {
    console.error('Error validating numeric range:', error);
    return {
      valid: false,
      errors: ['Validation error occurred'],
    };
  }
};

/**
 * Validate array length
 * @param {Array} value - Array to validate
 * @param {Object} options - Validation options
 * @returns {Object} Validation result
 */
export const validateArrayLength = (value, options = {}) => {
  try {
    const {
      minLength = 0,
      maxLength = null,
    } = options;
    
    const result = {
      valid: true,
      errors: [],
    };
    
    if (!Array.isArray(value)) {
      result.valid = false;
      result.errors.push('Value must be an array');
      return result;
    }
    
    if (value.length < minLength) {
      result.valid = false;
      result.errors.push(`Array must have at least ${minLength} items`);
    }
    
    if (maxLength !== null && value.length > maxLength) {
      result.valid = false;
      result.errors.push(`Array must have no more than ${maxLength} items`);
    }
    
    return result;
  } catch (error) {
    console.error('Error validating array length:', error);
    return {
      valid: false,
      errors: ['Validation error occurred'],
    };
  }
};

/**
 * Sanitize input string
 * @param {string} input - Input string to sanitize
 * @param {Object} options - Sanitization options
 * @returns {string} Sanitized string
 */
export const sanitizeInput = (input, options = {}) => {
  try {
    const {
      maxLength = null,
      removeHtml = true,
      trimWhitespace = true,
    } = options;
    
    if (typeof input !== 'string') return '';
    
    let sanitized = input;
    
    if (removeHtml) {
      sanitized = sanitized.replace(/<[^>]*>/g, '');
    }
    
    if (trimWhitespace) {
      sanitized = sanitized.trim();
    }
    
    if (maxLength !== null) {
      sanitized = sanitized.substring(0, maxLength);
    }
    
    return sanitized;
  } catch (error) {
    console.error('Error sanitizing input:', error);
    return '';
  }
};

/**
 * Validate scraper configuration
 * @param {Object} config - Scraper configuration to validate
 * @returns {Object} Validation result
 */
export const validateScraperConfig = (config) => {
  try {
    const result = {
      valid: true,
      errors: [],
    };
    
    if (typeof config !== 'object' || config === null) {
      result.valid = false;
      result.errors.push('Configuration must be an object');
      return result;
    }
    
    // Check required fields
    const requiredFields = ['name', 'url', 'selectors'];
    const requiredResult = validateRequiredFields(config, requiredFields);
    if (!requiredResult.valid) {
      result.valid = false;
      result.errors.push(...requiredResult.errors);
    }
    
    // Validate URL
    if (config.url && !validateUrl(config.url)) {
      result.valid = false;
      result.errors.push('Invalid URL format');
    }
    
    // Validate selectors
    if (config.selectors) {
      if (typeof config.selectors !== 'object' || Array.isArray(config.selectors)) {
        result.valid = false;
        result.errors.push('Selectors must be an object');
      } else if (Object.keys(config.selectors).length === 0) {
        result.valid = false;
        result.errors.push('At least one selector must be defined');
      }
    }
    
    // Validate delay
    if (config.delay !== undefined) {
      const delayResult = validateNumericRange(config.delay, { min: 0, max: 60 });
      if (!delayResult.valid) {
        result.valid = false;
        result.errors.push(...delayResult.errors);
      }
    }
    
    return result;
  } catch (error) {
    console.error('Error validating scraper config:', error);
    return {
      valid: false,
      errors: ['Validation error occurred'],
    };
  }
};
