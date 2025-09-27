"""Advanced user management for SPIDER framework."""

import asyncio
import time
import json
import uuid
import hashlib
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta

from ..core.exceptions import SpiderError, ValidationError, SecurityError
from ..core.logger import get_logger


class UserStatus(Enum):
    """User status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    LOCKED = "locked"
    EXPIRED = "expired"


class UserRole(Enum):
    """User roles."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(Enum):
    """Permissions."""
    # User management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    
    # Tenant management
    CREATE_TENANT = "create_tenant"
    READ_TENANT = "read_tenant"
    UPDATE_TENANT = "update_tenant"
    DELETE_TENANT = "delete_tenant"
    
    # Scraping operations
    CREATE_SCRAPER = "create_scraper"
    READ_SCRAPER = "read_scraper"
    UPDATE_SCRAPER = "update_scraper"
    DELETE_SCRAPER = "delete_scraper"
    EXECUTE_SCRAPER = "execute_scraper"
    
    # Data operations
    READ_DATA = "read_data"
    EXPORT_DATA = "export_data"
    DELETE_DATA = "delete_data"
    
    # System operations
    READ_LOGS = "read_logs"
    READ_METRICS = "read_metrics"
    UPDATE_CONFIG = "update_config"
    MANAGE_SYSTEM = "manage_system"
    
    # Compliance
    READ_COMPLIANCE = "read_compliance"
    MANAGE_COMPLIANCE = "manage_compliance"
    EXPORT_AUDIT = "export_audit"


@dataclass
class UserProfile:
    """User profile information."""
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class User:
    """User information."""
    user_id: str
    username: str
    email: str
    password_hash: str
    profile: UserProfile
    role: UserRole
    status: UserStatus
    tenant_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_login: Optional[float] = None
    last_activity: Optional[float] = None
    login_attempts: int = 0
    locked_until: Optional[float] = None
    password_changed_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Role:
    """Role definition."""
    role_id: str
    name: str
    description: str
    permissions: List[Permission]
    is_system_role: bool = False
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class UserGroup:
    """User group."""
    group_id: str
    name: str
    description: str
    members: List[str] = field(default_factory=list)
    permissions: List[Permission] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class UserSession:
    """User session."""
    session_id: str
    user_id: str
    tenant_id: Optional[str]
    created_at: float
    last_activity: float
    ip_address: str
    user_agent: str
    is_active: bool = True
    expires_at: Optional[float] = None


class UserManager:
    """Manages users and user operations."""
    
    def __init__(self):
        """Initialize user manager."""
        self.logger = get_logger(self.__class__.__name__)
        self.users: Dict[str, User] = {}
        self.roles: Dict[str, Role] = {}
        self.groups: Dict[str, UserGroup] = {}
        self.sessions: Dict[str, UserSession] = {}
        self.user_sessions: Dict[str, List[str]] = defaultdict(list)
        self.lock = threading.RLock()
        
        # Setup default roles
        self._setup_default_roles()
    
    def _setup_default_roles(self) -> None:
        """Setup default roles."""
        default_roles = [
            Role(
                role_id="super_admin",
                name="Super Administrator",
                description="Full system access",
                permissions=list(Permission),
                is_system_role=True
            ),
            Role(
                role_id="admin",
                name="Administrator",
                description="Administrative access",
                permissions=[
                    Permission.CREATE_USER, Permission.READ_USER, Permission.UPDATE_USER,
                    Permission.CREATE_TENANT, Permission.READ_TENANT, Permission.UPDATE_TENANT,
                    Permission.CREATE_SCRAPER, Permission.READ_SCRAPER, Permission.UPDATE_SCRAPER,
                    Permission.DELETE_SCRAPER, Permission.EXECUTE_SCRAPER,
                    Permission.READ_DATA, Permission.EXPORT_DATA, Permission.DELETE_DATA,
                    Permission.READ_LOGS, Permission.READ_METRICS, Permission.UPDATE_CONFIG,
                    Permission.MANAGE_SYSTEM,
                    Permission.READ_COMPLIANCE, Permission.MANAGE_COMPLIANCE, Permission.EXPORT_AUDIT
                ]
            ),
            Role(
                role_id="manager",
                name="Manager",
                description="Management access",
                permissions=[
                    Permission.READ_USER, Permission.UPDATE_USER,
                    Permission.READ_TENANT,
                    Permission.CREATE_SCRAPER, Permission.READ_SCRAPER, Permission.UPDATE_SCRAPER,
                    Permission.EXECUTE_SCRAPER,
                    Permission.READ_DATA, Permission.EXPORT_DATA,
                    Permission.READ_LOGS, Permission.READ_METRICS,
                    Permission.READ_COMPLIANCE
                ]
            ),
            Role(
                role_id="user",
                name="User",
                description="Standard user access",
                permissions=[
                    Permission.READ_USER,
                    Permission.CREATE_SCRAPER, Permission.READ_SCRAPER, Permission.UPDATE_SCRAPER,
                    Permission.EXECUTE_SCRAPER,
                    Permission.READ_DATA, Permission.EXPORT_DATA,
                    Permission.READ_LOGS, Permission.READ_METRICS
                ]
            ),
            Role(
                role_id="viewer",
                name="Viewer",
                description="Read-only access",
                permissions=[
                    Permission.READ_USER,
                    Permission.READ_TENANT,
                    Permission.READ_SCRAPER,
                    Permission.READ_DATA,
                    Permission.READ_LOGS, Permission.READ_METRICS
                ]
            ),
            Role(
                role_id="guest",
                name="Guest",
                description="Limited access",
                permissions=[
                    Permission.READ_SCRAPER,
                    Permission.READ_DATA
                ]
            )
        ]
        
        for role in default_roles:
            self.roles[role.role_id] = role
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        profile: UserProfile,
        role: UserRole,
        tenant_id: Optional[str] = None
    ) -> User:
        """Create new user.
        
        Args:
            username: Username
            email: Email address
            password: Plain text password
            profile: User profile
            role: User role
            tenant_id: Optional tenant ID
            
        Returns:
            Created user
        """
        with self.lock:
            # Check if user already exists
            if self._get_user_by_username(username):
                raise ValidationError(f"User with username '{username}' already exists")
            
            if self._get_user_by_email(email):
                raise ValidationError(f"User with email '{email}' already exists")
            
            # Hash password
            password_hash = self._hash_password(password)
            
            # Create user
            user_id = str(uuid.uuid4())
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                profile=profile,
                role=role,
                status=UserStatus.PENDING,
                tenant_id=tenant_id
            )
            
            self.users[user_id] = user
            self.logger.info(f"Created user: {username} ({user_id})")
            
            return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User or None if not found
        """
        with self.lock:
            return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User or None if not found
        """
        with self.lock:
            return self._get_user_by_username(username)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: Email address
            
        Returns:
            User or None if not found
        """
        with self.lock:
            return self._get_user_by_email(email)
    
    def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username (internal method)."""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email (internal method)."""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """Update user information.
        
        Args:
            user_id: User ID
            **kwargs: Fields to update
            
        Returns:
            True if updated, False if not found
        """
        with self.lock:
            if user_id not in self.users:
                return False
            
            user = self.users[user_id]
            
            # Update allowed fields
            allowed_fields = ['username', 'email', 'profile', 'role', 'status', 'tenant_id', 'metadata']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(user, field, value)
            
            user.updated_at = time.time()
            self.logger.info(f"Updated user: {user_id}")
            
            return True
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if user_id not in self.users:
                return False
            
            user = self.users[user_id]
            
            # Invalidate all user sessions
            self._invalidate_user_sessions(user_id)
            
            # Remove from groups
            for group in self.groups.values():
                if user_id in group.members:
                    group.members.remove(user_id)
            
            del self.users[user_id]
            self.logger.info(f"Deleted user: {user_id}")
            
            return True
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User if authenticated, None otherwise
        """
        with self.lock:
            # Find user by username or email
            user = self._get_user_by_username(username)
            if not user:
                user = self._get_user_by_email(username)
            
            if not user:
                return None
            
            # Check if user is locked
            if user.locked_until and time.time() < user.locked_until:
                self.logger.warning(f"User {username} is locked until {user.locked_until}")
                return None
            
            # Check user status
            if user.status not in [UserStatus.ACTIVE, UserStatus.PENDING]:
                self.logger.warning(f"User {username} has status {user.status.value}")
                return None
            
            # Verify password
            if not self._verify_password(password, user.password_hash):
                # Increment login attempts
                user.login_attempts += 1
                
                # Lock user after 5 failed attempts
                if user.login_attempts >= 5:
                    user.locked_until = time.time() + 900  # 15 minutes
                    user.status = UserStatus.LOCKED
                    self.logger.warning(f"User {username} locked due to too many failed attempts")
                
                return None
            
            # Reset login attempts and update last login
            user.login_attempts = 0
            user.locked_until = None
            user.last_login = time.time()
            user.last_activity = time.time()
            
            if user.status == UserStatus.PENDING:
                user.status = UserStatus.ACTIVE
            
            self.logger.info(f"User {username} authenticated successfully")
            return user
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            True if changed, False if old password incorrect
        """
        with self.lock:
            if user_id not in self.users:
                return False
            
            user = self.users[user_id]
            
            # Verify old password
            if not self._verify_password(old_password, user.password_hash):
                return False
            
            # Hash new password
            user.password_hash = self._hash_password(new_password)
            user.password_changed_at = time.time()
            user.updated_at = time.time()
            
            # Invalidate all user sessions
            self._invalidate_user_sessions(user_id)
            
            self.logger.info(f"Password changed for user: {user_id}")
            return True
    
    def reset_password(self, user_id: str, new_password: str) -> bool:
        """Reset user password (admin function).
        
        Args:
            user_id: User ID
            new_password: New password
            
        Returns:
            True if reset, False if user not found
        """
        with self.lock:
            if user_id not in self.users:
                return False
            
            user = self.users[user_id]
            user.password_hash = self._hash_password(new_password)
            user.password_changed_at = time.time()
            user.updated_at = time.time()
            user.login_attempts = 0
            user.locked_until = None
            
            # Invalidate all user sessions
            self._invalidate_user_sessions(user_id)
            
            self.logger.info(f"Password reset for user: {user_id}")
            return True
    
    def create_session(
        self,
        user_id: str,
        tenant_id: Optional[str],
        ip_address: str,
        user_agent: str,
        expires_in: int = 3600
    ) -> UserSession:
        """Create user session.
        
        Args:
            user_id: User ID
            tenant_id: Optional tenant ID
            ip_address: IP address
            user_agent: User agent
            expires_in: Session expiry in seconds
            
        Returns:
            User session
        """
        with self.lock:
            session_id = str(uuid.uuid4())
            current_time = time.time()
            
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                tenant_id=tenant_id,
                created_at=current_time,
                last_activity=current_time,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=current_time + expires_in
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
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if invalidated, False if not found
        """
        with self.lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
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
    
    def _invalidate_user_sessions(self, user_id: str) -> None:
        """Invalidate all sessions for user.
        
        Args:
            user_id: User ID
        """
        session_ids = self.user_sessions.get(user_id, [])
        for session_id in session_ids[:]:  # Copy to avoid modification during iteration
            self.invalidate_session(session_id)
    
    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has permission.
        
        Args:
            user_id: User ID
            permission: Permission to check
            
        Returns:
            True if user has permission
        """
        with self.lock:
            user = self.get_user(user_id)
            if not user:
                return False
            
            # Get user role
            role = self.roles.get(user.role.value)
            if not role:
                return False
            
            # Check role permissions
            if permission in role.permissions:
                return True
            
            # Check group permissions
            for group in self.groups.values():
                if user_id in group.members and permission in group.permissions:
                    return True
            
            return False
    
    def create_group(
        self,
        name: str,
        description: str,
        permissions: Optional[List[Permission]] = None
    ) -> UserGroup:
        """Create user group.
        
        Args:
            name: Group name
            description: Group description
            permissions: Optional permissions
            
        Returns:
            Created group
        """
        with self.lock:
            group_id = str(uuid.uuid4())
            
            group = UserGroup(
                group_id=group_id,
                name=name,
                description=description,
                permissions=permissions or []
            )
            
            self.groups[group_id] = group
            self.logger.info(f"Created group: {name} ({group_id})")
            
            return group
    
    def add_user_to_group(self, user_id: str, group_id: str) -> bool:
        """Add user to group.
        
        Args:
            user_id: User ID
            group_id: Group ID
            
        Returns:
            True if added, False if user or group not found
        """
        with self.lock:
            if user_id not in self.users or group_id not in self.groups:
                return False
            
            group = self.groups[group_id]
            if user_id not in group.members:
                group.members.append(user_id)
                group.updated_at = time.time()
                self.logger.info(f"Added user {user_id} to group {group_id}")
            
            return True
    
    def remove_user_from_group(self, user_id: str, group_id: str) -> bool:
        """Remove user from group.
        
        Args:
            user_id: User ID
            group_id: Group ID
            
        Returns:
            True if removed, False if user or group not found
        """
        with self.lock:
            if user_id not in self.users or group_id not in self.groups:
                return False
            
            group = self.groups[group_id]
            if user_id in group.members:
                group.members.remove(user_id)
                group.updated_at = time.time()
                self.logger.info(f"Removed user {user_id} from group {group_id}")
            
            return True
    
    def get_user_permissions(self, user_id: str) -> List[Permission]:
        """Get all permissions for user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of permissions
        """
        with self.lock:
            user = self.get_user(user_id)
            if not user:
                return []
            
            permissions = set()
            
            # Get role permissions
            role = self.roles.get(user.role.value)
            if role:
                permissions.update(role.permissions)
            
            # Get group permissions
            for group in self.groups.values():
                if user_id in group.members:
                    permissions.update(group.permissions)
            
            return list(permissions)
    
    def list_users(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[UserStatus] = None,
        role: Optional[UserRole] = None
    ) -> List[User]:
        """List users with filters.
        
        Args:
            tenant_id: Optional tenant ID filter
            status: Optional status filter
            role: Optional role filter
            
        Returns:
            List of users
        """
        with self.lock:
            users = list(self.users.values())
            
            if tenant_id:
                users = [u for u in users if u.tenant_id == tenant_id]
            
            if status:
                users = [u for u in users if u.status == status]
            
            if role:
                users = [u for u in users if u.role == role]
            
            return sorted(users, key=lambda u: u.created_at, reverse=True)
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics.
        
        Returns:
            User statistics
        """
        with self.lock:
            total_users = len(self.users)
            active_users = len([u for u in self.users.values() if u.status == UserStatus.ACTIVE])
            
            # Count by status
            status_counts = defaultdict(int)
            for user in self.users.values():
                status_counts[user.status.value] += 1
            
            # Count by role
            role_counts = defaultdict(int)
            for user in self.users.values():
                role_counts[user.role.value] += 1
            
            # Count by tenant
            tenant_counts = defaultdict(int)
            for user in self.users.values():
                if user.tenant_id:
                    tenant_counts[user.tenant_id] += 1
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "status_counts": dict(status_counts),
                "role_counts": dict(role_counts),
                "tenant_counts": dict(tenant_counts),
                "total_groups": len(self.groups),
                "active_sessions": len([s for s in self.sessions.values() if s.is_active])
            }
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        with self.lock:
            current_time = time.time()
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                if session.expires_at and current_time > session.expires_at:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self.invalidate_session(session_id)
            
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            return len(expired_sessions)
    
    def _hash_password(self, password: str) -> str:
        """Hash password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password.
        
        Args:
            password: Plain text password
            password_hash: Hashed password
            
        Returns:
            True if password matches
        """
        return self._hash_password(password) == password_hash
