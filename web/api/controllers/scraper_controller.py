"""
SPIDER Framework - Scraper Controller

Handles all scraper-related API endpoints including creation, management, and execution.
"""

from typing import List, Dict, Any, Optional
from fastapi import HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import asyncio
import uuid
from datetime import datetime

from ...core.config import get_settings
from ...core.database import get_db
from ...core.logger import get_logger
from ...enterprise.user_management import get_current_user, User
from ...enterprise.multi_tenant import get_current_tenant, Tenant

logger = get_logger(__name__)

class ScraperCreateRequest(BaseModel):
    """Request model for creating a scraper."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    url: str = Field(..., regex=r'^https?://.+')
    engine: str = Field(..., regex=r'^(scrapy|playwright|httpx)$')
    selectors: Dict[str, str] = Field(..., min_items=1)
    schedule: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None

class ScraperUpdateRequest(BaseModel):
    """Request model for updating a scraper."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    url: Optional[str] = Field(None, regex=r'^https?://.+')
    engine: Optional[str] = Field(None, regex=r'^(scrapy|playwright|httpx)$')
    selectors: Optional[Dict[str, str]] = None
    schedule: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None

class ScraperResponse(BaseModel):
    """Response model for scraper data."""
    id: str
    name: str
    description: Optional[str]
    url: str
    engine: str
    selectors: Dict[str, str]
    schedule: Optional[Dict[str, Any]]
    settings: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime]
    next_run: Optional[datetime]

class ScraperRunRequest(BaseModel):
    """Request model for running a scraper."""
    async_run: bool = True
    priority: str = Field("normal", regex=r'^(low|normal|high|urgent)$')
    max_pages: Optional[int] = Field(None, ge=1, le=10000)
    custom_settings: Optional[Dict[str, Any]] = None

class ScraperRunResponse(BaseModel):
    """Response model for scraper run."""
    job_id: str
    scraper_id: str
    status: str
    created_at: datetime
    estimated_duration: Optional[int] = None

class ScraperController:
    """Controller for scraper-related operations."""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def create_scraper(
        self,
        request: ScraperCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> ScraperResponse:
        """Create a new scraper."""
        try:
            # Validate scraper configuration
            await self._validate_scraper_config(request)
            
            # Create scraper record
            scraper_data = {
                "id": str(uuid.uuid4()),
                "name": request.name,
                "description": request.description,
                "url": request.url,
                "engine": request.engine,
                "selectors": request.selectors,
                "schedule": request.schedule or {},
                "settings": request.settings or {},
                "status": "created",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "user_id": current_user.id,
                "tenant_id": current_tenant.id
            }
            
            # Save to database
            # db.add(scraper)
            # db.commit()
            # db.refresh(scraper)
            
            logger.info(f"Created scraper {scraper_data['id']} for user {current_user.id}")
            
            return ScraperResponse(**scraper_data)
            
        except Exception as e:
            logger.error(f"Failed to create scraper: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create scraper")
    
    async def get_scrapers(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        engine: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> List[ScraperResponse]:
        """Get list of scrapers."""
        try:
            # Build query filters
            filters = {"tenant_id": current_tenant.id}
            if status:
                filters["status"] = status
            if engine:
                filters["engine"] = engine
            
            # Query database
            # scrapers = db.query(Scraper).filter_by(**filters).offset(skip).limit(limit).all()
            
            # Mock data for now
            scrapers = []
            
            return [ScraperResponse(**scraper.__dict__) for scraper in scrapers]
            
        except Exception as e:
            logger.error(f"Failed to get scrapers: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get scrapers")
    
    async def get_scraper(
        self,
        scraper_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> ScraperResponse:
        """Get a specific scraper."""
        try:
            # Query database
            # scraper = db.query(Scraper).filter_by(
            #     id=scraper_id,
            #     tenant_id=current_tenant.id
            # ).first()
            
            # if not scraper:
            #     raise HTTPException(status_code=404, detail="Scraper not found")
            
            # Mock data for now
            raise HTTPException(status_code=404, detail="Scraper not found")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get scraper {scraper_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get scraper")
    
    async def update_scraper(
        self,
        scraper_id: str,
        request: ScraperUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> ScraperResponse:
        """Update a scraper."""
        try:
            # Get existing scraper
            # scraper = db.query(Scraper).filter_by(
            #     id=scraper_id,
            #     tenant_id=current_tenant.id
            # ).first()
            
            # if not scraper:
            #     raise HTTPException(status_code=404, detail="Scraper not found")
            
            # Update fields
            update_data = request.dict(exclude_unset=True)
            if update_data:
                update_data["updated_at"] = datetime.utcnow()
                # for field, value in update_data.items():
                #     setattr(scraper, field, value)
                
                # db.commit()
                # db.refresh(scraper)
            
            logger.info(f"Updated scraper {scraper_id}")
            
            # Mock response for now
            raise HTTPException(status_code=404, detail="Scraper not found")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update scraper {scraper_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update scraper")
    
    async def delete_scraper(
        self,
        scraper_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> Dict[str, str]:
        """Delete a scraper."""
        try:
            # Check if scraper exists
            # scraper = db.query(Scraper).filter_by(
            #     id=scraper_id,
            #     tenant_id=current_tenant.id
            # ).first()
            
            # if not scraper:
            #     raise HTTPException(status_code=404, detail="Scraper not found")
            
            # Delete scraper
            # db.delete(scraper)
            # db.commit()
            
            logger.info(f"Deleted scraper {scraper_id}")
            
            return {"message": "Scraper deleted successfully", "scraper_id": scraper_id}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete scraper {scraper_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete scraper")
    
    async def run_scraper(
        self,
        scraper_id: str,
        request: ScraperRunRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> ScraperRunResponse:
        """Run a scraper."""
        try:
            # Get scraper
            # scraper = db.query(Scraper).filter_by(
            #     id=scraper_id,
            #     tenant_id=current_tenant.id
            # ).first()
            
            # if not scraper:
            #     raise HTTPException(status_code=404, detail="Scraper not found")
            
            # Create job
            job_id = str(uuid.uuid4())
            job_data = {
                "job_id": job_id,
                "scraper_id": scraper_id,
                "status": "queued",
                "created_at": datetime.utcnow(),
                "estimated_duration": 300  # 5 minutes default
            }
            
            # Add to background tasks if async
            if request.async_run:
                background_tasks.add_task(
                    self._run_scraper_job,
                    job_id,
                    scraper_id,
                    request.dict()
                )
            
            logger.info(f"Started scraper job {job_id} for scraper {scraper_id}")
            
            return ScraperRunResponse(**job_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to run scraper {scraper_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to run scraper")
    
    async def get_scraper_results(
        self,
        scraper_id: str,
        skip: int = 0,
        limit: int = 100,
        job_id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant)
    ) -> Dict[str, Any]:
        """Get scraper results."""
        try:
            # Query results
            # results = db.query(ScraperResult).filter_by(
            #     scraper_id=scraper_id,
            #     tenant_id=current_tenant.id
            # )
            
            # if job_id:
            #     results = results.filter_by(job_id=job_id)
            
            # results = results.offset(skip).limit(limit).all()
            
            # Mock data for now
            results = []
            total = 0
            
            return {
                "results": [result.__dict__ for result in results],
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get scraper results: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get scraper results")
    
    async def _validate_scraper_config(self, request: ScraperCreateRequest) -> None:
        """Validate scraper configuration."""
        # Validate URL accessibility
        # Validate selectors syntax
        # Validate engine compatibility
        pass
    
    async def _run_scraper_job(self, job_id: str, scraper_id: str, config: Dict[str, Any]) -> None:
        """Run scraper job in background."""
        try:
            # Update job status to running
            # Execute scraper
            # Update job status to completed
            logger.info(f"Completed scraper job {job_id}")
        except Exception as e:
            logger.error(f"Failed to run scraper job {job_id}: {str(e)}")
            # Update job status to failed
