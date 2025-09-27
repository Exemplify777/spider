"""Advanced security features for SPIDER framework."""

import asyncio
import time
import json
import hashlib
import hmac
import secrets
import base64
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque
import re
from datetime import datetime, timedelta
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..core.exceptions import SpiderError, SecurityError
from ..core.logger import get_logger


class SecurityLevel(Enum):
    """Security levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EncryptionAlgorithm(Enum):
    """Encryption algorithms."""
    AES_256 = "aes_256"
    RSA_2048 = "rsa_2048"
    RSA_4096 = "rsa_4096"
    FERNET = "fernet"


class HashAlgorithm(Enum):
    """Hash algorithms."""
    SHA_256 = "sha_256"
    SHA_512 = "sha_512"
    BLAKE2B = "blake2b"
    BCRYPT = "bcrypt"


@dataclass
class SecurityConfig:
    """Security configuration."""
    encryption_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.FERNET
    hash_algorithm: HashAlgorithm = HashAlgorithm.SHA_256
    jwt_secret: str = ""
    jwt_expiry_hours: int = 24
    password_min_length: int = 8
    password_require_special: bool = True
    password_require_numbers: bool = True
    password_require_uppercase: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    session_timeout_minutes: int = 60
    enable_2fa: bool = False
    enable_audit_logging: bool = True


@dataclass
class SecurityEvent:
    """Security event record."""
    event_id: str
    event_type: str
    user_id: Optional[str]
    tenant_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: float
    severity: SecurityLevel
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserSession:
    """User session information."""
    session_id: str
    user_id: str
    tenant_id: str
    created_at: float
    last_activity: float
    ip_address: str
    user_agent: str
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class PasswordValidator:
    """Password validation and hashing."""
    
    def __init__(self, config: SecurityConfig):
        """Initialize password validator.
        
        Args:
            config: Security configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check minimum length
        if len(password) < self.config.password_min_length:
            errors.append(f"Password must be at least {self.config.password_min_length} characters long")
        
        # Check for special characters
        if self.config.password_require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for numbers
        if self.config.password_require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        # Check for uppercase letters
        if self.config.password_require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for common passwords
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password.lower() in common_passwords:
            errors.append("Password is too common, please choose a stronger password")
        
        return len(errors) == 0, errors
    
    def hash_password(self, password: str) -> str:
        """Hash password using configured algorithm.
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password
        """
        if self.config.hash_algorithm == HashAlgorithm.SHA_256:
            return hashlib.sha256(password.encode()).hexdigest()
        elif self.config.hash_algorithm == HashAlgorithm.SHA_512:
            return hashlib.sha512(password.encode()).hexdigest()
        elif self.config.hash_algorithm == HashAlgorithm.BLAKE2B:
            return hashlib.blake2b(password.encode()).hexdigest()
        else:
            # Default to SHA-256
            return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash.
        
        Args:
            password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches
        """
        return self.hash_password(password) == hashed_password


class EncryptionManager:
    """Manages encryption and decryption operations."""
    
    def __init__(self, config: SecurityConfig):
        """Initialize encryption manager.
        
        Args:
            config: Security configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.fernet_key: Optional[Fernet] = None
        self.rsa_private_key: Optional[rsa.RSAPrivateKey] = None
        self.rsa_public_key: Optional[rsa.RSAPublicKey] = None
        
        self._generate_keys()
    
    def _generate_keys(self) -> None:
        """Generate encryption keys."""
        try:
            if self.config.encryption_algorithm == EncryptionAlgorithm.FERNET:
                key = Fernet.generate_key()
                self.fernet_key = Fernet(key)
            elif self.config.encryption_algorithm in [EncryptionAlgorithm.RSA_2048, EncryptionAlgorithm.RSA_4096]:
                key_size = 2048 if self.config.encryption_algorithm == EncryptionAlgorithm.RSA_2048 else 4096
                self.rsa_private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=key_size
                )
                self.rsa_public_key = self.rsa_private_key.public_key()
            
            self.logger.info(f"Generated {self.config.encryption_algorithm.value} encryption keys")
        except Exception as e:
            self.logger.error(f"Failed to generate encryption keys: {e}")
            raise SecurityError(f"Key generation failed: {e}")
    
    def encrypt(self, data: str) -> str:
        """Encrypt data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data (base64 encoded)
        """
        try:
            if self.config.encryption_algorithm == EncryptionAlgorithm.FERNET:
                if not self.fernet_key:
                    raise SecurityError("Fernet key not available")
                
                encrypted_data = self.fernet_key.encrypt(data.encode())
                return base64.b64encode(encrypted_data).decode()
            
            elif self.config.encryption_algorithm in [EncryptionAlgorithm.RSA_2048, EncryptionAlgorithm.RSA_4096]:
                if not self.rsa_public_key:
                    raise SecurityError("RSA public key not available")
                
                encrypted_data = self.rsa_public_key.encrypt(
                    data.encode(),
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                return base64.b64encode(encrypted_data).decode()
            
            else:
                raise SecurityError(f"Unsupported encryption algorithm: {self.config.encryption_algorithm}")
        
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise SecurityError(f"Encryption failed: {e}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data.
        
        Args:
            encrypted_data: Encrypted data (base64 encoded)
            
        Returns:
            Decrypted data
        """
        try:
            if self.config.encryption_algorithm == EncryptionAlgorithm.FERNET:
                if not self.fernet_key:
                    raise SecurityError("Fernet key not available")
                
                decoded_data = base64.b64decode(encrypted_data.encode())
                decrypted_data = self.fernet_key.decrypt(decoded_data)
                return decrypted_data.decode()
            
            elif self.config.encryption_algorithm in [EncryptionAlgorithm.RSA_2048, EncryptionAlgorithm.RSA_4096]:
                if not self.rsa_private_key:
                    raise SecurityError("RSA private key not available")
                
                decoded_data = base64.b64decode(encrypted_data.encode())
                decrypted_data = self.rsa_private_key.decrypt(
                    decoded_data,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                return decrypted_data.decode()
            
            else:
                raise SecurityError(f"Unsupported encryption algorithm: {self.config.encryption_algorithm}")
        
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise SecurityError(f"Decryption failed: {e}")
    
    def get_public_key(self) -> str:
        """Get public key for encryption.
        
        Returns:
            Public key (PEM format)
        """
        if not self.rsa_public_key:
            raise SecurityError("RSA public key not available")
        
        public_key_pem = self.rsa_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return public_key_pem.decode()


class JWTManager:
    """JWT token management."""
    
    def __init__(self, config: SecurityConfig):
        """Initialize JWT manager.
        
        Args:
            config: Security configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.secret_key = config.jwt_secret or secrets.token_urlsafe(32)
    
    def create_token(
        self,
        user_id: str,
        tenant_id: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create JWT token.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            additional_claims: Additional claims
            
        Returns:
            JWT token
        """
        try:
            now = time.time()
            expiry = now + (self.config.jwt_expiry_hours * 3600)
            
            payload = {
                'user_id': user_id,
                'tenant_id': tenant_id,
                'iat': now,
                'exp': expiry,
                'jti': secrets.token_urlsafe(16)
            }
            
            if additional_claims:
                payload.update(additional_claims)
            
            token = jwt.encode(payload, self.secret_key, algorithm='HS256')
            return token
        
        except Exception as e:
            self.logger.error(f"Token creation failed: {e}")
            raise SecurityError(f"Token creation failed: {e}")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            Token payload
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        
        except jwt.ExpiredSignatureError:
            raise SecurityError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise SecurityError(f"Invalid token: {e}")
        except Exception as e:
            self.logger.error(f"Token verification failed: {e}")
            raise SecurityError(f"Token verification failed: {e}")
    
    def refresh_token(self, token: str) -> str:
        """Refresh JWT token.
        
        Args:
            token: Current JWT token
            
        Returns:
            New JWT token
        """
        try:
            payload = self.verify_token(token)
            return self.create_token(
                payload['user_id'],
                payload['tenant_id'],
                {k: v for k, v in payload.items() if k not in ['iat', 'exp', 'jti']}
            )
        
        except SecurityError:
            raise
        except Exception as e:
            self.logger.error(f"Token refresh failed: {e}")
            raise SecurityError(f"Token refresh failed: {e}")


class SessionManager:
    """Manages user sessions."""
    
    def __init__(self, config: SecurityConfig):
        """Initialize session manager.
        
        Args:
            config: Security configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.sessions: Dict[str, UserSession] = {}
        self.user_sessions: Dict[str, List[str]] = defaultdict(list)
        self.lock = threading.RLock()
    
    def create_session(
        self,
        user_id: str,
        tenant_id: str,
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserSession:
        """Create user session.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            ip_address: IP address
            user_agent: User agent
            metadata: Optional metadata
            
        Returns:
            User session
        """
        with self.lock:
            session_id = secrets.token_urlsafe(32)
            current_time = time.time()
            
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                tenant_id=tenant_id,
                created_at=current_time,
                last_activity=current_time,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            self.sessions[session_id] = session
            self.user_sessions[user_id].append(session_id)
            
            self.logger.info(f"Created session for user {user_id}")
            return session
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            User session or None
        """
        with self.lock:
            return self.sessions.get(session_id)
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if updated, False if not found
        """
        with self.lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            session.last_activity = time.time()
            return True
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if invalidated, False if not found
        """
        with self.lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            session.is_active = False
            del self.sessions[session_id]
            
            # Remove from user sessions
            if session.user_id in self.user_sessions:
                try:
                    self.user_sessions[session.user_id].remove(session_id)
                except ValueError:
                    pass
            
            self.logger.info(f"Invalidated session {session_id}")
            return True
    
    def invalidate_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions invalidated
        """
        with self.lock:
            session_ids = self.user_sessions.get(user_id, [])
            invalidated_count = 0
            
            for session_id in session_ids[:]:  # Copy to avoid modification during iteration
                if self.invalidate_session(session_id):
                    invalidated_count += 1
            
            return invalidated_count
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        with self.lock:
            current_time = time.time()
            timeout_seconds = self.config.session_timeout_minutes * 60
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                if current_time - session.last_activity > timeout_seconds:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self.invalidate_session(session_id)
            
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            return len(expired_sessions)
    
    def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of user sessions
        """
        with self.lock:
            session_ids = self.user_sessions.get(user_id, [])
            sessions = []
            
            for session_id in session_ids:
                session = self.sessions.get(session_id)
                if session and session.is_active:
                    sessions.append(session)
            
            return sessions


class AuditLogger:
    """Security audit logging."""
    
    def __init__(self, config: SecurityConfig):
        """Initialize audit logger.
        
        Args:
            config: Security configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.audit_events: deque = deque(maxlen=10000)
        self.lock = threading.RLock()
    
    def log_event(
        self,
        event_type: str,
        user_id: Optional[str],
        tenant_id: Optional[str],
        ip_address: str,
        user_agent: str,
        severity: SecurityLevel,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log security event.
        
        Args:
            event_type: Event type
            user_id: User ID
            tenant_id: Tenant ID
            ip_address: IP address
            user_agent: User agent
            severity: Security level
            description: Event description
            metadata: Optional metadata
        """
        if not self.config.enable_audit_logging:
            return
        
        with self.lock:
            event = SecurityEvent(
                event_id=secrets.token_urlsafe(16),
                event_type=event_type,
                user_id=user_id,
                tenant_id=tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=time.time(),
                severity=severity,
                description=description,
                metadata=metadata or {}
            )
            
            self.audit_events.append(event)
            
            # Log based on severity
            if severity == SecurityLevel.CRITICAL:
                self.logger.critical(f"SECURITY EVENT: {description}")
            elif severity == SecurityLevel.HIGH:
                self.logger.error(f"SECURITY EVENT: {description}")
            elif severity == SecurityLevel.MEDIUM:
                self.logger.warning(f"SECURITY EVENT: {description}")
            else:
                self.logger.info(f"SECURITY EVENT: {description}")
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        severity: Optional[SecurityLevel] = None,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """Get audit events with filters.
        
        Args:
            event_type: Optional event type filter
            user_id: Optional user ID filter
            tenant_id: Optional tenant ID filter
            severity: Optional severity filter
            limit: Maximum number of events
            
        Returns:
            List of security events
        """
        with self.lock:
            events = list(self.audit_events)
            
            # Apply filters
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            
            if user_id:
                events = [e for e in events if e.user_id == user_id]
            
            if tenant_id:
                events = [e for e in events if e.tenant_id == tenant_id]
            
            if severity:
                events = [e for e in events if e.severity == severity]
            
            # Sort by timestamp (newest first) and limit
            events.sort(key=lambda e: e.timestamp, reverse=True)
            return events[:limit]
    
    def get_security_statistics(self) -> Dict[str, Any]:
        """Get security statistics.
        
        Returns:
            Security statistics
        """
        with self.lock:
            events = list(self.audit_events)
            
            if not events:
                return {
                    "total_events": 0,
                    "events_by_type": {},
                    "events_by_severity": {},
                    "recent_events": 0
                }
            
            # Count by type
            events_by_type = defaultdict(int)
            for event in events:
                events_by_type[event.event_type] += 1
            
            # Count by severity
            events_by_severity = defaultdict(int)
            for event in events:
                events_by_severity[event.severity.value] += 1
            
            # Recent events (last 24 hours)
            current_time = time.time()
            recent_events = len([
                e for e in events
                if current_time - e.timestamp < 86400  # 24 hours
            ])
            
            return {
                "total_events": len(events),
                "events_by_type": dict(events_by_type),
                "events_by_severity": dict(events_by_severity),
                "recent_events": recent_events
            }


class SecurityManager:
    """Main security manager."""
    
    def __init__(self, config: SecurityConfig):
        """Initialize security manager.
        
        Args:
            config: Security configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize components
        self.password_validator = PasswordValidator(config)
        self.encryption_manager = EncryptionManager(config)
        self.jwt_manager = JWTManager(config)
        self.session_manager = SessionManager(config)
        self.audit_logger = AuditLogger(config)
        
        # Login attempt tracking
        self.login_attempts: Dict[str, List[float]] = defaultdict(list)
        self.locked_accounts: Dict[str, float] = {}
        self.lock = threading.RLock()
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        return self.password_validator.validate_password(password)
    
    def hash_password(self, password: str) -> str:
        """Hash password.
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password
        """
        return self.password_validator.hash_password(password)
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password.
        
        Args:
            password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches
        """
        return self.password_validator.verify_password(password, hashed_password)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data
        """
        return self.encryption_manager.encrypt(data)
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data.
        
        Args:
            encrypted_data: Encrypted data
            
        Returns:
            Decrypted data
        """
        return self.encryption_manager.decrypt(encrypted_data)
    
    def create_token(self, user_id: str, tenant_id: str, **kwargs) -> str:
        """Create JWT token.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            **kwargs: Additional claims
            
        Returns:
            JWT token
        """
        return self.jwt_manager.create_token(user_id, tenant_id, kwargs)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            Token payload
        """
        return self.jwt_manager.verify_token(token)
    
    def create_session(
        self,
        user_id: str,
        tenant_id: str,
        ip_address: str,
        user_agent: str,
        **kwargs
    ) -> UserSession:
        """Create user session.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            ip_address: IP address
            user_agent: User agent
            **kwargs: Additional metadata
            
        Returns:
            User session
        """
        return self.session_manager.create_session(
            user_id, tenant_id, ip_address, user_agent, kwargs
        )
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            User session or None
        """
        return self.session_manager.get_session(session_id)
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if invalidated
        """
        return self.session_manager.invalidate_session(session_id)
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str],
        tenant_id: Optional[str],
        ip_address: str,
        user_agent: str,
        severity: SecurityLevel,
        description: str,
        **kwargs
    ) -> None:
        """Log security event.
        
        Args:
            event_type: Event type
            user_id: User ID
            tenant_id: Tenant ID
            ip_address: IP address
            user_agent: User agent
            severity: Security level
            description: Event description
            **kwargs: Additional metadata
        """
        self.audit_logger.log_event(
            event_type, user_id, tenant_id, ip_address, user_agent,
            severity, description, kwargs
        )
    
    def check_login_attempts(self, user_id: str, ip_address: str) -> bool:
        """Check if login attempts are within limits.
        
        Args:
            user_id: User ID
            ip_address: IP address
            
        Returns:
            True if login allowed
        """
        with self.lock:
            current_time = time.time()
            lockout_duration = self.config.lockout_duration_minutes * 60
            
            # Check if account is locked
            if user_id in self.locked_accounts:
                if current_time - self.locked_accounts[user_id] < lockout_duration:
                    return False
                else:
                    del self.locked_accounts[user_id]
            
            # Check recent attempts
            attempts = self.login_attempts[user_id]
            recent_attempts = [
                attempt for attempt in attempts
                if current_time - attempt < lockout_duration
            ]
            
            if len(recent_attempts) >= self.config.max_login_attempts:
                self.locked_accounts[user_id] = current_time
                self.log_security_event(
                    "account_locked", user_id, None, ip_address, "",
                    SecurityLevel.HIGH, f"Account locked due to too many login attempts"
                )
                return False
            
            return True
    
    def record_login_attempt(self, user_id: str, ip_address: str, success: bool) -> None:
        """Record login attempt.
        
        Args:
            user_id: User ID
            ip_address: IP address
            success: Whether login was successful
        """
        with self.lock:
            current_time = time.time()
            
            if success:
                # Clear failed attempts on successful login
                if user_id in self.login_attempts:
                    del self.login_attempts[user_id]
                if user_id in self.locked_accounts:
                    del self.locked_accounts[user_id]
            else:
                # Record failed attempt
                self.login_attempts[user_id].append(current_time)
                
                # Log failed attempt
                self.log_security_event(
                    "login_failed", user_id, None, ip_address, "",
                    SecurityLevel.MEDIUM, f"Failed login attempt for user {user_id}"
                )
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired security data.
        
        Returns:
            Cleanup statistics
        """
        with self.lock:
            current_time = time.time()
            lockout_duration = self.config.lockout_duration_minutes * 60
            
            # Clean up expired login attempts
            expired_attempts = 0
            for user_id, attempts in list(self.login_attempts.items()):
                recent_attempts = [
                    attempt for attempt in attempts
                    if current_time - attempt < lockout_duration
                ]
                if recent_attempts:
                    self.login_attempts[user_id] = recent_attempts
                else:
                    del self.login_attempts[user_id]
                    expired_attempts += 1
            
            # Clean up expired account locks
            expired_locks = 0
            for user_id, lock_time in list(self.locked_accounts.items()):
                if current_time - lock_time >= lockout_duration:
                    del self.locked_accounts[user_id]
                    expired_locks += 1
            
            # Clean up expired sessions
            expired_sessions = self.session_manager.cleanup_expired_sessions()
            
            return {
                "expired_attempts": expired_attempts,
                "expired_locks": expired_locks,
                "expired_sessions": expired_sessions
            }
