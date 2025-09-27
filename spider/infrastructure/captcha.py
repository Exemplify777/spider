"""CAPTCHA solving infrastructure for SPIDER framework."""

import asyncio
import base64
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from enum import Enum

import httpx

from ..core.exceptions import CAPTCHAError
from ..core.logger import get_logger


class CAPTCHAType(Enum):
    """CAPTCHA type enumeration."""
    IMAGE = "image"
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    FUNCAPTCHA = "funcaptcha"


@dataclass
class CAPTCHATask:
    """CAPTCHA task container."""
    task_id: str
    captcha_type: CAPTCHAType
    site_key: Optional[str] = None
    page_url: Optional[str] = None
    image_data: Optional[bytes] = None
    additional_data: Optional[Dict[str, Any]] = None
    created_at: Optional[float] = None
    solved_at: Optional[float] = None
    solution: Optional[str] = None
    success: bool = False
    error: Optional[str] = None


class CAPTCHAProvider(ABC):
    """Base class for CAPTCHA solving providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize CAPTCHA provider.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', '')
        self.timeout = config.get('timeout', 120)
    
    @abstractmethod
    async def solve_captcha(self, task: CAPTCHATask) -> str:
        """Solve a CAPTCHA task.
        
        Args:
            task: CAPTCHA task to solve
            
        Returns:
            CAPTCHA solution
        """
        pass
    
    @abstractmethod
    async def get_balance(self) -> float:
        """Get account balance.
        
        Returns:
            Account balance
        """
        pass


class TwoCaptchaProvider(CAPTCHAProvider):
    """2captcha.com provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize 2captcha provider."""
        super().__init__(config)
        self.base_url = "http://2captcha.com"
    
    async def solve_captcha(self, task: CAPTCHATask) -> str:
        """Solve CAPTCHA using 2captcha."""
        try:
            if task.captcha_type == CAPTCHAType.IMAGE:
                return await self._solve_image_captcha(task)
            elif task.captcha_type == CAPTCHAType.RECAPTCHA_V2:
                return await self._solve_recaptcha_v2(task)
            elif task.captcha_type == CAPTCHAType.RECAPTCHA_V3:
                return await self._solve_recaptcha_v3(task)
            elif task.captcha_type == CAPTCHAType.HCAPTCHA:
                return await self._solve_hcaptcha(task)
            else:
                raise CAPTCHAError(f"Unsupported CAPTCHA type: {task.captcha_type}")
        except Exception as e:
            self.logger.error(f"2captcha solving failed: {e}")
            raise CAPTCHAError(f"2captcha solving failed: {e}")
    
    async def _solve_image_captcha(self, task: CAPTCHATask) -> str:
        """Solve image CAPTCHA."""
        # Submit CAPTCHA
        submit_data = {
            'key': self.api_key,
            'method': 'base64',
            'body': base64.b64encode(task.image_data).decode('utf-8')
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/in.php",
                data=submit_data,
                timeout=self.timeout
            )
            
            if response.text.startswith('OK|'):
                captcha_id = response.text.split('|')[1]
            else:
                raise CAPTCHAError(f"Failed to submit CAPTCHA: {response.text}")
        
        # Wait for solution
        return await self._wait_for_solution(captcha_id)
    
    async def _solve_recaptcha_v2(self, task: CAPTCHATask) -> str:
        """Solve reCAPTCHA v2."""
        submit_data = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': task.site_key,
            'pageurl': task.page_url
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/in.php",
                data=submit_data,
                timeout=self.timeout
            )
            
            if response.text.startswith('OK|'):
                captcha_id = response.text.split('|')[1]
            else:
                raise CAPTCHAError(f"Failed to submit reCAPTCHA v2: {response.text}")
        
        return await self._wait_for_solution(captcha_id)
    
    async def _solve_recaptcha_v3(self, task: CAPTCHATask) -> str:
        """Solve reCAPTCHA v3."""
        submit_data = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': task.site_key,
            'pageurl': task.page_url,
            'version': 'v3',
            'action': task.additional_data.get('action', 'verify'),
            'min_score': task.additional_data.get('min_score', 0.3)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/in.php",
                data=submit_data,
                timeout=self.timeout
            )
            
            if response.text.startswith('OK|'):
                captcha_id = response.text.split('|')[1]
            else:
                raise CAPTCHAError(f"Failed to submit reCAPTCHA v3: {response.text}")
        
        return await self._wait_for_solution(captcha_id)
    
    async def _solve_hcaptcha(self, task: CAPTCHATask) -> str:
        """Solve hCaptcha."""
        submit_data = {
            'key': self.api_key,
            'method': 'hcaptcha',
            'sitekey': task.site_key,
            'pageurl': task.page_url
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/in.php",
                data=submit_data,
                timeout=self.timeout
            )
            
            if response.text.startswith('OK|'):
                captcha_id = response.text.split('|')[1]
            else:
                raise CAPTCHAError(f"Failed to submit hCaptcha: {response.text}")
        
        return await self._wait_for_solution(captcha_id)
    
    async def _wait_for_solution(self, captcha_id: str) -> str:
        """Wait for CAPTCHA solution."""
        max_attempts = 60  # 5 minutes with 5-second intervals
        attempt = 0
        
        while attempt < max_attempts:
            await asyncio.sleep(5)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/res.php",
                    params={
                        'key': self.api_key,
                        'action': 'get',
                        'id': captcha_id
                    },
                    timeout=self.timeout
                )
            
            if response.text == 'CAPCHA_NOT_READY':
                attempt += 1
                continue
            elif response.text.startswith('OK|'):
                return response.text.split('|')[1]
            else:
                raise CAPTCHAError(f"Failed to get solution: {response.text}")
        
        raise CAPTCHAError("CAPTCHA solving timeout")
    
    async def get_balance(self) -> float:
        """Get account balance."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/res.php",
                params={
                    'key': self.api_key,
                    'action': 'getbalance'
                },
                timeout=self.timeout
            )
        
        if response.text.startswith('ERROR_'):
            raise CAPTCHAError(f"Failed to get balance: {response.text}")
        
        return float(response.text)


class AntiCaptchaProvider(CAPTCHAProvider):
    """Anti-Captcha.com provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Anti-Captcha provider."""
        super().__init__(config)
        self.base_url = "https://api.anti-captcha.com"
    
    async def solve_captcha(self, task: CAPTCHATask) -> str:
        """Solve CAPTCHA using Anti-Captcha."""
        try:
            if task.captcha_type == CAPTCHAType.IMAGE:
                return await self._solve_image_captcha(task)
            elif task.captcha_type == CAPTCHAType.RECAPTCHA_V2:
                return await self._solve_recaptcha_v2(task)
            elif task.captcha_type == CAPTCHAType.RECAPTCHA_V3:
                return await self._solve_recaptcha_v3(task)
            elif task.captcha_type == CAPTCHAType.HCAPTCHA:
                return await self._solve_hcaptcha(task)
            else:
                raise CAPTCHAError(f"Unsupported CAPTCHA type: {task.captcha_type}")
        except Exception as e:
            self.logger.error(f"Anti-Captcha solving failed: {e}")
            raise CAPTCHAError(f"Anti-Captcha solving failed: {e}")
    
    async def _solve_image_captcha(self, task: CAPTCHATask) -> str:
        """Solve image CAPTCHA."""
        # Create task
        task_data = {
            "clientKey": self.api_key,
            "task": {
                "type": "ImageToTextTask",
                "body": base64.b64encode(task.image_data).decode('utf-8')
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/createTask",
                json=task_data,
                timeout=self.timeout
            )
            
            result = response.json()
            if result.get('errorId') != 0:
                raise CAPTCHAError(f"Failed to create task: {result.get('errorDescription')}")
            
            task_id = result['taskId']
        
        # Wait for solution
        return await self._wait_for_solution(task_id)
    
    async def _solve_recaptcha_v2(self, task: CAPTCHATask) -> str:
        """Solve reCAPTCHA v2."""
        task_data = {
            "clientKey": self.api_key,
            "task": {
                "type": "NoCaptchaTaskProxyless",
                "websiteURL": task.page_url,
                "websiteKey": task.site_key
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/createTask",
                json=task_data,
                timeout=self.timeout
            )
            
            result = response.json()
            if result.get('errorId') != 0:
                raise CAPTCHAError(f"Failed to create task: {result.get('errorDescription')}")
            
            task_id = result['taskId']
        
        return await self._wait_for_solution(task_id)
    
    async def _solve_recaptcha_v3(self, task: CAPTCHATask) -> str:
        """Solve reCAPTCHA v3."""
        task_data = {
            "clientKey": self.api_key,
            "task": {
                "type": "RecaptchaV3TaskProxyless",
                "websiteURL": task.page_url,
                "websiteKey": task.site_key,
                "minScore": task.additional_data.get('min_score', 0.3),
                "pageAction": task.additional_data.get('action', 'verify')
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/createTask",
                json=task_data,
                timeout=self.timeout
            )
            
            result = response.json()
            if result.get('errorId') != 0:
                raise CAPTCHAError(f"Failed to create task: {result.get('errorDescription')}")
            
            task_id = result['taskId']
        
        return await self._wait_for_solution(task_id)
    
    async def _solve_hcaptcha(self, task: CAPTCHATask) -> str:
        """Solve hCaptcha."""
        task_data = {
            "clientKey": self.api_key,
            "task": {
                "type": "HCaptchaTaskProxyless",
                "websiteURL": task.page_url,
                "websiteKey": task.site_key
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/createTask",
                json=task_data,
                timeout=self.timeout
            )
            
            result = response.json()
            if result.get('errorId') != 0:
                raise CAPTCHAError(f"Failed to create task: {result.get('errorDescription')}")
            
            task_id = result['taskId']
        
        return await self._wait_for_solution(task_id)
    
    async def _wait_for_solution(self, task_id: int) -> str:
        """Wait for CAPTCHA solution."""
        max_attempts = 60  # 5 minutes with 5-second intervals
        attempt = 0
        
        while attempt < max_attempts:
            await asyncio.sleep(5)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/getTaskResult",
                    json={
                        "clientKey": self.api_key,
                        "taskId": task_id
                    },
                    timeout=self.timeout
                )
            
            result = response.json()
            
            if result.get('status') == 'ready':
                return result['solution']['gRecaptchaResponse']
            elif result.get('errorId') != 0:
                raise CAPTCHAError(f"Task failed: {result.get('errorDescription')}")
            
            attempt += 1
        
        raise CAPTCHAError("CAPTCHA solving timeout")
    
    async def get_balance(self) -> float:
        """Get account balance."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/getBalance",
                json={"clientKey": self.api_key},
                timeout=self.timeout
            )
        
        result = response.json()
        if result.get('errorId') != 0:
            raise CAPTCHAError(f"Failed to get balance: {result.get('errorDescription')}")
        
        return result['balance']


class CAPTCHAManager:
    """Main CAPTCHA management class."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize CAPTCHA manager.
        
        Args:
            config: CAPTCHA configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.providers: List[CAPTCHAProvider] = []
        self.current_provider_index = 0
        
        # Initialize providers
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize CAPTCHA providers."""
        provider_configs = self.config.get('providers', [])
        
        for provider_config in provider_configs:
            provider_type = provider_config.get('type')
            provider_settings = provider_config.get('settings', {})
            
            if provider_type == '2captcha':
                provider = TwoCaptchaProvider(provider_settings)
            elif provider_type == 'anticaptcha':
                provider = AntiCaptchaProvider(provider_settings)
            else:
                self.logger.warning(f"Unknown CAPTCHA provider type: {provider_type}")
                continue
            
            self.providers.append(provider)
    
    async def solve_captcha(self, task: CAPTCHATask) -> str:
        """Solve CAPTCHA using available providers.
        
        Args:
            task: CAPTCHA task to solve
            
        Returns:
            CAPTCHA solution
        """
        if not self.providers:
            raise CAPTCHAError("No CAPTCHA providers available")
        
        # Try providers in order
        for i, provider in enumerate(self.providers):
            try:
                self.logger.info(f"Attempting to solve CAPTCHA with provider {i+1}")
                solution = await provider.solve_captcha(task)
                
                # Update task
                task.solution = solution
                task.success = True
                task.solved_at = asyncio.get_event_loop().time()
                
                self.logger.info(f"CAPTCHA solved successfully with provider {i+1}")
                return solution
                
            except Exception as e:
                self.logger.warning(f"Provider {i+1} failed: {e}")
                if i == len(self.providers) - 1:
                    # Last provider failed
                    task.error = str(e)
                    task.success = False
                    raise CAPTCHAError(f"All CAPTCHA providers failed: {e}")
        
        raise CAPTCHAError("No CAPTCHA providers available")
    
    async def get_balance(self) -> Dict[str, float]:
        """Get balance for all providers.
        
        Returns:
            Dictionary of provider balances
        """
        balances = {}
        
        for i, provider in enumerate(self.providers):
            try:
                balance = await provider.get_balance()
                balances[f"provider_{i+1}"] = balance
            except Exception as e:
                self.logger.error(f"Failed to get balance for provider {i+1}: {e}")
                balances[f"provider_{i+1}"] = 0.0
        
        return balances
