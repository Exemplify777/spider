"""
SPIDER Framework - Scraper API Models

Pydantic models for scraper-related API endpoints.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
import re

from .common_models import BaseResponse, PaginationResponse

class ScraperCreateRequest(BaseModel):
    """Request model for creating a scraper."""
    name: str = Field(..., min_length=1, max_length=255, description="Scraper name")
    description: Optional[str] = Field(None, max_length=1000, description="Scraper description")
    url: str = Field(..., regex=r'^https?://.+', description="Target URL to scrape")
    engine: str = Field(..., regex=r'^(scrapy|playwright|httpx)$', description="Scraping engine")
    selectors: Dict[str, str] = Field(..., min_items=1, description="CSS selectors for data extraction")
    schedule: Optional[Dict[str, Any]] = Field(None, description="Scheduling configuration")
    settings: Optional[Dict[str, Any]] = Field(None, description="Scraper-specific settings")
    
    @validator('selectors')
    def validate_selectors(cls, v):
        """Validate CSS selectors."""
        for key, selector in v.items():
            if not selector or not selector.strip():
                raise ValueError(f"Selector for '{key}' cannot be empty")
        return v
    
    @validator('schedule')
    def validate_schedule(cls, v):
        """Validate schedule configuration."""
        if v:
            if 'cron' in v and not re.match(r'^(\*|[0-5]?\d) (\*|[01]?\d|2[0-3]) (\*|[12]?\d|3[01]) (\*|[01]?\d|1[0-2]) (\*|[0-6])$', v['cron']):
                raise ValueError("Invalid cron expression")
        return v

class ScraperUpdateRequest(BaseModel):
    """Request model for updating a scraper."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Scraper name")
    description: Optional[str] = Field(None, max_length=1000, description="Scraper description")
    url: Optional[str] = Field(None, regex=r'^https?://.+', description="Target URL to scrape")
    engine: Optional[str] = Field(None, regex=r'^(scrapy|playwright|httpx)$', description="Scraping engine")
    selectors: Optional[Dict[str, str]] = Field(None, min_items=1, description="CSS selectors for data extraction")
    schedule: Optional[Dict[str, Any]] = Field(None, description="Scheduling configuration")
    settings: Optional[Dict[str, Any]] = Field(None, description="Scraper-specific settings")
    
    @validator('selectors')
    def validate_selectors(cls, v):
        """Validate CSS selectors."""
        if v:
            for key, selector in v.items():
                if not selector or not selector.strip():
                    raise ValueError(f"Selector for '{key}' cannot be empty")
        return v

class ScraperResponse(BaseResponse):
    """Response model for scraper data."""
    id: str = Field(..., description="Unique scraper identifier")
    name: str = Field(..., description="Scraper name")
    description: Optional[str] = Field(None, description="Scraper description")
    url: str = Field(..., description="Target URL")
    engine: str = Field(..., description="Scraping engine")
    selectors: Dict[str, str] = Field(..., description="CSS selectors")
    schedule: Optional[Dict[str, Any]] = Field(None, description="Schedule configuration")
    settings: Optional[Dict[str, Any]] = Field(None, description="Scraper settings")
    status: str = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_run: Optional[datetime] = Field(None, description="Last run timestamp")
    next_run: Optional[datetime] = Field(None, description="Next scheduled run")

class ScraperListResponse(BaseResponse):
    """Response model for scraper list."""
    scrapers: List[ScraperResponse] = Field(..., description="List of scrapers")
    pagination: PaginationResponse = Field(..., description="Pagination information")

class ScraperRunRequest(BaseModel):
    """Request model for running a scraper."""
    async_run: bool = Field(True, description="Run asynchronously")
    priority: str = Field("normal", regex=r'^(low|normal|high|urgent)$', description="Job priority")
    max_pages: Optional[int] = Field(None, ge=1, le=10000, description="Maximum pages to scrape")
    custom_settings: Optional[Dict[str, Any]] = Field(None, description="Custom settings for this run")

class ScraperRunResponse(BaseResponse):
    """Response model for scraper run."""
    job_id: str = Field(..., description="Job identifier")
    scraper_id: str = Field(..., description="Scraper identifier")
    status: str = Field(..., description="Job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in seconds")

class ScraperResultsRequest(BaseModel):
    """Request model for getting scraper results."""
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(50, ge=1, le=1000, description="Items per page")
    job_id: Optional[str] = Field(None, description="Filter by job ID")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    format: str = Field("json", regex=r'^(json|csv|xlsx)$', description="Output format")

class ScraperResultsResponse(BaseResponse):
    """Response model for scraper results."""
    results: List[Dict[str, Any]] = Field(..., description="Scraped data")
    pagination: PaginationResponse = Field(..., description="Pagination information")
    statistics: Dict[str, Any] = Field(..., description="Scraping statistics")

class JobStatusResponse(BaseResponse):
    """Response model for job status."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status")
    progress: Optional[Dict[str, Any]] = Field(None, description="Job progress")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class ScraperStatisticsResponse(BaseResponse):
    """Response model for scraper statistics."""
    scraper_id: str = Field(..., description="Scraper identifier")
    period: str = Field(..., description="Statistics period")
    statistics: Dict[str, Any] = Field(..., description="Statistics data")
    timeline: List[Dict[str, Any]] = Field(..., description="Timeline data")

class ScraperValidationRequest(BaseModel):
    """Request model for validating scraper configuration."""
    url: str = Field(..., regex=r'^https?://.+', description="URL to validate")
    selectors: Dict[str, str] = Field(..., min_items=1, description="Selectors to validate")
    engine: str = Field(..., regex=r'^(scrapy|playwright|httpx)$', description="Engine to use")

class ScraperValidationResponse(BaseResponse):
    """Response model for scraper validation."""
    is_valid: bool = Field(..., description="Whether configuration is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    sample_data: Optional[Dict[str, Any]] = Field(None, description="Sample extracted data")

class ScraperTestRequest(BaseModel):
    """Request model for testing scraper."""
    url: str = Field(..., regex=r'^https?://.+', description="URL to test")
    selectors: Dict[str, str] = Field(..., min_items=1, description="Selectors to test")
    engine: str = Field(..., regex=r'^(scrapy|playwright|httpx)$', description="Engine to use")
    max_pages: int = Field(1, ge=1, le=10, description="Maximum pages to test")

class ScraperTestResponse(BaseResponse):
    """Response model for scraper test."""
    test_id: str = Field(..., description="Test identifier")
    status: str = Field(..., description="Test status")
    results: List[Dict[str, Any]] = Field(..., description="Test results")
    errors: List[str] = Field(default_factory=list, description="Test errors")
    warnings: List[str] = Field(default_factory=list, description="Test warnings")

class ScraperScheduleRequest(BaseModel):
    """Request model for updating scraper schedule."""
    enabled: bool = Field(..., description="Whether scheduling is enabled")
    cron: Optional[str] = Field(None, description="Cron expression")
    timezone: str = Field("UTC", description="Timezone for scheduling")
    
    @validator('cron')
    def validate_cron(cls, v):
        """Validate cron expression."""
        if v and not re.match(r'^(\*|[0-5]?\d) (\*|[01]?\d|2[0-3]) (\*|[12]?\d|3[01]) (\*|[01]?\d|1[0-2]) (\*|[0-6])$', v):
            raise ValueError("Invalid cron expression")
        return v

class ScraperScheduleResponse(BaseResponse):
    """Response model for scraper schedule."""
    enabled: bool = Field(..., description="Whether scheduling is enabled")
    cron: Optional[str] = Field(None, description="Cron expression")
    timezone: str = Field(..., description="Timezone")
    next_run: Optional[datetime] = Field(None, description="Next scheduled run")

class ScraperSettingsRequest(BaseModel):
    """Request model for updating scraper settings."""
    rate_limit: Optional[Dict[str, Any]] = Field(None, description="Rate limiting settings")
    proxy: Optional[Dict[str, Any]] = Field(None, description="Proxy settings")
    user_agent: Optional[str] = Field(None, description="User agent string")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")
    timeout: Optional[int] = Field(None, ge=1, le=300, description="Request timeout in seconds")
    retries: Optional[int] = Field(None, ge=0, le=10, description="Number of retries")

class ScraperSettingsResponse(BaseResponse):
    """Response model for scraper settings."""
    rate_limit: Optional[Dict[str, Any]] = Field(None, description="Rate limiting settings")
    proxy: Optional[Dict[str, Any]] = Field(None, description="Proxy settings")
    user_agent: Optional[str] = Field(None, description="User agent string")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")
    timeout: Optional[int] = Field(None, description="Request timeout in seconds")
    retries: Optional[int] = Field(None, description="Number of retries")

class ScraperExportRequest(BaseModel):
    """Request model for exporting scraper data."""
    format: str = Field(..., regex=r'^(json|csv|xlsx|xml)$', description="Export format")
    date_from: Optional[datetime] = Field(None, description="Export from date")
    date_to: Optional[datetime] = Field(None, description="Export to date")
    job_id: Optional[str] = Field(None, description="Filter by job ID")
    fields: Optional[List[str]] = Field(None, description="Fields to export")

class ScraperExportResponse(BaseResponse):
    """Response model for scraper export."""
    export_id: str = Field(..., description="Export identifier")
    download_url: str = Field(..., description="Download URL")
    expires_at: datetime = Field(..., description="Download expiration timestamp")
    file_size: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="Export format")
