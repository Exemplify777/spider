"""Tests for SPIDER infrastructure components."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass

from spider.infrastructure.proxy import (
    ProxyManager, ProxyPool, ProxyInfo, ProxyStatus,
    BrightDataProvider, OxylabsProvider
)
from spider.infrastructure.captcha import (
    CAPTCHAManager, CAPTCHATask, CAPTCHAType,
    TwoCaptchaProvider, AntiCaptchaProvider
)
from spider.core.exceptions import ProxyError, CAPTCHAError


class TestProxyInfo:
    """Test proxy information container."""
    
    def test_proxy_info_creation(self):
        """Test proxy info creation."""
        proxy = ProxyInfo(
            host="proxy.example.com",
            port=8080,
            username="user",
            password="pass",
            protocol="http",
            country="US"
        )
        
        assert proxy.host == "proxy.example.com"
        assert proxy.port == 8080
        assert proxy.username == "user"
        assert proxy.password == "pass"
        assert proxy.protocol == "http"
        assert proxy.country == "US"
        assert proxy.status == ProxyStatus.UNKNOWN
        assert proxy.success_rate == 0.0
        assert proxy.error_count == 0
    
    def test_proxy_url(self):
        """Test proxy URL generation."""
        # With credentials
        proxy = ProxyInfo(
            host="proxy.example.com",
            port=8080,
            username="user",
            password="pass",
            protocol="http"
        )
        assert proxy.url == "http://user:pass@proxy.example.com:8080"
        
        # Without credentials
        proxy = ProxyInfo(
            host="proxy.example.com",
            port=8080,
            protocol="https"
        )
        assert proxy.url == "https://proxy.example.com:8080"
    
    def test_proxy_health(self):
        """Test proxy health status."""
        # Healthy proxy
        proxy = ProxyInfo(
            host="proxy.example.com",
            port=8080,
            status=ProxyStatus.HEALTHY,
            success_rate=0.8
        )
        assert proxy.is_healthy is True
        
        # Unhealthy proxy
        proxy = ProxyInfo(
            host="proxy.example.com",
            port=8080,
            status=ProxyStatus.UNHEALTHY,
            success_rate=0.3
        )
        assert proxy.is_healthy is False


class TestProxyPool:
    """Test proxy pool management."""
    
    @pytest.fixture
    def proxy_pool(self):
        """Create proxy pool for testing."""
        config = {
            'rotation_interval': 300,
            'health_check_interval': 60
        }
        return ProxyPool(config)
    
    @pytest.fixture
    def sample_proxies(self):
        """Create sample proxies for testing."""
        return [
            ProxyInfo(host="proxy1.com", port=8080, status=ProxyStatus.HEALTHY, success_rate=0.9),
            ProxyInfo(host="proxy2.com", port=8080, status=ProxyStatus.HEALTHY, success_rate=0.8),
            ProxyInfo(host="proxy3.com", port=8080, status=ProxyStatus.UNHEALTHY, success_rate=0.2),
        ]
    
    @pytest.mark.asyncio
    async def test_add_proxy(self, proxy_pool):
        """Test adding proxy to pool."""
        proxy = ProxyInfo(host="test.com", port=8080)
        
        await proxy_pool.add_proxy(proxy)
        
        assert len(proxy_pool.proxies) == 1
        assert proxy_pool.proxies[0] == proxy
    
    @pytest.mark.asyncio
    async def test_add_proxies(self, proxy_pool, sample_proxies):
        """Test adding multiple proxies to pool."""
        await proxy_pool.add_proxies(sample_proxies)
        
        assert len(proxy_pool.proxies) == 3
    
    @pytest.mark.asyncio
    async def test_get_proxy_round_robin(self, proxy_pool, sample_proxies):
        """Test getting proxy with round-robin strategy."""
        await proxy_pool.add_proxies(sample_proxies)
        
        # Get first proxy
        proxy1 = await proxy_pool.get_proxy("round_robin")
        assert proxy1 is not None
        assert proxy1.host == "proxy1.com"
        
        # Get second proxy
        proxy2 = await proxy_pool.get_proxy("round_robin")
        assert proxy2 is not None
        assert proxy2.host == "proxy2.com"
    
    @pytest.mark.asyncio
    async def test_get_proxy_random(self, proxy_pool, sample_proxies):
        """Test getting proxy with random strategy."""
        await proxy_pool.add_proxies(sample_proxies)
        
        proxy = await proxy_pool.get_proxy("random")
        assert proxy is not None
        assert proxy in sample_proxies
    
    @pytest.mark.asyncio
    async def test_get_proxy_healthiest(self, proxy_pool, sample_proxies):
        """Test getting healthiest proxy."""
        await proxy_pool.add_proxies(sample_proxies)
        
        proxy = await proxy_pool.get_proxy("healthiest")
        assert proxy is not None
        assert proxy.success_rate == 0.9  # Highest success rate
    
    @pytest.mark.asyncio
    async def test_get_proxy_no_healthy(self, proxy_pool):
        """Test getting proxy when no healthy proxies available."""
        # Add only unhealthy proxy
        unhealthy_proxy = ProxyInfo(
            host="unhealthy.com",
            port=8080,
            status=ProxyStatus.UNHEALTHY,
            success_rate=0.1
        )
        await proxy_pool.add_proxy(unhealthy_proxy)
        
        proxy = await proxy_pool.get_proxy("round_robin")
        assert proxy is None
    
    @pytest.mark.asyncio
    async def test_get_proxy_empty_pool(self, proxy_pool):
        """Test getting proxy from empty pool."""
        proxy = await proxy_pool.get_proxy("round_robin")
        assert proxy is None
    
    def test_update_proxy_stats(self, proxy_pool):
        """Test updating proxy statistics."""
        proxy = ProxyInfo(host="test.com", port=8080)
        
        # Update with success
        proxy_pool.update_proxy_stats(proxy, True, 1.5)
        assert proxy.success_rate == 0.05  # Initial increment
        assert proxy.response_time == 1.5
        
        # Update with failure
        proxy_pool.update_proxy_stats(proxy, False, 2.0)
        assert proxy.success_rate == 0.0  # Decremented
        assert proxy.error_count == 1


class TestProxyProviders:
    """Test proxy providers."""
    
    @pytest.mark.asyncio
    async def test_bright_data_provider(self):
        """Test Bright Data provider."""
        config = {
            'proxies': [
                {
                    'host': 'proxy.brightdata.com',
                    'port': 22225,
                    'username': 'user',
                    'password': 'pass',
                    'protocol': 'http',
                    'country': 'US'
                }
            ]
        }
        
        provider = BrightDataProvider(config)
        proxies = await provider.get_proxies()
        
        assert len(proxies) == 1
        assert proxies[0].host == 'proxy.brightdata.com'
        assert proxies[0].port == 22225
        assert proxies[0].username == 'user'
        assert proxies[0].password == 'pass'
    
    @pytest.mark.asyncio
    async def test_oxylabs_provider(self):
        """Test Oxylabs provider."""
        config = {
            'proxies': [
                {
                    'host': 'pr.oxylabs.io',
                    'port': 7777,
                    'username': 'user',
                    'password': 'pass',
                    'protocol': 'http',
                    'country': 'US'
                }
            ]
        }
        
        provider = OxylabsProvider(config)
        proxies = await provider.get_proxies()
        
        assert len(proxies) == 1
        assert proxies[0].host == 'pr.oxylabs.io'
        assert proxies[0].port == 7777


class TestProxyManager:
    """Test proxy manager."""
    
    @pytest.fixture
    def proxy_config(self):
        """Create proxy configuration for testing."""
        return {
            'enabled': True,
            'providers': [
                {
                    'type': 'bright_data',
                    'settings': {
                        'proxies': [
                            {
                                'host': 'proxy1.com',
                                'port': 8080,
                                'username': 'user1',
                                'password': 'pass1'
                            }
                        ]
                    }
                }
            ],
            'pool': {
                'rotation_interval': 300,
                'health_check_interval': 60
            }
        }
    
    @pytest.mark.asyncio
    async def test_proxy_manager_initialization(self, proxy_config):
        """Test proxy manager initialization."""
        manager = ProxyManager(proxy_config)
        
        assert manager.config == proxy_config
        assert len(manager.providers) == 1
        assert manager.pool is not None
    
    @pytest.mark.asyncio
    async def test_proxy_manager_initialize(self, proxy_config):
        """Test proxy manager initialization process."""
        manager = ProxyManager(proxy_config)
        
        # Mock provider.get_proxies
        with patch.object(manager.providers[0], 'get_proxies') as mock_get_proxies:
            mock_proxy = ProxyInfo(host="test.com", port=8080)
            mock_get_proxies.return_value = [mock_proxy]
            
            await manager.initialize()
            
            assert len(manager.pool.proxies) == 1
            mock_get_proxies.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_proxy(self, proxy_config):
        """Test getting proxy from manager."""
        manager = ProxyManager(proxy_config)
        
        # Add test proxy
        test_proxy = ProxyInfo(host="test.com", port=8080, status=ProxyStatus.HEALTHY)
        await manager.pool.add_proxy(test_proxy)
        
        proxy = await manager.get_proxy("round_robin")
        assert proxy == test_proxy
    
    @pytest.mark.asyncio
    async def test_report_proxy_result(self, proxy_config):
        """Test reporting proxy usage result."""
        manager = ProxyManager(proxy_config)
        
        test_proxy = ProxyInfo(host="test.com", port=8080)
        await manager.pool.add_proxy(test_proxy)
        
        await manager.report_proxy_result(test_proxy, True, 1.5)
        
        assert test_proxy.success_rate > 0
        assert test_proxy.response_time == 1.5


class TestCAPTCHATask:
    """Test CAPTCHA task container."""
    
    def test_captcha_task_creation(self):
        """Test CAPTCHA task creation."""
        task = CAPTCHATask(
            task_id="task123",
            captcha_type=CAPTCHAType.IMAGE,
            image_data=b"fake_image_data"
        )
        
        assert task.task_id == "task123"
        assert task.captcha_type == CAPTCHAType.IMAGE
        assert task.image_data == b"fake_image_data"
        assert task.success is False
        assert task.error is None
    
    def test_captcha_task_with_site_key(self):
        """Test CAPTCHA task with site key."""
        task = CAPTCHATask(
            task_id="task456",
            captcha_type=CAPTCHAType.RECAPTCHA_V2,
            site_key="6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_kl-",
            page_url="https://example.com"
        )
        
        assert task.site_key == "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_kl-"
        assert task.page_url == "https://example.com"


class TestCAPTCHAProviders:
    """Test CAPTCHA providers."""
    
    @pytest.mark.asyncio
    async def test_two_captcha_provider(self):
        """Test 2captcha provider."""
        config = {
            'api_key': 'test_key',
            'base_url': 'http://2captcha.com',
            'timeout': 120
        }
        
        provider = TwoCaptchaProvider(config)
        
        assert provider.api_key == 'test_key'
        assert provider.base_url == 'http://2captcha.com'
        assert provider.timeout == 120
    
    @pytest.mark.asyncio
    async def test_anticaptcha_provider(self):
        """Test Anti-Captcha provider."""
        config = {
            'api_key': 'test_key',
            'base_url': 'https://api.anti-captcha.com',
            'timeout': 120
        }
        
        provider = AntiCaptchaProvider(config)
        
        assert provider.api_key == 'test_key'
        assert provider.base_url == 'https://api.anti-captcha.com'
        assert provider.timeout == 120


class TestCAPTCHAManager:
    """Test CAPTCHA manager."""
    
    @pytest.fixture
    def captcha_config(self):
        """Create CAPTCHA configuration for testing."""
        return {
            'enabled': True,
            'providers': [
                {
                    'type': '2captcha',
                    'settings': {
                        'api_key': 'test_key',
                        'base_url': 'http://2captcha.com',
                        'timeout': 120
                    }
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_captcha_manager_initialization(self, captcha_config):
        """Test CAPTCHA manager initialization."""
        manager = CAPTCHAManager(captcha_config)
        
        assert manager.config == captcha_config
        assert len(manager.providers) == 1
        assert manager.current_provider_index == 0
    
    @pytest.mark.asyncio
    async def test_solve_captcha_success(self, captcha_config):
        """Test successful CAPTCHA solving."""
        manager = CAPTCHAManager(captcha_config)
        
        task = CAPTCHATask(
            task_id="task123",
            captcha_type=CAPTCHAType.IMAGE,
            image_data=b"fake_image_data"
        )
        
        # Mock provider.solve_captcha
        with patch.object(manager.providers[0], 'solve_captcha') as mock_solve:
            mock_solve.return_value = "solution123"
            
            solution = await manager.solve_captcha(task)
            
            assert solution == "solution123"
            assert task.success is True
            assert task.solution == "solution123"
            mock_solve.assert_called_once_with(task)
    
    @pytest.mark.asyncio
    async def test_solve_captcha_failure(self, captcha_config):
        """Test CAPTCHA solving failure."""
        manager = CAPTCHAManager(captcha_config)
        
        task = CAPTCHATask(
            task_id="task123",
            captcha_type=CAPTCHAType.IMAGE,
            image_data=b"fake_image_data"
        )
        
        # Mock provider.solve_captcha to raise exception
        with patch.object(manager.providers[0], 'solve_captcha') as mock_solve:
            mock_solve.side_effect = CAPTCHAError("Solving failed")
            
            with pytest.raises(CAPTCHAError):
                await manager.solve_captcha(task)
            
            assert task.success is False
            assert task.error == "Solving failed"
    
    @pytest.mark.asyncio
    async def test_solve_captcha_no_providers(self):
        """Test CAPTCHA solving with no providers."""
        config = {'enabled': True, 'providers': []}
        manager = CAPTCHAManager(config)
        
        task = CAPTCHATask(
            task_id="task123",
            captcha_type=CAPTCHAType.IMAGE,
            image_data=b"fake_image_data"
        )
        
        with pytest.raises(CAPTCHAError):
            await manager.solve_captcha(task)
    
    @pytest.mark.asyncio
    async def test_get_balance(self, captcha_config):
        """Test getting provider balances."""
        manager = CAPTCHAManager(captcha_config)
        
        # Mock provider.get_balance
        with patch.object(manager.providers[0], 'get_balance') as mock_balance:
            mock_balance.return_value = 10.50
            
            balances = await manager.get_balance()
            
            assert 'provider_1' in balances
            assert balances['provider_1'] == 10.50
            mock_balance.assert_called_once()


# Integration tests
class TestInfrastructureIntegration:
    """Test infrastructure component integration."""
    
    @pytest.mark.asyncio
    async def test_proxy_and_captcha_integration(self):
        """Test proxy and CAPTCHA integration."""
        proxy_config = {
            'enabled': True,
            'providers': [
                {
                    'type': 'bright_data',
                    'settings': {
                        'proxies': [
                            {
                                'host': 'proxy.com',
                                'port': 8080,
                                'username': 'user',
                                'password': 'pass'
                            }
                        ]
                    }
                }
            ]
        }
        
        captcha_config = {
            'enabled': True,
            'providers': [
                {
                    'type': '2captcha',
                    'settings': {
                        'api_key': 'test_key',
                        'base_url': 'http://2captcha.com'
                    }
                }
            ]
        }
        
        # Initialize managers
        proxy_manager = ProxyManager(proxy_config)
        captcha_manager = CAPTCHAManager(captcha_config)
        
        # Add test proxy
        test_proxy = ProxyInfo(host="proxy.com", port=8080, status=ProxyStatus.HEALTHY)
        await proxy_manager.pool.add_proxy(test_proxy)
        
        # Test getting proxy
        proxy = await proxy_manager.get_proxy()
        assert proxy is not None
        
        # Test CAPTCHA task
        task = CAPTCHATask(
            task_id="test_task",
            captcha_type=CAPTCHAType.IMAGE,
            image_data=b"test_data"
        )
        
        # Mock CAPTCHA solving
        with patch.object(captcha_manager.providers[0], 'solve_captcha') as mock_solve:
            mock_solve.return_value = "test_solution"
            
            solution = await captcha_manager.solve_captcha(task)
            assert solution == "test_solution"
