"""Automated health recovery system for SPIDER framework."""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import random

from ..core.exceptions import SpiderError, MonitoringError
from ..core.logger import get_logger
from .health import HealthChecker, HealthStatus, SystemHealth


class RecoveryAction(Enum):
    """Available recovery actions."""
    RESTART_SERVICE = "restart_service"
    RESTART_ENGINE = "restart_engine"
    CLEAR_CACHE = "clear_cache"
    RESET_CONNECTIONS = "reset_connections"
    SWITCH_PROXY = "switch_proxy"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NOTIFY_ADMIN = "notify_admin"
    CUSTOM = "custom"


@dataclass
class RecoveryRule:
    """Recovery rule definition."""
    name: str
    condition: Callable[[SystemHealth], bool]
    action: RecoveryAction
    priority: int = 1
    cooldown: int = 300  # seconds
    max_attempts: int = 3
    custom_handler: Optional[Callable] = None
    enabled: bool = True


@dataclass
class RecoveryAttempt:
    """Recovery attempt record."""
    rule_name: str
    action: RecoveryAction
    timestamp: float
    success: bool
    error_message: Optional[str] = None
    duration: float = 0.0


class RecoveryManager:
    """Manages automated health recovery for SPIDER framework."""
    
    def __init__(self, health_checker: HealthChecker):
        """Initialize recovery manager.
        
        Args:
            health_checker: Health checker instance
        """
        self.health_checker = health_checker
        self.logger = get_logger(self.__class__.__name__)
        self.rules: List[RecoveryRule] = []
        self.attempts: List[RecoveryAttempt] = []
        self.last_attempts: Dict[str, float] = {}
        self.attempt_counts: Dict[str, int] = {}
        self._running = False
        self._recovery_lock = asyncio.Lock()
        
        # Initialize default recovery rules
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Setup default recovery rules."""
        # High priority rules
        self.add_rule(RecoveryRule(
            name="database_connection_failure",
            condition=lambda health: (
                health.components.get("database", {}).get("status") == HealthStatus.UNHEALTHY
            ),
            action=RecoveryAction.RESTART_SERVICE,
            priority=1,
            cooldown=60,
            max_attempts=3
        ))
        
        self.add_rule(RecoveryRule(
            name="redis_connection_failure",
            condition=lambda health: (
                health.components.get("redis", {}).get("status") == HealthStatus.UNHEALTHY
            ),
            action=RecoveryAction.RESTART_SERVICE,
            priority=1,
            cooldown=60,
            max_attempts=3
        ))
        
        self.add_rule(RecoveryRule(
            name="proxy_failure",
            condition=lambda health: (
                health.components.get("proxy", {}).get("status") == HealthStatus.UNHEALTHY
            ),
            action=RecoveryAction.SWITCH_PROXY,
            priority=2,
            cooldown=30,
            max_attempts=5
        ))
        
        self.add_rule(RecoveryRule(
            name="captcha_failure",
            condition=lambda health: (
                health.components.get("captcha", {}).get("status") == HealthStatus.UNHEALTHY
            ),
            action=RecoveryAction.SWITCH_PROXY,
            priority=2,
            cooldown=30,
            max_attempts=3
        ))
        
        # Medium priority rules
        self.add_rule(RecoveryRule(
            name="high_memory_usage",
            condition=lambda health: (
                health.system_metrics.get("memory_usage_percent", 0) > 90
            ),
            action=RecoveryAction.CLEAR_CACHE,
            priority=3,
            cooldown=120,
            max_attempts=2
        ))
        
        self.add_rule(RecoveryRule(
            name="high_cpu_usage",
            condition=lambda health: (
                health.system_metrics.get("cpu_usage_percent", 0) > 95
            ),
            action=RecoveryAction.SCALE_UP,
            priority=3,
            cooldown=180,
            max_attempts=2
        ))
        
        self.add_rule(RecoveryRule(
            name="low_success_rate",
            condition=lambda health: (
                health.business_metrics.get("success_rate", 100) < 50
            ),
            action=RecoveryAction.RESTART_ENGINE,
            priority=2,
            cooldown=300,
            max_attempts=3
        ))
        
        # Low priority rules
        self.add_rule(RecoveryRule(
            name="low_memory_usage",
            condition=lambda health: (
                health.system_metrics.get("memory_usage_percent", 0) < 20
            ),
            action=RecoveryAction.SCALE_DOWN,
            priority=5,
            cooldown=600,
            max_attempts=1
        ))
        
        self.add_rule(RecoveryRule(
            name="critical_failure",
            condition=lambda health: (
                health.overall_status == HealthStatus.UNHEALTHY and
                len([c for c in health.components.values() if c.get("status") == HealthStatus.UNHEALTHY]) > 2
            ),
            action=RecoveryAction.NOTIFY_ADMIN,
            priority=0,
            cooldown=60,
            max_attempts=1
        ))
    
    def add_rule(self, rule: RecoveryRule) -> None:
        """Add a recovery rule.
        
        Args:
            rule: Recovery rule to add
        """
        self.rules.append(rule)
        self.logger.info(f"Added recovery rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a recovery rule.
        
        Args:
            rule_name: Name of rule to remove
            
        Returns:
            True if rule was removed, False if not found
        """
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                self.logger.info(f"Removed recovery rule: {rule_name}")
                return True
        return False
    
    def enable_rule(self, rule_name: str) -> bool:
        """Enable a recovery rule.
        
        Args:
            rule_name: Name of rule to enable
            
        Returns:
            True if rule was enabled, False if not found
        """
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                self.logger.info(f"Enabled recovery rule: {rule_name}")
                return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """Disable a recovery rule.
        
        Args:
            rule_name: Name of rule to disable
            
        Returns:
            True if rule was disabled, False if not found
        """
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                self.logger.info(f"Disabled recovery rule: {rule_name}")
                return True
        return False
    
    async def start_monitoring(self, check_interval: int = 30) -> None:
        """Start automated recovery monitoring.
        
        Args:
            check_interval: Health check interval in seconds
        """
        if self._running:
            self.logger.warning("Recovery monitoring is already running")
            return
        
        self._running = True
        self.logger.info(f"Started recovery monitoring with {check_interval}s interval")
        
        try:
            while self._running:
                await self._check_and_recover()
                await asyncio.sleep(check_interval)
        except Exception as e:
            self.logger.error(f"Error in recovery monitoring: {e}")
        finally:
            self._running = False
            self.logger.info("Recovery monitoring stopped")
    
    async def stop_monitoring(self) -> None:
        """Stop automated recovery monitoring."""
        self._running = False
        self.logger.info("Stopping recovery monitoring")
    
    async def _check_and_recover(self) -> None:
        """Check health and attempt recovery if needed."""
        try:
            # Get current health status
            health = await self.health_checker.get_system_health()
            
            # Find applicable recovery rules
            applicable_rules = []
            for rule in self.rules:
                if not rule.enabled:
                    continue
                
                try:
                    if rule.condition(health):
                        applicable_rules.append(rule)
                except Exception as e:
                    self.logger.error(f"Error evaluating rule {rule.name}: {e}")
            
            # Sort by priority (lower number = higher priority)
            applicable_rules.sort(key=lambda r: r.priority)
            
            # Execute recovery actions
            for rule in applicable_rules:
                await self._execute_recovery_rule(rule, health)
                
        except Exception as e:
            self.logger.error(f"Error in recovery check: {e}")
    
    async def _execute_recovery_rule(self, rule: RecoveryRule, health: SystemHealth) -> None:
        """Execute a recovery rule.
        
        Args:
            rule: Recovery rule to execute
            health: Current health status
        """
        async with self._recovery_lock:
            # Check cooldown
            last_attempt = self.last_attempts.get(rule.name, 0)
            if time.time() - last_attempt < rule.cooldown:
                return
            
            # Check max attempts
            attempt_count = self.attempt_counts.get(rule.name, 0)
            if attempt_count >= rule.max_attempts:
                self.logger.warning(f"Max attempts reached for rule {rule.name}")
                return
            
            # Execute recovery action
            self.logger.info(f"Executing recovery action: {rule.action.value} for rule: {rule.name}")
            
            start_time = time.time()
            success = False
            error_message = None
            
            try:
                if rule.custom_handler:
                    await rule.custom_handler(health)
                else:
                    await self._execute_recovery_action(rule.action, health)
                
                success = True
                self.logger.info(f"Recovery action {rule.action.value} completed successfully")
                
            except Exception as e:
                error_message = str(e)
                self.logger.error(f"Recovery action {rule.action.value} failed: {e}")
            
            # Record attempt
            duration = time.time() - start_time
            attempt = RecoveryAttempt(
                rule_name=rule.name,
                action=rule.action,
                timestamp=time.time(),
                success=success,
                error_message=error_message,
                duration=duration
            )
            self.attempts.append(attempt)
            
            # Update counters
            self.last_attempts[rule.name] = time.time()
            if success:
                self.attempt_counts[rule.name] = 0  # Reset on success
            else:
                self.attempt_counts[rule.name] = attempt_count + 1
            
            # Keep only recent attempts
            cutoff_time = time.time() - 3600  # 1 hour
            self.attempts = [a for a in self.attempts if a.timestamp > cutoff_time]
    
    async def _execute_recovery_action(self, action: RecoveryAction, health: SystemHealth) -> None:
        """Execute a specific recovery action.
        
        Args:
            action: Recovery action to execute
            health: Current health status
        """
        if action == RecoveryAction.RESTART_SERVICE:
            await self._restart_service()
        elif action == RecoveryAction.RESTART_ENGINE:
            await self._restart_engine()
        elif action == RecoveryAction.CLEAR_CACHE:
            await self._clear_cache()
        elif action == RecoveryAction.RESET_CONNECTIONS:
            await self._reset_connections()
        elif action == RecoveryAction.SWITCH_PROXY:
            await self._switch_proxy()
        elif action == RecoveryAction.SCALE_UP:
            await self._scale_up()
        elif action == RecoveryAction.SCALE_DOWN:
            await self._scale_down()
        elif action == RecoveryAction.NOTIFY_ADMIN:
            await self._notify_admin(health)
        else:
            raise ValueError(f"Unknown recovery action: {action}")
    
    async def _restart_service(self) -> None:
        """Restart SPIDER service."""
        self.logger.info("Restarting SPIDER service...")
        # In a real implementation, this would restart the service
        # For now, we'll simulate a restart
        await asyncio.sleep(2)
        self.logger.info("SPIDER service restarted")
    
    async def _restart_engine(self) -> None:
        """Restart scraping engine."""
        self.logger.info("Restarting scraping engine...")
        # In a real implementation, this would restart the engine
        await asyncio.sleep(1)
        self.logger.info("Scraping engine restarted")
    
    async def _clear_cache(self) -> None:
        """Clear system cache."""
        self.logger.info("Clearing system cache...")
        # In a real implementation, this would clear caches
        await asyncio.sleep(0.5)
        self.logger.info("System cache cleared")
    
    async def _reset_connections(self) -> None:
        """Reset network connections."""
        self.logger.info("Resetting network connections...")
        # In a real implementation, this would reset connections
        await asyncio.sleep(1)
        self.logger.info("Network connections reset")
    
    async def _switch_proxy(self) -> None:
        """Switch to a different proxy."""
        self.logger.info("Switching proxy...")
        # In a real implementation, this would switch proxies
        await asyncio.sleep(0.5)
        self.logger.info("Proxy switched")
    
    async def _scale_up(self) -> None:
        """Scale up system resources."""
        self.logger.info("Scaling up system resources...")
        # In a real implementation, this would scale up
        await asyncio.sleep(2)
        self.logger.info("System resources scaled up")
    
    async def _scale_down(self) -> None:
        """Scale down system resources."""
        self.logger.info("Scaling down system resources...")
        # In a real implementation, this would scale down
        await asyncio.sleep(1)
        self.logger.info("System resources scaled down")
    
    async def _notify_admin(self, health: SystemHealth) -> None:
        """Notify administrators of critical issues."""
        self.logger.critical(f"Critical system failure detected: {health}")
        # In a real implementation, this would send notifications
        # via email, Slack, PagerDuty, etc.
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics.
        
        Returns:
            Recovery statistics
        """
        total_attempts = len(self.attempts)
        successful_attempts = len([a for a in self.attempts if a.success])
        failed_attempts = total_attempts - successful_attempts
        
        # Recent attempts (last hour)
        recent_cutoff = time.time() - 3600
        recent_attempts = [a for a in self.attempts if a.timestamp > recent_cutoff]
        
        # Rule statistics
        rule_stats = {}
        for rule in self.rules:
            rule_attempts = [a for a in self.attempts if a.rule_name == rule.name]
            rule_stats[rule.name] = {
                "enabled": rule.enabled,
                "total_attempts": len(rule_attempts),
                "successful_attempts": len([a for a in rule_attempts if a.success]),
                "last_attempt": max([a.timestamp for a in rule_attempts]) if rule_attempts else None,
                "attempt_count": self.attempt_counts.get(rule.name, 0)
            }
        
        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "success_rate": (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            "recent_attempts": len(recent_attempts),
            "active_rules": len([r for r in self.rules if r.enabled]),
            "rule_stats": rule_stats,
            "monitoring_active": self._running
        }
    
    def get_recent_attempts(self, hours: int = 24) -> List[RecoveryAttempt]:
        """Get recent recovery attempts.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent recovery attempts
        """
        cutoff_time = time.time() - (hours * 3600)
        return [a for a in self.attempts if a.timestamp > cutoff_time]
    
    def cleanup(self) -> None:
        """Cleanup recovery manager."""
        self._running = False
        self.attempts.clear()
        self.last_attempts.clear()
        self.attempt_counts.clear()
        self.logger.info("Recovery manager cleaned up")


class RecoveryConfig:
    """Configuration for recovery manager."""
    
    def __init__(
        self,
        check_interval: int = 30,
        max_attempts_per_rule: int = 3,
        default_cooldown: int = 300,
        cleanup_interval: int = 3600
    ):
        """Initialize recovery configuration.
        
        Args:
            check_interval: Health check interval in seconds
            max_attempts_per_rule: Maximum attempts per rule
            default_cooldown: Default cooldown period in seconds
            cleanup_interval: Cleanup interval in seconds
        """
        self.check_interval = check_interval
        self.max_attempts_per_rule = max_attempts_per_rule
        self.default_cooldown = default_cooldown
        self.cleanup_interval = cleanup_interval
