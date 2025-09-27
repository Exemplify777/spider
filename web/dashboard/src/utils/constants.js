/**
 * SPIDER Framework - Constants
 * 
 * Application constants and configuration values.
 */

// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  TIMEOUT: parseInt(process.env.REACT_APP_API_TIMEOUT) || 30000,
  RETRY_ATTEMPTS: parseInt(process.env.REACT_APP_API_RETRY_ATTEMPTS) || 3,
  RETRY_DELAY: parseInt(process.env.REACT_APP_API_RETRY_DELAY) || 1000,
};

// Authentication
export const AUTH_CONFIG = {
  TOKEN_KEY: 'auth_token',
  REFRESH_TOKEN_KEY: 'refresh_token',
  USER_INFO_KEY: 'user_info',
  TOKEN_EXPIRY_BUFFER: 5 * 60 * 1000, // 5 minutes
};

// User Roles
export const USER_ROLES = {
  SUPER_ADMIN: 'super_admin',
  ADMIN: 'admin',
  USER: 'user',
  GUEST: 'guest',
};

// User Permissions
export const PERMISSIONS = {
  // Scraping permissions
  SCRAPING_CREATE: 'scraping:create',
  SCRAPING_READ: 'scraping:read',
  SCRAPING_UPDATE: 'scraping:update',
  SCRAPING_DELETE: 'scraping:delete',
  SCRAPING_EXECUTE: 'scraping:execute',
  
  // User management permissions
  USER_CREATE: 'user:create',
  USER_READ: 'user:read',
  USER_UPDATE: 'user:update',
  USER_DELETE: 'user:delete',
  
  // System permissions
  SYSTEM_READ: 'system:read',
  SYSTEM_UPDATE: 'system:update',
  SYSTEM_MONITOR: 'system:monitor',
  
  // AI permissions
  AI_USE: 'ai:use',
  AI_TRAIN: 'ai:train',
  AI_MANAGE: 'ai:manage',
  
  // Analytics permissions
  ANALYTICS_READ: 'analytics:read',
  ANALYTICS_EXPORT: 'analytics:export',
};

// Scraping Status
export const SCRAPING_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
  PAUSED: 'paused',
};

// Scraping Types
export const SCRAPING_TYPES = {
  STATIC: 'static',
  DYNAMIC: 'dynamic',
  API: 'api',
  FILE: 'file',
};

// Data Types
export const DATA_TYPES = {
  TEXT: 'text',
  HTML: 'html',
  JSON: 'json',
  XML: 'xml',
  CSV: 'csv',
  IMAGE: 'image',
  FILE: 'file',
};

// File Types
export const FILE_TYPES = {
  IMAGE: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'],
  DOCUMENT: ['pdf', 'doc', 'docx', 'txt', 'rtf'],
  SPREADSHEET: ['xls', 'xlsx', 'csv'],
  PRESENTATION: ['ppt', 'pptx'],
  ARCHIVE: ['zip', 'rar', '7z', 'tar', 'gz'],
};

// HTTP Status Codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  METHOD_NOT_ALLOWED: 405,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
  GATEWAY_TIMEOUT: 504,
};

// Error Types
export const ERROR_TYPES = {
  VALIDATION: 'validation',
  AUTHENTICATION: 'authentication',
  AUTHORIZATION: 'authorization',
  NETWORK: 'network',
  SERVER: 'server',
  CLIENT: 'client',
  UNKNOWN: 'unknown',
};

// UI Configuration
export const UI_CONFIG = {
  THEME: {
    LIGHT: 'light',
    DARK: 'dark',
  },
  LANGUAGE: {
    EN: 'en',
    ES: 'es',
    FR: 'fr',
    DE: 'de',
  },
  PAGINATION: {
    DEFAULT_PAGE_SIZE: 20,
    MAX_PAGE_SIZE: 100,
    PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
  },
  REFRESH_INTERVALS: {
    REAL_TIME: 5000, // 5 seconds
    FAST: 30000, // 30 seconds
    NORMAL: 60000, // 1 minute
    SLOW: 300000, // 5 minutes
  },
};

// Form Validation
export const VALIDATION_RULES = {
  EMAIL: {
    PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    MESSAGE: 'Please enter a valid email address',
  },
  PASSWORD: {
    MIN_LENGTH: 8,
    REQUIRE_UPPERCASE: true,
    REQUIRE_LOWERCASE: true,
    REQUIRE_NUMBERS: true,
    REQUIRE_SPECIAL_CHARS: true,
  },
  USERNAME: {
    MIN_LENGTH: 3,
    MAX_LENGTH: 20,
    PATTERN: /^[a-zA-Z][a-zA-Z0-9_-]*$/,
    MESSAGE: 'Username must start with a letter and contain only letters, numbers, underscores, and hyphens',
  },
  URL: {
    PATTERN: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/,
    MESSAGE: 'Please enter a valid URL',
  },
  PHONE: {
    PATTERN: /^[\+]?[1-9][\d]{0,15}$/,
    MESSAGE: 'Please enter a valid phone number',
  },
};

// Date Formats
export const DATE_FORMATS = {
  SHORT: 'MM/DD/YYYY',
  LONG: 'MMMM DD, YYYY',
  DATETIME: 'MM/DD/YYYY HH:mm:ss',
  ISO: 'YYYY-MM-DDTHH:mm:ss.SSSZ',
  RELATIVE: 'relative',
};

// Time Formats
export const TIME_FORMATS = {
  SHORT: 'HH:mm',
  LONG: 'HH:mm:ss',
  WITH_AMPM: 'h:mm A',
  WITH_AMPM_LONG: 'h:mm:ss A',
};

// Storage Keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_INFO: 'user_info',
  THEME: 'theme',
  LANGUAGE: 'language',
  PREFERENCES: 'preferences',
  CACHE: 'cache',
};

// Cache Configuration
export const CACHE_CONFIG = {
  TTL: {
    SHORT: 5 * 60 * 1000, // 5 minutes
    MEDIUM: 30 * 60 * 1000, // 30 minutes
    LONG: 60 * 60 * 1000, // 1 hour
    VERY_LONG: 24 * 60 * 60 * 1000, // 24 hours
  },
  MAX_SIZE: 50 * 1024 * 1024, // 50MB
  MAX_ITEMS: 1000,
};

// Notification Types
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
};

// Notification Positions
export const NOTIFICATION_POSITIONS = {
  TOP_LEFT: 'top-left',
  TOP_RIGHT: 'top-right',
  TOP_CENTER: 'top-center',
  BOTTOM_LEFT: 'bottom-left',
  BOTTOM_RIGHT: 'bottom-right',
  BOTTOM_CENTER: 'bottom-center',
};

// Chart Types
export const CHART_TYPES = {
  LINE: 'line',
  BAR: 'bar',
  PIE: 'pie',
  DOUGHNUT: 'doughnut',
  AREA: 'area',
  SCATTER: 'scatter',
  RADAR: 'radar',
  POLAR: 'polar',
};

// Export Formats
export const EXPORT_FORMATS = {
  JSON: 'json',
  CSV: 'csv',
  XLSX: 'xlsx',
  PDF: 'pdf',
  XML: 'xml',
  HTML: 'html',
};

// Import Formats
export const IMPORT_FORMATS = {
  JSON: 'json',
  CSV: 'csv',
  XLSX: 'xlsx',
  XML: 'xml',
  HTML: 'html',
};

// AI Model Types
export const AI_MODEL_TYPES = {
  CLASSIFICATION: 'classification',
  REGRESSION: 'regression',
  CLUSTERING: 'clustering',
  NLP: 'nlp',
  COMPUTER_VISION: 'computer_vision',
  RECOMMENDATION: 'recommendation',
  ANOMALY_DETECTION: 'anomaly_detection',
};

// AI Model Status
export const AI_MODEL_STATUS = {
  TRAINING: 'training',
  TRAINED: 'trained',
  DEPLOYED: 'deployed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
};

// Monitoring Metrics
export const MONITORING_METRICS = {
  CPU_USAGE: 'cpu_usage',
  MEMORY_USAGE: 'memory_usage',
  DISK_USAGE: 'disk_usage',
  NETWORK_USAGE: 'network_usage',
  REQUEST_COUNT: 'request_count',
  RESPONSE_TIME: 'response_time',
  ERROR_RATE: 'error_rate',
  THROUGHPUT: 'throughput',
};

// Alert Severity Levels
export const ALERT_SEVERITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical',
};

// Alert Status
export const ALERT_STATUS = {
  ACTIVE: 'active',
  ACKNOWLEDGED: 'acknowledged',
  RESOLVED: 'resolved',
  SUPPRESSED: 'suppressed',
};

// Feature Flags
export const FEATURE_FLAGS = {
  AI_ENABLED: 'ai_enabled',
  REAL_TIME_MONITORING: 'real_time_monitoring',
  ADVANCED_ANALYTICS: 'advanced_analytics',
  MULTI_TENANT: 'multi_tenant',
  ENTERPRISE_FEATURES: 'enterprise_features',
  API_DOCUMENTATION: 'api_documentation',
  WEBHOOK_SUPPORT: 'webhook_support',
  SCHEDULED_SCRAPING: 'scheduled_scraping',
};

// Default Values
export const DEFAULTS = {
  PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  REFRESH_INTERVAL: 30000,
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
  CACHE_TTL: 300000,
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  MAX_ITEMS_PER_PAGE: 100,
  DEBOUNCE_DELAY: 300,
  THROTTLE_DELAY: 1000,
};
