"""
SPIDER Framework - Shared Utilities

This package contains utility functions and classes used across the SPIDER web interface.
"""

from .api_utils import (
    make_api_request,
    handle_api_response,
    format_api_error,
    get_api_headers,
    build_api_url,
    parse_api_response,
    validate_api_response,
    retry_api_request,
    get_api_timeout,
    get_api_retry_config
)

from .auth_utils import (
    get_auth_token,
    set_auth_token,
    clear_auth_token,
    is_authenticated,
    get_user_info,
    has_permission,
    check_role,
    get_user_roles,
    validate_token,
    refresh_token,
    logout_user
)

from .data_utils import (
    format_data,
    parse_data,
    validate_data,
    transform_data,
    filter_data,
    sort_data,
    paginate_data,
    search_data,
    aggregate_data,
    export_data,
    import_data,
    clean_data,
    normalize_data,
    deduplicate_data,
    merge_data,
    split_data,
    convert_data,
    validate_data_schema,
    get_data_summary,
    get_data_statistics
)

from .config_utils import (
    get_api_config,
    get_ui_config,
    get_feature_flags,
    is_development,
    is_production,
    get_environment,
    get_log_level,
    get_database_config,
    get_redis_config,
    get_security_config,
    get_monitoring_config,
    load_config_file,
    save_config_file,
    merge_configs,
    get_config_value
)

from .validation_utils import (
    validate_email,
    validate_password,
    validate_url,
    validate_phone,
    validate_username,
    validate_json,
    validate_required_fields,
    validate_data_types,
    validate_string_length,
    validate_numeric_range,
    validate_list_length,
    sanitize_input,
    validate_scraper_config
)

from .error_utils import (
    SPIDERError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ScrapingError,
    ConfigurationError,
    DatabaseError,
    NetworkError,
    RateLimitError,
    AIError,
    handle_exception,
    create_error_response,
    log_error,
    format_error_message,
    get_error_code,
    is_retryable_error,
    get_retry_delay,
    should_log_error,
    create_error_summary
)

from .security_utils import (
    generate_random_string,
    generate_api_key,
    hash_password,
    verify_password,
    generate_hmac_signature,
    verify_hmac_signature,
    sanitize_input,
    validate_input,
    escape_html,
    unescape_html,
    generate_csrf_token,
    validate_csrf_token,
    generate_secure_filename,
    validate_file_extension,
    check_password_strength
)

__all__ = [
    # API utilities
    'make_api_request',
    'handle_api_response',
    'format_api_error',
    'get_api_headers',
    'build_api_url',
    'parse_api_response',
    'validate_api_response',
    'retry_api_request',
    'get_api_timeout',
    'get_api_retry_config',
    
    # Authentication utilities
    'get_auth_token',
    'set_auth_token',
    'clear_auth_token',
    'is_authenticated',
    'get_user_info',
    'has_permission',
    'check_role',
    'get_user_roles',
    'validate_token',
    'refresh_token',
    'logout_user',
    
    # Data utilities
    'format_data',
    'parse_data',
    'validate_data',
    'transform_data',
    'filter_data',
    'sort_data',
    'paginate_data',
    'search_data',
    'aggregate_data',
    'export_data',
    'import_data',
    'clean_data',
    'normalize_data',
    'deduplicate_data',
    'merge_data',
    'split_data',
    'convert_data',
    'validate_data_schema',
    'get_data_summary',
    'get_data_statistics',
    
    # Configuration utilities
    'get_api_config',
    'get_ui_config',
    'get_feature_flags',
    'is_development',
    'is_production',
    'get_environment',
    'get_log_level',
    'get_database_config',
    'get_redis_config',
    'get_security_config',
    'get_monitoring_config',
    'load_config_file',
    'save_config_file',
    'merge_configs',
    'get_config_value',
    
    # Validation utilities
    'validate_email',
    'validate_password',
    'validate_url',
    'validate_phone',
    'validate_username',
    'validate_json',
    'validate_required_fields',
    'validate_data_types',
    'validate_string_length',
    'validate_numeric_range',
    'validate_list_length',
    'sanitize_input',
    'validate_scraper_config',
    
    # Error utilities
    'SPIDERError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'ScrapingError',
    'ConfigurationError',
    'DatabaseError',
    'NetworkError',
    'RateLimitError',
    'AIError',
    'handle_exception',
    'create_error_response',
    'log_error',
    'format_error_message',
    'get_error_code',
    'is_retryable_error',
    'get_retry_delay',
    'should_log_error',
    'create_error_summary',
    
    # Security utilities
    'generate_random_string',
    'generate_api_key',
    'hash_password',
    'verify_password',
    'generate_hmac_signature',
    'verify_hmac_signature',
    'sanitize_input',
    'validate_input',
    'escape_html',
    'unescape_html',
    'generate_csrf_token',
    'validate_csrf_token',
    'generate_secure_filename',
    'validate_file_extension',
    'check_password_strength'
]