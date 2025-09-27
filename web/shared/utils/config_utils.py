"""
SPIDER Framework - Configuration Utilities

Utility functions for configuration management.
"""

import os
import json
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

def get_api_config() -> Dict[str, Any]:
    """
    Get API configuration from environment variables.
    
    Returns:
        API configuration dictionary
    """
    try:
        return {
            'base_url': os.getenv('API_BASE_URL', 'http://localhost:8000'),
            'timeout': int(os.getenv('API_TIMEOUT', '30')),
            'retry_attempts': int(os.getenv('API_RETRY_ATTEMPTS', '3')),
            'retry_delay': float(os.getenv('API_RETRY_DELAY', '1.0')),
            'max_retry_delay': float(os.getenv('API_MAX_RETRY_DELAY', '60.0')),
            'backoff_factor': float(os.getenv('API_BACKOFF_FACTOR', '2.0'))
        }
    
    except Exception as e:
        logger.error(f"Error getting API config: {str(e)}")
        return {
            'base_url': 'http://localhost:8000',
            'timeout': 30,
            'retry_attempts': 3,
            'retry_delay': 1.0,
            'max_retry_delay': 60.0,
            'backoff_factor': 2.0
        }

def get_ui_config() -> Dict[str, Any]:
    """
    Get UI configuration from environment variables.
    
    Returns:
        UI configuration dictionary
    """
    try:
        return {
            'theme': os.getenv('UI_THEME', 'light'),
            'language': os.getenv('UI_LANGUAGE', 'en'),
            'timezone': os.getenv('UI_TIMEZONE', 'UTC'),
            'date_format': os.getenv('UI_DATE_FORMAT', '%Y-%m-%d %H:%M:%S'),
            'items_per_page': int(os.getenv('UI_ITEMS_PER_PAGE', '20')),
            'max_items_per_page': int(os.getenv('UI_MAX_ITEMS_PER_PAGE', '100')),
            'auto_refresh_interval': int(os.getenv('UI_AUTO_REFRESH_INTERVAL', '30')),
            'show_debug_info': os.getenv('UI_SHOW_DEBUG_INFO', 'false').lower() == 'true'
        }
    
    except Exception as e:
        logger.error(f"Error getting UI config: {str(e)}")
        return {
            'theme': 'light',
            'language': 'en',
            'timezone': 'UTC',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'items_per_page': 20,
            'max_items_per_page': 100,
            'auto_refresh_interval': 30,
            'show_debug_info': False
        }

def get_feature_flags() -> Dict[str, bool]:
    """
    Get feature flags from environment variables.
    
    Returns:
        Feature flags dictionary
    """
    try:
        return {
            'ai_enabled': os.getenv('FEATURE_AI_ENABLED', 'true').lower() == 'true',
            'real_time_monitoring': os.getenv('FEATURE_REAL_TIME_MONITORING', 'true').lower() == 'true',
            'advanced_analytics': os.getenv('FEATURE_ADVANCED_ANALYTICS', 'true').lower() == 'true',
            'multi_tenant': os.getenv('FEATURE_MULTI_TENANT', 'true').lower() == 'true',
            'enterprise_features': os.getenv('FEATURE_ENTERPRISE_FEATURES', 'true').lower() == 'true',
            'api_documentation': os.getenv('FEATURE_API_DOCUMENTATION', 'true').lower() == 'true',
            'webhook_support': os.getenv('FEATURE_WEBHOOK_SUPPORT', 'true').lower() == 'true',
            'scheduled_scraping': os.getenv('FEATURE_SCHEDULED_SCRAPING', 'true').lower() == 'true'
        }
    
    except Exception as e:
        logger.error(f"Error getting feature flags: {str(e)}")
        return {
            'ai_enabled': True,
            'real_time_monitoring': True,
            'advanced_analytics': True,
            'multi_tenant': True,
            'enterprise_features': True,
            'api_documentation': True,
            'webhook_support': True,
            'scheduled_scraping': True
        }

def is_development() -> bool:
    """
    Check if running in development mode.
    
    Returns:
        True if development mode, False otherwise
    """
    try:
        return os.getenv('ENVIRONMENT', 'development').lower() in ['development', 'dev', 'local']
    
    except Exception as e:
        logger.error(f"Error checking development mode: {str(e)}")
        return True

def is_production() -> bool:
    """
    Check if running in production mode.
    
    Returns:
        True if production mode, False otherwise
    """
    try:
        return os.getenv('ENVIRONMENT', 'development').lower() in ['production', 'prod']
    
    except Exception as e:
        logger.error(f"Error checking production mode: {str(e)}")
        return False

def get_environment() -> str:
    """
    Get current environment.
    
    Returns:
        Environment name
    """
    try:
        return os.getenv('ENVIRONMENT', 'development').lower()
    
    except Exception as e:
        logger.error(f"Error getting environment: {str(e)}")
        return 'development'

def get_log_level() -> str:
    """
    Get log level from environment.
    
    Returns:
        Log level
    """
    try:
        return os.getenv('LOG_LEVEL', 'INFO').upper()
    
    except Exception as e:
        logger.error(f"Error getting log level: {str(e)}")
        return 'INFO'

def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration from environment variables.
    
    Returns:
        Database configuration dictionary
    """
    try:
        return {
            'url': os.getenv('DATABASE_URL', 'sqlite:///spider.db'),
            'pool_size': int(os.getenv('DATABASE_POOL_SIZE', '20')),
            'max_overflow': int(os.getenv('DATABASE_MAX_OVERFLOW', '30')),
            'pool_timeout': int(os.getenv('DATABASE_POOL_TIMEOUT', '30')),
            'pool_recycle': int(os.getenv('DATABASE_POOL_RECYCLE', '3600')),
            'echo': os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
        }
    
    except Exception as e:
        logger.error(f"Error getting database config: {str(e)}")
        return {
            'url': 'sqlite:///spider.db',
            'pool_size': 20,
            'max_overflow': 30,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'echo': False
        }

def get_redis_config() -> Dict[str, Any]:
    """
    Get Redis configuration from environment variables.
    
    Returns:
        Redis configuration dictionary
    """
    try:
        return {
            'url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
            'cluster_mode': os.getenv('REDIS_CLUSTER_MODE', 'false').lower() == 'true',
            'decode_responses': os.getenv('REDIS_DECODE_RESPONSES', 'true').lower() == 'true',
            'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', '100')),
            'retry_on_timeout': os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true',
            'socket_keepalive': os.getenv('REDIS_SOCKET_KEEPALIVE', 'true').lower() == 'true'
        }
    
    except Exception as e:
        logger.error(f"Error getting Redis config: {str(e)}")
        return {
            'url': 'redis://localhost:6379',
            'cluster_mode': False,
            'decode_responses': True,
            'max_connections': 100,
            'retry_on_timeout': True,
            'socket_keepalive': True
        }

def get_security_config() -> Dict[str, Any]:
    """
    Get security configuration from environment variables.
    
    Returns:
        Security configuration dictionary
    """
    try:
        return {
            'secret_key': os.getenv('SECRET_KEY', 'your-secret-key-here'),
            'jwt_secret': os.getenv('JWT_SECRET', 'your-jwt-secret-here'),
            'encryption_key': os.getenv('ENCRYPTION_KEY', 'your-encryption-key-here'),
            'session_timeout': int(os.getenv('SESSION_TIMEOUT', '3600')),
            'password_min_length': int(os.getenv('PASSWORD_MIN_LENGTH', '8')),
            'password_require_special': os.getenv('PASSWORD_REQUIRE_SPECIAL', 'true').lower() == 'true',
            'rate_limiting_enabled': os.getenv('RATE_LIMITING_ENABLED', 'true').lower() == 'true',
            'rate_limit_requests_per_minute': int(os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', '100')),
            'rate_limit_burst_size': int(os.getenv('RATE_LIMIT_BURST_SIZE', '200'))
        }
    
    except Exception as e:
        logger.error(f"Error getting security config: {str(e)}")
        return {
            'secret_key': 'your-secret-key-here',
            'jwt_secret': 'your-jwt-secret-here',
            'encryption_key': 'your-encryption-key-here',
            'session_timeout': 3600,
            'password_min_length': 8,
            'password_require_special': True,
            'rate_limiting_enabled': True,
            'rate_limit_requests_per_minute': 100,
            'rate_limit_burst_size': 200
        }

def get_monitoring_config() -> Dict[str, Any]:
    """
    Get monitoring configuration from environment variables.
    
    Returns:
        Monitoring configuration dictionary
    """
    try:
        return {
            'prometheus_enabled': os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true',
            'prometheus_port': int(os.getenv('PROMETHEUS_PORT', '9090')),
            'grafana_url': os.getenv('GRAFANA_URL', 'http://localhost:3000'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_format': os.getenv('LOG_FORMAT', 'json'),
            'log_file': os.getenv('LOG_FILE', '/var/log/spider/spider.log'),
            'max_log_size': os.getenv('MAX_LOG_SIZE', '100MB'),
            'max_log_files': int(os.getenv('MAX_LOG_FILES', '10')),
            'compress_logs': os.getenv('COMPRESS_LOGS', 'true').lower() == 'true'
        }
    
    except Exception as e:
        logger.error(f"Error getting monitoring config: {str(e)}")
        return {
            'prometheus_enabled': True,
            'prometheus_port': 9090,
            'grafana_url': 'http://localhost:3000',
            'log_level': 'INFO',
            'log_format': 'json',
            'log_file': '/var/log/spider/spider.log',
            'max_log_size': '100MB',
            'max_log_files': 10,
            'compress_logs': True
        }

def load_config_file(file_path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        file_path: Path to configuration file
    
    Returns:
        Configuration dictionary
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    
    except FileNotFoundError:
        logger.warning(f"Configuration file not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing configuration file {file_path}: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Error loading configuration file {file_path}: {str(e)}")
        return {}

def save_config_file(config: Dict[str, Any], file_path: str) -> bool:
    """
    Save configuration to JSON file.
    
    Args:
        config: Configuration dictionary
        file_path: Path to configuration file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    
    except Exception as e:
        logger.error(f"Error saving configuration file {file_path}: {str(e)}")
        return False

def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple configuration dictionaries.
    
    Args:
        *configs: Configuration dictionaries to merge
    
    Returns:
        Merged configuration dictionary
    """
    try:
        merged = {}
        for config in configs:
            merged.update(config)
        return merged
    
    except Exception as e:
        logger.error(f"Error merging configurations: {str(e)}")
        return {}

def get_config_value(key: str, default: Any = None, config: Dict[str, Any] = None) -> Any:
    """
    Get configuration value by key with dot notation support.
    
    Args:
        key: Configuration key (supports dot notation)
        default: Default value if key not found
        config: Configuration dictionary (optional)
    
    Returns:
        Configuration value
    """
    try:
        if config is None:
            config = {}
        
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    except Exception as e:
        logger.error(f"Error getting config value for key {key}: {str(e)}")
        return default
