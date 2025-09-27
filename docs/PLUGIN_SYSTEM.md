# SPIDER Plugin System

The SPIDER framework includes a comprehensive plugin system that allows developers to extend functionality through custom plugins. This document provides a complete guide to creating, managing, and using plugins in SPIDER.

## Table of Contents

- [Overview](#overview)
- [Plugin Architecture](#plugin-architecture)
- [Plugin Types](#plugin-types)
- [Creating Plugins](#creating-plugins)
- [Plugin Lifecycle](#plugin-lifecycle)
- [Configuration](#configuration)
- [Plugin Management](#plugin-management)
- [Security](#security)
- [Examples](#examples)
- [Best Practices](#best-practices)

## Overview

The SPIDER plugin system provides:

- **Extensibility**: Add custom functionality without modifying core code
- **Type Safety**: Strongly typed plugin interfaces
- **Lifecycle Management**: Automatic plugin loading, initialization, and cleanup
- **Dependency Resolution**: Automatic handling of plugin dependencies
- **Security**: Sandboxed execution and access controls
- **Monitoring**: Performance tracking and usage analytics
- **Hot Reloading**: Dynamic plugin loading and unloading

## Plugin Architecture

### Core Components

1. **Plugin Base Class**: Abstract base class for all plugins
2. **Plugin Registry**: Manages plugin registration and discovery
3. **Plugin Manager**: Handles plugin lifecycle and execution
4. **Plugin Types**: Specialized interfaces for different functionality

### Plugin Structure

```
spider/plugins/
├── __init__.py          # Plugin system exports
├── base.py              # Core plugin architecture
├── extractor.py         # Data extraction plugins
├── processor.py         # Data processing plugins
├── engine.py            # Scraping engine plugins
├── monitor.py           # Monitoring plugins
├── middleware.py        # Request/response middleware
├── validator.py         # Data validation plugins
├── storage.py           # Storage backend plugins
├── auth.py              # Authentication plugins
├── rate_limiter.py      # Rate limiting plugins
├── proxy.py             # Proxy management plugins
├── captcha.py           # CAPTCHA solving plugins
├── behavior.py          # Behavior simulation plugins (legacy)
├── behavior_simulation.py  # Advanced behavior simulation
├── fingerprint.py       # Browser fingerprint plugins
├── cache.py             # Caching plugins
├── notification.py      # Notification plugins
├── reporting.py         # Reporting plugins
├── compliance.py        # Compliance plugins
├── security.py          # Security plugins
├── analytics.py         # Analytics plugins
└── ai.py                # AI/ML plugins
```

## Plugin Types

### 1. Extractor Plugins

Extract data from various sources and formats.

**Base Class**: `ExtractorPlugin`
**Specialized Classes**: `HTMLExtractorPlugin`, `JSONExtractorPlugin`, `TextExtractorPlugin`

```python
from spider.plugins.extractor import HTMLExtractorPlugin

class MyHTMLExtractor(HTMLExtractorPlugin):
    async def extract(self, data, context=None):
        # Extract data from HTML
        return extracted_data
```

### 2. Processor Plugins

Transform, clean, and process data.

**Base Class**: `ProcessorPlugin`
**Specialized Classes**: `DataCleanerPlugin`, `DataTransformerPlugin`, `DataValidatorPlugin`

```python
from spider.plugins.processor import DataCleanerPlugin

class MyDataCleaner(DataCleanerPlugin):
    async def process(self, data, context=None):
        # Clean and process data
        return cleaned_data
```

### 3. Engine Plugins

Provide different scraping engines and execution backends.

**Base Class**: `EnginePlugin`
**Specialized Classes**: `WebScrapingEnginePlugin`, `APIScrapingEnginePlugin`

```python
from spider.plugins.engine import WebScrapingEnginePlugin

class MyWebEngine(WebScrapingEnginePlugin):
    async def execute(self, task, context=None):
        # Execute scraping task
        return result
```

### 4. Monitor Plugins

Provide monitoring and observability capabilities.

**Base Class**: `MonitorPlugin`

```python
from spider.plugins.monitor import MonitorPlugin

class MyMonitor(MonitorPlugin):
    async def collect_metrics(self, context=None):
        # Collect monitoring metrics
        return metrics
```

### 5. Middleware Plugins

Intercept and modify requests/responses in the processing pipeline.

**Base Class**: `MiddlewarePlugin`

```python
from spider.plugins.middleware import MiddlewarePlugin

class MyMiddleware(MiddlewarePlugin):
    async def process_request(self, request, context=None):
        # Process incoming request
        return modified_request
    
    async def process_response(self, response, context=None):
        # Process outgoing response
        return modified_response
```

## Creating Plugins

### 1. Basic Plugin Structure

```python
from spider.plugins.base import Plugin, PluginMetadata, PluginType
from typing import Any, Dict, Optional

class MyPlugin(Plugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="MyPlugin",
            version="1.0.0",
            description="My custom plugin",
            author="Your Name",
            plugin_type=PluginType.EXTRACTOR,
            dependencies=["OtherPlugin"],
            requirements=["requests>=2.25.0"],
            config_schema=self._get_config_schema(),
            tags=["custom", "example"]
        )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        return "enabled" in config
    
    async def _initialize(self) -> None:
        # Plugin-specific initialization
        pass
    
    async def _start(self) -> None:
        # Plugin-specific start logic
        pass
    
    async def _stop(self) -> None:
        # Plugin-specific stop logic
        pass
    
    async def _cleanup(self) -> None:
        # Plugin-specific cleanup
        pass
```

### 2. Plugin Metadata

The `PluginMetadata` class provides comprehensive information about your plugin:

```python
PluginMetadata(
    name="PluginName",                    # Unique plugin name
    version="1.0.0",                     # Semantic version
    description="Plugin description",    # Human-readable description
    author="Author Name",                # Plugin author
    plugin_type=PluginType.EXTRACTOR,   # Plugin type
    dependencies=["Plugin1", "Plugin2"], # Required plugins
    requirements=["requests>=2.25.0"],   # Python package requirements
    config_schema={...},                 # Configuration schema
    tags=["tag1", "tag2"],              # Searchable tags
    min_spider_version="1.0.0",         # Minimum SPIDER version
    max_spider_version="*",             # Maximum SPIDER version
    license="MIT",                       # License type
    homepage="https://example.com",      # Plugin homepage
    repository="https://github.com/...", # Source repository
    documentation="https://docs.example.com", # Documentation URL
    changelog="https://changelog.example.com" # Changelog URL
)
```

### 3. Configuration Schema

Define a JSON schema for your plugin configuration:

```python
def _get_config_schema(self) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "enabled": {"type": "boolean", "default": True},
            "timeout": {"type": "number", "default": 30},
            "retry_attempts": {"type": "integer", "default": 3},
            "custom_setting": {"type": "string", "default": "value"}
        },
        "required": ["enabled"]
    }
```

## Plugin Lifecycle

### 1. Loading Phase

1. **Discovery**: Plugin files are discovered in configured directories
2. **Registration**: Plugins are registered in the plugin registry
3. **Validation**: Plugin metadata and configuration are validated
4. **Dependency Check**: Plugin dependencies are verified

### 2. Initialization Phase

1. **Instance Creation**: Plugin instance is created with configuration
2. **Config Validation**: Plugin configuration is validated
3. **Dependency Loading**: Required plugins are loaded and started
4. **Plugin Initialize**: Plugin's `_initialize()` method is called

### 3. Execution Phase

1. **Plugin Start**: Plugin's `_start()` method is called
2. **Active State**: Plugin is ready to handle requests
3. **Metrics Collection**: Performance and usage metrics are tracked

### 4. Cleanup Phase

1. **Plugin Stop**: Plugin's `_stop()` method is called
2. **Resource Cleanup**: Plugin's `_cleanup()` method is called
3. **Dependency Cleanup**: Dependent plugins are stopped
4. **Unloading**: Plugin is removed from memory

## Configuration

### Plugin System Configuration

```yaml
plugins:
  enabled: true
  auto_discovery: true
  plugin_directories:
    - "plugins"
    - "examples/plugins"
    - "custom_plugins"
  
  loading:
    max_plugins: 100
    load_timeout: 30
    dependency_resolution: true
    auto_load_tags: ["auto_load", "essential"]
  
  execution:
    max_concurrent_plugins: 10
    execution_timeout: 300
    retry_attempts: 3
    error_handling: "continue"  # continue, stop, retry
  
  monitoring:
    track_performance: true
    track_usage: true
    performance_threshold: 5.0
    usage_threshold: 1000
  
  security:
    sandbox_plugins: true
    restrict_file_access: true
    allowed_imports: ["spider", "asyncio", "json", "datetime"]
    blocked_imports: ["os", "subprocess", "sys"]
  
  registry:
    cache_metadata: true
    validate_plugins: true
    check_dependencies: true
    version_compatibility: true
```

### Plugin Configuration

```yaml
my_plugin:
  enabled: true
  timeout: 30
  retry_attempts: 3
  custom_setting: "value"
```

## Plugin Management

### 1. Programmatic Management

```python
from spider.plugins.base import PluginManager, PluginRegistry

# Create plugin manager
registry = PluginRegistry()
manager = PluginManager(registry)

# Load and start a plugin
await manager.load_plugin("MyPlugin", {"enabled": True})
await manager.start_plugin("MyPlugin")

# Get plugin instance
plugin = await manager.get_plugin("MyPlugin")

# Stop and unload plugin
await manager.stop_plugin("MyPlugin")
await manager.unload_plugin("MyPlugin")
```

### 2. Auto-Discovery

Plugins are automatically discovered from configured directories:

```python
# Load all plugins from directory
loaded_plugins = await manager.load_plugins_from_directory(Path("plugins"))
```

### 3. Plugin Registry

```python
# Register a plugin
registry.register(MyPlugin, metadata)

# Search plugins
results = registry.search_plugins("html extractor")

# Get plugins by type
extractors = registry.get_plugins_by_type(PluginType.EXTRACTOR)
```

## Security

### 1. Sandboxing

Plugins run in a sandboxed environment with restricted access:

- **File System**: Limited access to specific directories
- **Network**: Controlled network access
- **Imports**: Whitelist of allowed modules
- **Resources**: Memory and CPU limits

### 2. Access Controls

```python
# Security configuration
security:
  sandbox_plugins: true
  restrict_file_access: true
  allowed_imports: ["spider", "asyncio", "json"]
  blocked_imports: ["os", "subprocess", "sys"]
```

### 3. Validation

- **Code Validation**: Plugin code is validated before execution
- **Dependency Check**: Dependencies are verified for security
- **Configuration Validation**: Plugin configurations are validated
- **Version Compatibility**: Plugin versions are checked for compatibility

## Examples

### 1. HTML Extractor Plugin

```python
from spider.plugins.extractor import HTMLExtractorPlugin
from bs4 import BeautifulSoup

class SimpleHTMLExtractor(HTMLExtractorPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="SimpleHTMLExtractor",
            version="1.0.0",
            description="Simple HTML extractor",
            author="SPIDER Framework",
            plugin_type=PluginType.EXTRACTOR
        )
    
    async def extract(self, data, context=None):
        soup = BeautifulSoup(data, 'html.parser')
        return {
            "title": soup.find('title').get_text() if soup.find('title') else None,
            "headings": [h.get_text() for h in soup.find_all(['h1', 'h2', 'h3'])],
            "links": [a['href'] for a in soup.find_all('a', href=True)]
        }
```

### 2. Data Cleaner Plugin

```python
from spider.plugins.processor import DataCleanerPlugin
import re

class TextCleaner(DataCleanerPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="TextCleaner",
            version="1.0.0",
            description="Text cleaning plugin",
            author="SPIDER Framework",
            plugin_type=PluginType.PROCESSOR
        )
    
    async def process(self, data, context=None):
        if isinstance(data, str):
            # Remove extra whitespace
            data = re.sub(r'\s+', ' ', data).strip()
            # Remove control characters
            data = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', data)
        return data
```

### 3. Custom Monitor Plugin

```python
from spider.plugins.monitor import MonitorPlugin
import psutil

class SystemMonitor(MonitorPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="SystemMonitor",
            version="1.0.0",
            description="System resource monitor",
            author="SPIDER Framework",
            plugin_type=PluginType.MONITOR
        )
    
    async def collect_metrics(self, context=None):
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
```

## Best Practices

### 1. Plugin Design

- **Single Responsibility**: Each plugin should have one clear purpose
- **Stateless**: Avoid storing state between calls when possible
- **Error Handling**: Implement robust error handling and recovery
- **Resource Management**: Properly manage resources and cleanup

### 2. Configuration

- **Sensible Defaults**: Provide reasonable default values
- **Validation**: Validate all configuration parameters
- **Documentation**: Document all configuration options
- **Type Safety**: Use proper type hints and validation

### 3. Performance

- **Async Operations**: Use async/await for I/O operations
- **Caching**: Cache expensive operations when appropriate
- **Resource Limits**: Respect memory and CPU limits
- **Metrics**: Record performance metrics for monitoring

### 4. Security

- **Input Validation**: Validate all inputs thoroughly
- **Output Sanitization**: Sanitize outputs to prevent injection
- **Access Control**: Follow principle of least privilege
- **Audit Logging**: Log important operations for auditing

### 5. Testing

- **Unit Tests**: Write comprehensive unit tests
- **Integration Tests**: Test plugin integration with SPIDER
- **Error Cases**: Test error conditions and edge cases
- **Performance Tests**: Test performance under load

### 6. Documentation

- **README**: Provide clear usage instructions
- **API Documentation**: Document all public methods
- **Examples**: Include practical usage examples
- **Changelog**: Maintain a changelog for version updates

## Troubleshooting

### Common Issues

1. **Plugin Not Loading**: Check plugin metadata and dependencies
2. **Configuration Errors**: Validate configuration against schema
3. **Import Errors**: Ensure all dependencies are installed
4. **Permission Errors**: Check file system permissions
5. **Performance Issues**: Monitor resource usage and optimize

### Debug Mode

Enable debug mode for detailed plugin information:

```yaml
environment: development
debug: true
```

### Logging

Plugin system logs are available at:

```
logs/plugin_system.log
```

## Conclusion

The SPIDER plugin system provides a powerful and flexible way to extend the framework's functionality. By following the guidelines and best practices outlined in this document, you can create robust, secure, and maintainable plugins that integrate seamlessly with the SPIDER ecosystem.

For more information, see the [API Reference](API_REFERENCE.md) and [Examples](EXAMPLES.md) documentation.
