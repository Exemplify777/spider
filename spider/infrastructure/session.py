"""Session management infrastructure for SPIDER framework."""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from urllib.parse import urlparse

from ..core.exceptions import SpiderError
from ..core.logger import get_logger


@dataclass
class Cookie:
    """Cookie representation."""
    name: str
    value: str
    domain: str
    path: str = "/"
    expires: Optional[float] = None
    secure: bool = False
    http_only: bool = False
    same_site: str = "Lax"
    
    def is_expired(self) -> bool:
        """Check if cookie is expired."""
        if self.expires is None:
            return False
        return time.time() > self.expires
    
    def matches_domain(self, domain: str) -> bool:
        """Check if cookie matches domain."""
        if self.domain.startswith('.'):
            return domain.endswith(self.domain[1:]) or domain == self.domain[1:]
        return domain == self.domain
    
    def matches_path(self, path: str) -> bool:
        """Check if cookie matches path."""
        return path.startswith(self.path)


@dataclass
class Session:
    """Session representation."""
    session_id: str
    cookies: Dict[str, Cookie]
    headers: Dict[str, str]
    created_at: float
    last_used: float
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def get_cookies_for_domain(self, domain: str, path: str = "/") -> Dict[str, str]:
        """Get cookies for specific domain and path."""
        result = {}
        for cookie in self.cookies.values():
            if not cookie.is_expired() and cookie.matches_domain(domain) and cookie.matches_path(path):
                result[cookie.name] = cookie.value
        return result
    
    def add_cookie(self, cookie: Cookie) -> None:
        """Add cookie to session."""
        self.cookies[cookie.name] = cookie
        self.last_used = time.time()
    
    def remove_cookie(self, name: str) -> None:
        """Remove cookie from session."""
        if name in self.cookies:
            del self.cookies[name]
            self.last_used = time.time()
    
    def clear_expired_cookies(self) -> None:
        """Remove expired cookies from session."""
        expired_cookies = [name for name, cookie in self.cookies.items() if cookie.is_expired()]
        for name in expired_cookies:
            del self.cookies[name]


class BaseSessionManager(ABC):
    """Base class for session managers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize session manager.
        
        Args:
            config: Session manager configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    async def create_session(self, session_id: str) -> Session:
        """Create a new session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            New session instance
        """
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get existing session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session instance or None if not found
        """
        pass
    
    @abstractmethod
    async def save_session(self, session: Session) -> None:
        """Save session to storage.
        
        Args:
            session: Session to save
        """
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        """Delete session from storage.
        
        Args:
            session_id: Session identifier
        """
        pass


class InMemorySessionManager(BaseSessionManager):
    """In-memory session manager implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize in-memory session manager."""
        super().__init__(config)
        self.sessions: Dict[str, Session] = {}
        self.max_sessions = config.get('max_sessions', 1000)
        self.session_timeout = config.get('session_timeout', 3600)  # 1 hour
    
    async def create_session(self, session_id: str) -> Session:
        """Create a new session."""
        current_time = time.time()
        session = Session(
            session_id=session_id,
            cookies={},
            headers={},
            created_at=current_time,
            last_used=current_time,
            expires_at=current_time + self.session_timeout
        )
        
        self.sessions[session_id] = session
        self.logger.info(f"Created session: {session_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get existing session."""
        session = self.sessions.get(session_id)
        
        if session is None:
            return None
        
        if session.is_expired():
            await self.delete_session(session_id)
            return None
        
        # Update last used time
        session.last_used = time.time()
        return session
    
    async def save_session(self, session: Session) -> None:
        """Save session to memory."""
        if session.session_id in self.sessions:
            self.sessions[session_id] = session
            self.logger.debug(f"Updated session: {session.session_id}")
    
    async def delete_session(self, session_id: str) -> None:
        """Delete session from memory."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"Deleted session: {session_id}")
    
    async def cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired()
        ]
        
        for session_id in expired_sessions:
            await self.delete_session(session_id)
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")


class RedisSessionManager(BaseSessionManager):
    """Redis-based session manager implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Redis session manager."""
        super().__init__(config)
        self.redis_url = config.get('redis_url', 'redis://localhost:6379')
        self.session_timeout = config.get('session_timeout', 3600)
        self.redis_client = None
    
    async def _get_redis_client(self):
        """Get Redis client connection."""
        if self.redis_client is None:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(self.redis_url)
        return self.redis_client
    
    async def create_session(self, session_id: str) -> Session:
        """Create a new session."""
        current_time = time.time()
        session = Session(
            session_id=session_id,
            cookies={},
            headers={},
            created_at=current_time,
            last_used=current_time,
            expires_at=current_time + self.session_timeout
        )
        
        await self.save_session(session)
        self.logger.info(f"Created session: {session_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get existing session."""
        redis_client = await self._get_redis_client()
        session_data = await redis_client.get(f"session:{session_id}")
        
        if session_data is None:
            return None
        
        try:
            session_dict = json.loads(session_data)
            
            # Reconstruct session
            session = Session(
                session_id=session_dict['session_id'],
                cookies={},
                headers=session_dict.get('headers', {}),
                created_at=session_dict['created_at'],
                last_used=session_dict['last_used'],
                expires_at=session_dict.get('expires_at'),
                metadata=session_dict.get('metadata', {})
            )
            
            # Reconstruct cookies
            for cookie_data in session_dict.get('cookies', []):
                cookie = Cookie(
                    name=cookie_data['name'],
                    value=cookie_data['value'],
                    domain=cookie_data['domain'],
                    path=cookie_data.get('path', '/'),
                    expires=cookie_data.get('expires'),
                    secure=cookie_data.get('secure', False),
                    http_only=cookie_data.get('http_only', False),
                    same_site=cookie_data.get('same_site', 'Lax')
                )
                session.cookies[cookie.name] = cookie
            
            if session.is_expired():
                await self.delete_session(session_id)
                return None
            
            # Update last used time
            session.last_used = time.time()
            await self.save_session(session)
            
            return session
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to deserialize session {session_id}: {e}")
            await self.delete_session(session_id)
            return None
    
    async def save_session(self, session: Session) -> None:
        """Save session to Redis."""
        redis_client = await self._get_redis_client()
        
        # Prepare session data
        session_dict = {
            'session_id': session.session_id,
            'headers': session.headers,
            'created_at': session.created_at,
            'last_used': session.last_used,
            'expires_at': session.expires_at,
            'metadata': session.metadata,
            'cookies': []
        }
        
        # Add cookies
        for cookie in session.cookies.values():
            cookie_data = {
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path,
                'expires': cookie.expires,
                'secure': cookie.secure,
                'http_only': cookie.http_only,
                'same_site': cookie.same_site
            }
            session_dict['cookies'].append(cookie_data)
        
        # Save to Redis with expiration
        session_data = json.dumps(session_dict)
        await redis_client.setex(
            f"session:{session.session_id}",
            self.session_timeout,
            session_data
        )
        
        self.logger.debug(f"Saved session: {session.session_id}")
    
    async def delete_session(self, session_id: str) -> None:
        """Delete session from Redis."""
        redis_client = await self._get_redis_client()
        await redis_client.delete(f"session:{session_id}")
        self.logger.info(f"Deleted session: {session_id}")


class CookieManager:
    """Cookie management utilities."""
    
    def __init__(self, session_manager: BaseSessionManager):
        """Initialize cookie manager.
        
        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
        self.logger = get_logger(self.__class__.__name__)
    
    async def parse_set_cookie(self, set_cookie_header: str, domain: str, path: str = "/") -> Cookie:
        """Parse Set-Cookie header and create Cookie object.
        
        Args:
            set_cookie_header: Set-Cookie header value
            domain: Domain for the cookie
            path: Path for the cookie
            
        Returns:
            Cookie object
        """
        parts = set_cookie_header.split(';')
        name_value = parts[0].strip().split('=', 1)
        
        if len(name_value) != 2:
            raise ValueError(f"Invalid Set-Cookie header: {set_cookie_header}")
        
        name, value = name_value
        
        # Parse attributes
        expires = None
        secure = False
        http_only = False
        same_site = "Lax"
        cookie_path = path
        
        for part in parts[1:]:
            part = part.strip().lower()
            if part.startswith('expires='):
                try:
                    from email.utils import parsedate_to_datetime
                    expires = parsedate_to_datetime(part[8:]).timestamp()
                except Exception:
                    pass
            elif part.startswith('max-age='):
                try:
                    max_age = int(part[8:])
                    expires = time.time() + max_age
                except ValueError:
                    pass
            elif part == 'secure':
                secure = True
            elif part == 'httponly':
                http_only = True
            elif part.startswith('samesite='):
                same_site = part[9:].capitalize()
            elif part.startswith('path='):
                cookie_path = part[5:]
        
        return Cookie(
            name=name,
            value=value,
            domain=domain,
            path=cookie_path,
            expires=expires,
            secure=secure,
            http_only=http_only,
            same_site=same_site
        )
    
    async def update_session_cookies(self, session: Session, response_headers: Dict[str, str], url: str) -> None:
        """Update session cookies from response headers.
        
        Args:
            session: Session to update
            response_headers: HTTP response headers
            url: Request URL
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path or "/"
        
        set_cookie_headers = response_headers.get('set-cookie', [])
        if isinstance(set_cookie_headers, str):
            set_cookie_headers = [set_cookie_headers]
        
        for set_cookie_header in set_cookie_headers:
            try:
                cookie = await self.parse_set_cookie(set_cookie_header, domain, path)
                session.add_cookie(cookie)
                self.logger.debug(f"Added cookie: {cookie.name}={cookie.value}")
            except Exception as e:
                self.logger.warning(f"Failed to parse cookie: {set_cookie_header}, error: {e}")
        
        # Clean up expired cookies
        session.clear_expired_cookies()
    
    async def get_cookies_for_url(self, session: Session, url: str) -> Dict[str, str]:
        """Get cookies for specific URL.
        
        Args:
            session: Session to get cookies from
            url: URL to get cookies for
            
        Returns:
            Dictionary of cookie name-value pairs
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path or "/"
        
        return session.get_cookies_for_domain(domain, path)


class SessionManager:
    """Main session management class."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize session manager.
        
        Args:
            config: Session manager configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.enabled = config.get('enabled', True)
        
        if not self.enabled:
            self.session_manager = None
            self.cookie_manager = None
            return
        
        # Create session manager based on config
        session_type = config.get('type', 'memory')
        session_config = config.get('settings', {})
        
        if session_type == 'memory':
            self.session_manager = InMemorySessionManager(session_config)
        elif session_type == 'redis':
            self.session_manager = RedisSessionManager(session_config)
        else:
            raise ValueError(f"Unknown session manager type: {session_type}")
        
        self.cookie_manager = CookieManager(self.session_manager)
        
        # Start cleanup task if using in-memory manager
        if session_type == 'memory':
            asyncio.create_task(self._cleanup_task())
    
    async def create_session(self, session_id: str) -> Optional[Session]:
        """Create a new session."""
        if not self.enabled or not self.session_manager:
            return None
        
        return await self.session_manager.create_session(session_id)
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get existing session."""
        if not self.enabled or not self.session_manager:
            return None
        
        return await self.session_manager.get_session(session_id)
    
    async def save_session(self, session: Session) -> None:
        """Save session."""
        if not self.enabled or not self.session_manager:
            return
        
        await self.session_manager.save_session(session)
    
    async def delete_session(self, session_id: str) -> None:
        """Delete session."""
        if not self.enabled or not self.session_manager:
            return
        
        await self.session_manager.delete_session(session_id)
    
    async def update_cookies(self, session: Session, response_headers: Dict[str, str], url: str) -> None:
        """Update session cookies from response."""
        if not self.enabled or not self.cookie_manager:
            return
        
        await self.cookie_manager.update_session_cookies(session, response_headers, url)
    
    async def get_cookies_for_url(self, session: Session, url: str) -> Dict[str, str]:
        """Get cookies for URL."""
        if not self.enabled or not self.cookie_manager:
            return {}
        
        return await self.cookie_manager.get_cookies_for_url(session, url)
    
    async def _cleanup_task(self) -> None:
        """Background task to clean up expired sessions."""
        while True:
            try:
                if hasattr(self.session_manager, 'cleanup_expired_sessions'):
                    await self.session_manager.cleanup_expired_sessions()
                await asyncio.sleep(300)  # Clean up every 5 minutes
            except Exception as e:
                self.logger.error(f"Session cleanup task error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
