"""
Base Plugin System

This module defines the core plugin architecture and interfaces for the SPIDER framework.
"""

import asyncio
import importlib
import inspect
import json
import logging
import os
import sys
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, Callable, Set
from datetime import datetime, timedelta
import yaml

from ..core.exceptions import SpiderError


class PluginType(Enum):
    """Types of plugins supported by the system."""
    EXTRACTOR = "extractor"
    PROCESSOR = "processor"
    ENGINE = "engine"
    MONITOR = "monitor"
    MIDDLEWARE = "middleware"
    VALIDATOR = "validator"
    STORAGE = "storage"
    AUTH = "auth"
    RATE_LIMITER = "rate_limiter"
    PROXY = "proxy"
    CAPTCHA = "captcha"
    BEHAVIOR = "behavior"
    FINGERPRINT = "fingerprint"
    CACHE = "cache"
    NOTIFICATION = "notification"
    REPORTING = "reporting"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    ANALYTICS = "analytics"
    AI = "ai"


class PluginStatus(Enum):
    """Plugin lifecycle status."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginMetadata:
    """Plugin metadata and configuration."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    min_spider_version: str = "1.0.0"
    max_spider_version: str = "*"
    license: str = "MIT"
    homepage: str = ""
    repository: str = ""
    documentation: str = ""
    changelog: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PluginInfo:
    """Complete plugin information including metadata and runtime state."""
    metadata: PluginMetadata
    status: PluginStatus = PluginStatus.UNLOADED
    instance: Optional['Plugin'] = None
    config: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    load_time: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class PluginError(SpiderError):
    """Base exception for plugin-related errors."""
    pass


class PluginValidationError(PluginError):
    """Raised when plugin validation fails."""
    pass


class PluginLoadError(PluginError):
    """Raised when plugin loading fails."""
    pass


class PluginExecutionError(PluginError):
    """Raised when plugin execution fails."""
    pass


class Plugin(ABC):
    """
    Base class for all SPIDER plugins.
    
    Plugins extend SPIDER functionality by implementing specific interfaces
    and following the plugin lifecycle.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the plugin with configuration."""
        self.config = config or {}
        self.logger = logging.getLogger(f"spider.plugin.{self.__class__.__name__}")
        self._status = PluginStatus.UNLOADED
        self._initialized = False
        self._started = False
        self._performance_metrics = {}
        
    @property
    def status(self) -> PluginStatus:
        """Get current plugin status."""
        return self._status
    
    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized
    
    @property
    def is_started(self) -> bool:
        """Check if plugin is started."""
        return self._started
    
    @property
    def performance_metrics(self) -> Dict[str, Any]:
        """Get plugin performance metrics."""
        return self._performance_metrics.copy()
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration."""
        pass
    
    async def initialize(self) -> None:
        """Initialize the plugin. Called once during plugin loading."""
        if self._initialized:
            return
            
        self._status = PluginStatus.INITIALIZING
        self.logger.info(f"Initializing plugin: {self.__class__.__name__}")
        
        try:
            await self._initialize()
            self._initialized = True
            self._status = PluginStatus.INITIALIZED
            self.logger.info(f"Plugin initialized: {self.__class__.__name__}")
        except Exception as e:
            self._status = PluginStatus.ERROR
            self.logger.error(f"Failed to initialize plugin {self.__class__.__name__}: {e}")
            raise PluginLoadError(f"Plugin initialization failed: {e}") from e
    
    async def start(self) -> None:
        """Start the plugin. Called when plugin becomes active."""
        if not self._initialized:
            await self.initialize()
            
        if self._started:
            return
            
        self._status = PluginStatus.RUNNING
        self.logger.info(f"Starting plugin: {self.__class__.__name__}")
        
        try:
            await self._start()
            self._started = True
            self.logger.info(f"Plugin started: {self.__class__.__name__}")
        except Exception as e:
            self._status = PluginStatus.ERROR
            self.logger.error(f"Failed to start plugin {self.__class__.__name__}: {e}")
            raise PluginExecutionError(f"Plugin start failed: {e}") from e
    
    async def stop(self) -> None:
        """Stop the plugin. Called when plugin becomes inactive."""
        if not self._started:
            return
            
        self._status = PluginStatus.STOPPING
        self.logger.info(f"Stopping plugin: {self.__class__.__name__}")
        
        try:
            await self._stop()
            self._started = False
            self._status = PluginStatus.STOPPED
            self.logger.info(f"Plugin stopped: {self.__class__.__name__}")
        except Exception as e:
            self._status = PluginStatus.ERROR
            self.logger.error(f"Failed to stop plugin {self.__class__.__name__}: {e}")
            raise PluginExecutionError(f"Plugin stop failed: {e}") from e
    
    async def cleanup(self) -> None:
        """Cleanup plugin resources. Called during plugin unloading."""
        if self._started:
            await self.stop()
            
        self._status = PluginStatus.UNLOADED
        self.logger.info(f"Cleaning up plugin: {self.__class__.__name__}")
        
        try:
            await self._cleanup()
            self._initialized = False
            self.logger.info(f"Plugin cleaned up: {self.__class__.__name__}")
        except Exception as e:
            self.logger.error(f"Failed to cleanup plugin {self.__class__.__name__}: {e}")
            raise PluginExecutionError(f"Plugin cleanup failed: {e}") from e
    
    async def _initialize(self) -> None:
        """Override this method to implement plugin-specific initialization."""
        pass
    
    async def _start(self) -> None:
        """Override this method to implement plugin-specific start logic."""
        pass
    
    async def _stop(self) -> None:
        """Override this method to implement plugin-specific stop logic."""
        pass
    
    async def _cleanup(self) -> None:
        """Override this method to implement plugin-specific cleanup logic."""
        pass
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update plugin configuration."""
        if not self.validate_config(config):
            raise PluginValidationError("Invalid configuration provided")
        self.config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current plugin configuration."""
        return self.config.copy()
    
    def record_metric(self, name: str, value: Any, timestamp: Optional[datetime] = None) -> None:
        """Record a performance metric."""
        if timestamp is None:
            timestamp = datetime.now()
        self._performance_metrics[name] = {
            'value': value,
            'timestamp': timestamp
        }
    
    def get_metric(self, name: str) -> Optional[Any]:
        """Get a performance metric value."""
        metric = self._performance_metrics.get(name)
        return metric['value'] if metric else None


class PluginRegistry:
    """Registry for managing available plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, Type[Plugin]] = {}
        self._metadata: Dict[str, PluginMetadata] = {}
        self._plugin_types: Dict[PluginType, Set[str]] = {
            plugin_type: set() for plugin_type in PluginType
        }
    
    def register(self, plugin_class: Type[Plugin], metadata: PluginMetadata) -> None:
        """Register a plugin class with metadata."""
        plugin_name = metadata.name
        
        if plugin_name in self._plugins:
            raise PluginError(f"Plugin '{plugin_name}' is already registered")
        
        self._plugins[plugin_name] = plugin_class
        self._metadata[plugin_name] = metadata
        self._plugin_types[metadata.plugin_type].add(plugin_name)
    
    def unregister(self, plugin_name: str) -> None:
        """Unregister a plugin."""
        if plugin_name not in self._plugins:
            return
            
        metadata = self._metadata[plugin_name]
        self._plugin_types[metadata.plugin_type].discard(plugin_name)
        del self._plugins[plugin_name]
        del self._metadata[plugin_name]
    
    def get_plugin_class(self, plugin_name: str) -> Optional[Type[Plugin]]:
        """Get plugin class by name."""
        return self._plugins.get(plugin_name)
    
    def get_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """Get plugin metadata by name."""
        return self._metadata.get(plugin_name)
    
    def list_plugins(self, plugin_type: Optional[PluginType] = None) -> List[str]:
        """List all registered plugins, optionally filtered by type."""
        if plugin_type is None:
            return list(self._plugins.keys())
        return list(self._plugin_types[plugin_type])
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> Dict[str, Type[Plugin]]:
        """Get all plugins of a specific type."""
        return {
            name: self._plugins[name] 
            for name in self._plugin_types[plugin_type]
        }
    
    def search_plugins(self, query: str, plugin_type: Optional[PluginType] = None) -> List[str]:
        """Search plugins by name, description, or tags."""
        results = []
        plugins_to_search = self.list_plugins(plugin_type)
        
        for plugin_name in plugins_to_search:
            metadata = self._metadata[plugin_name]
            searchable_text = f"{plugin_name} {metadata.description} {' '.join(metadata.tags)}".lower()
            
            if query.lower() in searchable_text:
                results.append(plugin_name)
        
        return results


class PluginManager:
    """Manager for plugin lifecycle and execution."""
    
    def __init__(self, registry: Optional[PluginRegistry] = None):
        self.registry = registry or PluginRegistry()
        self._loaded_plugins: Dict[str, PluginInfo] = {}
        self._plugin_instances: Dict[str, Plugin] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._logger = logging.getLogger("spider.plugin.manager")
    
    async def load_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> PluginInfo:
        """Load a plugin with configuration."""
        if plugin_name in self._loaded_plugins:
            return self._loaded_plugins[plugin_name]
        
        plugin_class = self.registry.get_plugin_class(plugin_name)
        if not plugin_class:
            raise PluginLoadError(f"Plugin '{plugin_name}' not found in registry")
        
        metadata = self.registry.get_metadata(plugin_name)
        plugin_info = PluginInfo(metadata=metadata, config=config or {})
        
        try:
            plugin_info.status = PluginStatus.LOADING
            self._logger.info(f"Loading plugin: {plugin_name}")
            
            # Validate configuration
            if not plugin_class(None).validate_config(plugin_info.config):
                raise PluginValidationError(f"Invalid configuration for plugin '{plugin_name}'")
            
            # Check dependencies
            await self._check_dependencies(metadata.dependencies)
            
            # Create plugin instance
            plugin_instance = plugin_class(plugin_info.config)
            plugin_info.instance = plugin_instance
            plugin_info.status = PluginStatus.LOADED
            plugin_info.load_time = datetime.now()
            
            self._loaded_plugins[plugin_name] = plugin_info
            self._plugin_instances[plugin_name] = plugin_instance
            
            self._logger.info(f"Plugin loaded successfully: {plugin_name}")
            return plugin_info
            
        except Exception as e:
            plugin_info.status = PluginStatus.ERROR
            plugin_info.errors.append(str(e))
            self._logger.error(f"Failed to load plugin '{plugin_name}': {e}")
            raise PluginLoadError(f"Failed to load plugin '{plugin_name}': {e}") from e
    
    async def unload_plugin(self, plugin_name: str) -> None:
        """Unload a plugin and cleanup resources."""
        if plugin_name not in self._loaded_plugins:
            return
        
        plugin_info = self._loaded_plugins[plugin_name]
        
        try:
            if plugin_info.instance:
                await plugin_info.instance.cleanup()
            
            del self._loaded_plugins[plugin_name]
            if plugin_name in self._plugin_instances:
                del self._plugin_instances[plugin_name]
            
            self._logger.info(f"Plugin unloaded: {plugin_name}")
            
        except Exception as e:
            self._logger.error(f"Failed to unload plugin '{plugin_name}': {e}")
            raise PluginExecutionError(f"Failed to unload plugin '{plugin_name}': {e}") from e
    
    async def start_plugin(self, plugin_name: str) -> None:
        """Start a loaded plugin."""
        if plugin_name not in self._loaded_plugins:
            raise PluginExecutionError(f"Plugin '{plugin_name}' is not loaded")
        
        plugin_info = self._loaded_plugins[plugin_name]
        
        if not plugin_info.instance:
            raise PluginExecutionError(f"Plugin instance not available for '{plugin_name}'")
        
        try:
            await plugin_info.instance.start()
            plugin_info.status = PluginStatus.RUNNING
            plugin_info.last_used = datetime.now()
            plugin_info.usage_count += 1
            
            self._logger.info(f"Plugin started: {plugin_name}")
            
        except Exception as e:
            plugin_info.status = PluginStatus.ERROR
            plugin_info.errors.append(str(e))
            self._logger.error(f"Failed to start plugin '{plugin_name}': {e}")
            raise PluginExecutionError(f"Failed to start plugin '{plugin_name}': {e}") from e
    
    async def stop_plugin(self, plugin_name: str) -> None:
        """Stop a running plugin."""
        if plugin_name not in self._loaded_plugins:
            return
        
        plugin_info = self._loaded_plugins[plugin_name]
        
        if not plugin_info.instance or plugin_info.status != PluginStatus.RUNNING:
            return
        
        try:
            await plugin_info.instance.stop()
            plugin_info.status = PluginStatus.STOPPED
            
            self._logger.info(f"Plugin stopped: {plugin_name}")
            
        except Exception as e:
            plugin_info.status = PluginStatus.ERROR
            plugin_info.errors.append(str(e))
            self._logger.error(f"Failed to stop plugin '{plugin_name}': {e}")
            raise PluginExecutionError(f"Failed to stop plugin '{plugin_name}': {e}") from e
    
    async def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a loaded plugin instance."""
        if plugin_name not in self._loaded_plugins:
            return None
        
        plugin_info = self._loaded_plugins[plugin_name]
        return plugin_info.instance
    
    def list_loaded_plugins(self) -> List[str]:
        """List all loaded plugins."""
        return list(self._loaded_plugins.keys())
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get plugin information."""
        return self._loaded_plugins.get(plugin_name)
    
    async def load_plugins_from_directory(self, directory: Path) -> List[str]:
        """Load all plugins from a directory."""
        loaded_plugins = []
        
        for plugin_file in directory.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
                
            try:
                plugin_name = plugin_file.stem
                module_name = f"plugins.{plugin_name}"
                
                # Load module
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find plugin classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, Plugin) and 
                        obj != Plugin and 
                        hasattr(obj, 'get_metadata')):
                        
                        metadata = obj().get_metadata()
                        self.registry.register(obj, metadata)
                        
                        # Auto-load if configured
                        if self._should_auto_load(metadata):
                            await self.load_plugin(plugin_name)
                            loaded_plugins.append(plugin_name)
                
            except Exception as e:
                self._logger.error(f"Failed to load plugin from {plugin_file}: {e}")
        
        return loaded_plugins
    
    def _should_auto_load(self, metadata: PluginMetadata) -> bool:
        """Determine if a plugin should be auto-loaded."""
        # Check for auto-load configuration
        return metadata.tags and "auto_load" in metadata.tags
    
    async def _check_dependencies(self, dependencies: List[str]) -> None:
        """Check if all plugin dependencies are satisfied."""
        for dep in dependencies:
            if dep not in self._loaded_plugins:
                raise PluginLoadError(f"Dependency '{dep}' is not loaded")
            
            dep_info = self._loaded_plugins[dep]
            if dep_info.status != PluginStatus.RUNNING:
                raise PluginLoadError(f"Dependency '{dep}' is not running")
    
    async def shutdown(self) -> None:
        """Shutdown all loaded plugins."""
        for plugin_name in list(self._loaded_plugins.keys()):
            try:
                await self.unload_plugin(plugin_name)
            except Exception as e:
                self._logger.error(f"Error during plugin shutdown '{plugin_name}': {e}")
