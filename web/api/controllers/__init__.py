"""
SPIDER Framework - API Controllers

This module contains API controllers for handling HTTP requests and responses.
Controllers are responsible for business logic and data transformation.
"""

from .scraper_controller import ScraperController
from .user_controller import UserController
from .system_controller import SystemController
from .monitoring_controller import MonitoringController
from .ai_controller import AIController

__all__ = [
    'ScraperController',
    'UserController', 
    'SystemController',
    'MonitoringController',
    'AIController'
]

__version__ = '2.0.0'
__author__ = 'SPIDER Framework Team'
__email__ = 'team@example.com'
