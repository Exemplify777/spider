"""Configuration management for SPIDER framework."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(default="sqlite:///data/spider.db", description="Database connection URL")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")
    echo: bool = Field(default=False, description="Enable SQL echo")


class RedisConfig(BaseModel):
    """Redis configuration."""
    url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    db: int = Field(default=0, description="Redis database number")
    max_connections: int = Field(default=100, description="Max Redis connections")


class ProxyConfig(BaseModel):
    """Proxy configuration."""
    enabled: bool = Field(default=True, description="Enable proxy rotation")
    providers: list[str] = Field(default_factory=list, description="Proxy providers")
    rotation_interval: int = Field(default=300, description="Rotation interval in seconds")
    health_check_interval: int = Field(default=60, description="Health check interval in seconds")


class CAPTCHAConfig(BaseModel):
    """CAPTCHA solving configuration."""
    enabled: bool = Field(default=True, description="Enable CAPTCHA solving")
    providers: list[str] = Field(default_factory=list, description="CAPTCHA providers")
    timeout: int = Field(default=120, description="CAPTCHA solving timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    enabled: bool = Field(default=True, description="Enable monitoring")
    prometheus_port: int = Field(default=8000, description="Prometheus metrics port")
    health_check_port: int = Field(default=8001, description="Health check port")
    log_level: str = Field(default="INFO", description="Log level")


class PluginLoadingConfig(BaseModel):
    """Plugin loading configuration."""
    max_plugins: int = Field(default=100, description="Maximum number of plugins to load")
    load_timeout: int = Field(default=30, description="Plugin loading timeout in seconds")
    dependency_resolution: bool = Field(default=True, description="Enable dependency resolution")
    auto_load_tags: list[str] = Field(default_factory=lambda: ["auto_load", "essential"], description="Tags for auto-loading plugins")


class PluginExecutionConfig(BaseModel):
    """Plugin execution configuration."""
    max_concurrent_plugins: int = Field(default=10, description="Maximum concurrent plugin executions")
    execution_timeout: int = Field(default=300, description="Plugin execution timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts for failed plugins")
    error_handling: str = Field(default="continue", description="Error handling strategy: continue, stop, retry")


class PluginMonitoringConfig(BaseModel):
    """Plugin monitoring configuration."""
    track_performance: bool = Field(default=True, description="Track plugin performance metrics")
    track_usage: bool = Field(default=True, description="Track plugin usage statistics")
    performance_threshold: float = Field(default=5.0, description="Performance threshold in seconds")
    usage_threshold: int = Field(default=1000, description="Usage threshold per hour")


class PluginSecurityConfig(BaseModel):
    """Plugin security configuration."""
    sandbox_plugins: bool = Field(default=True, description="Enable plugin sandboxing")
    restrict_file_access: bool = Field(default=True, description="Restrict file system access")
    allowed_imports: list[str] = Field(default_factory=lambda: ["spider", "asyncio", "json", "datetime"], description="Allowed import modules")
    blocked_imports: list[str] = Field(default_factory=lambda: ["os", "subprocess", "sys"], description="Blocked import modules")


class PluginRegistryConfig(BaseModel):
    """Plugin registry configuration."""
    cache_metadata: bool = Field(default=True, description="Cache plugin metadata")
    validate_plugins: bool = Field(default=True, description="Validate plugins on registration")
    check_dependencies: bool = Field(default=True, description="Check plugin dependencies")
    version_compatibility: bool = Field(default=True, description="Check version compatibility")


class PluginConfig(BaseModel):
    """Plugin system configuration."""
    enabled: bool = Field(default=True, description="Enable plugin system")
    auto_discovery: bool = Field(default=True, description="Enable automatic plugin discovery")
    plugin_directories: list[str] = Field(default_factory=lambda: ["plugins", "examples/plugins", "custom_plugins"], description="Plugin directories to scan")
    loading: PluginLoadingConfig = Field(default_factory=PluginLoadingConfig)
    execution: PluginExecutionConfig = Field(default_factory=PluginExecutionConfig)
    monitoring: PluginMonitoringConfig = Field(default_factory=PluginMonitoringConfig)
    security: PluginSecurityConfig = Field(default_factory=PluginSecurityConfig)
    registry: PluginRegistryConfig = Field(default_factory=PluginRegistryConfig)


class EngineConfig(BaseModel):
    """Engine-specific configuration."""
    scrapy: Dict[str, Any] = Field(default_factory=dict, description="Scrapy configuration")
    playwright: Dict[str, Any] = Field(default_factory=dict, description="Playwright configuration")
    httpx: Dict[str, Any] = Field(default_factory=dict, description="HTTPX configuration")


class Config(BaseSettings):
    """Main configuration class for SPIDER."""
    
    # Environment
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Database
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # Redis
    redis: RedisConfig = Field(default_factory=RedisConfig)
    
    # Proxy
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    
    # CAPTCHA
    captcha: CAPTCHAConfig = Field(default_factory=CAPTCHAConfig)
    
    # Monitoring
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    # Plugin system
    plugins: PluginConfig = Field(default_factory=PluginConfig)
    
    # Engines
    engines: EngineConfig = Field(default_factory=EngineConfig)
    
    # Scraping settings
    max_concurrent_requests: int = Field(default=16, description="Max concurrent requests")
    request_delay: float = Field(default=1.0, description="Delay between requests in seconds")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    
    # Data storage
    data_dir: str = Field(default="data", description="Data directory")
    log_dir: str = Field(default="logs", description="Log directory")
    cache_dir: str = Field(default="cache", description="Cache directory")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_nested_delimiter = "__"
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment value."""
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v
    
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> "Config":
        """Load configuration from YAML file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        return cls(**config_data)
    
    def to_file(self, config_path: Union[str, Path]) -> None:
        """Save configuration to YAML file."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.dict(), f, default_flow_style=False, indent=2)
    
    def get_engine_config(self, engine_name: str) -> Dict[str, Any]:
        """Get configuration for specific engine."""
        engine_configs = {
            "scrapy": self.engines.scrapy,
            "playwright": self.engines.playwright,
            "httpx": self.engines.httpx,
        }
        
        if engine_name not in engine_configs:
            raise ValueError(f"Unknown engine: {engine_name}")
        
        return engine_configs[engine_name]
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
