"""Advanced data transformation pipelines for SPIDER framework."""

import asyncio
import time
import json
import re
import hashlib
from typing import Dict, List, Optional, Any, Union, Callable, Tuple, Iterator
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque
import statistics
import numpy as np
from datetime import datetime, date, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.exceptions import SpiderError, ValidationError
from ..core.logger import get_logger


class TransformationType(Enum):
    """Transformation types."""
    CLEAN = "clean"
    NORMALIZE = "normalize"
    ENRICH = "enrich"
    AGGREGATE = "aggregate"
    FILTER = "filter"
    SORT = "sort"
    GROUP = "group"
    JOIN = "join"
    PIVOT = "pivot"
    CUSTOM = "custom"


class DataFormat(Enum):
    """Data formats."""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    HTML = "html"
    TEXT = "text"
    BINARY = "binary"


class PipelineStage(Enum):
    """Pipeline stages."""
    INPUT = "input"
    TRANSFORM = "transform"
    VALIDATE = "validate"
    OUTPUT = "output"


@dataclass
class TransformationStep:
    """Single transformation step."""
    name: str
    transformation_type: TransformationType
    function: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    parallel: bool = False
    timeout: Optional[float] = None
    retry_count: int = 0
    error_handling: str = "skip"  # skip, fail, retry


@dataclass
class PipelineConfig:
    """Pipeline configuration."""
    name: str
    description: str = ""
    max_workers: int = 4
    batch_size: int = 1000
    timeout: Optional[float] = None
    retry_count: int = 3
    error_handling: str = "skip"
    parallel_execution: bool = True
    memory_limit: Optional[int] = None  # MB


@dataclass
class PipelineResult:
    """Pipeline execution result."""
    success: bool
    input_count: int
    output_count: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataCleaner:
    """Data cleaning transformations."""
    
    def __init__(self):
        """Initialize data cleaner."""
        self.logger = get_logger(self.__class__.__name__)
    
    def clean_text(self, text: str, remove_whitespace: bool = True, normalize_case: bool = False) -> str:
        """Clean text data.
        
        Args:
            text: Input text
            remove_whitespace: Remove extra whitespace
            normalize_case: Normalize case
            
        Returns:
            Cleaned text
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Normalize unicode
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        # Remove extra whitespace
        if remove_whitespace:
            text = re.sub(r'\s+', ' ', text).strip()
        
        # Normalize case
        if normalize_case:
            text = text.lower()
        
        return text
    
    def clean_numeric(self, value: Union[str, int, float], decimal_places: int = 2) -> float:
        """Clean numeric data.
        
        Args:
            value: Input value
            decimal_places: Number of decimal places
            
        Returns:
            Cleaned numeric value
        """
        if isinstance(value, (int, float)):
            return round(float(value), decimal_places)
        
        # Remove non-numeric characters except decimal point and minus
        cleaned = re.sub(r'[^\d.-]', '', str(value))
        
        try:
            return round(float(cleaned), decimal_places)
        except ValueError:
            return 0.0
    
    def clean_email(self, email: str) -> str:
        """Clean email address.
        
        Args:
            email: Input email
            
        Returns:
            Cleaned email
        """
        if not isinstance(email, str):
            return ""
        
        # Convert to lowercase and strip whitespace
        email = email.lower().strip()
        
        # Remove invalid characters
        email = re.sub(r'[^\w@.-]', '', email)
        
        return email
    
    def clean_phone(self, phone: str) -> str:
        """Clean phone number.
        
        Args:
            phone: Input phone number
            
        Returns:
            Cleaned phone number
        """
        if not isinstance(phone, str):
            return ""
        
        # Remove all non-digit characters
        cleaned = re.sub(r'\D', '', phone)
        
        # Format as standard phone number
        if len(cleaned) == 10:
            return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
        elif len(cleaned) == 11 and cleaned[0] == '1':
            return f"({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:]}"
        
        return cleaned
    
    def remove_duplicates(self, data: List[Any], key_func: Optional[Callable] = None) -> List[Any]:
        """Remove duplicates from data.
        
        Args:
            data: Input data list
            key_func: Optional function to extract key for comparison
            
        Returns:
            Data with duplicates removed
        """
        if key_func is None:
            return list(dict.fromkeys(data))  # Preserve order
        
        seen = set()
        result = []
        
        for item in data:
            key = key_func(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        
        return result


class DataNormalizer:
    """Data normalization transformations."""
    
    def __init__(self):
        """Initialize data normalizer."""
        self.logger = get_logger(self.__class__.__name__)
    
    def normalize_text(self, text: str, case: str = "lower", encoding: str = "utf-8") -> str:
        """Normalize text data.
        
        Args:
            text: Input text
            case: Case normalization (lower, upper, title)
            encoding: Text encoding
            
        Returns:
            Normalized text
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Normalize unicode
        text = text.encode(encoding, errors='ignore').decode(encoding)
        
        # Apply case normalization
        if case == "lower":
            text = text.lower()
        elif case == "upper":
            text = text.upper()
        elif case == "title":
            text = text.title()
        
        return text
    
    def normalize_numeric(self, value: Union[str, int, float], scale: float = 1.0, offset: float = 0.0) -> float:
        """Normalize numeric data.
        
        Args:
            value: Input value
            scale: Scaling factor
            offset: Offset value
            
        Returns:
            Normalized numeric value
        """
        try:
            numeric_value = float(value)
            return (numeric_value * scale) + offset
        except (ValueError, TypeError):
            return 0.0
    
    def normalize_date(self, date_value: Union[str, datetime, date], format: str = "%Y-%m-%d") -> str:
        """Normalize date data.
        
        Args:
            date_value: Input date
            format: Output format
            
        Returns:
            Normalized date string
        """
        if isinstance(date_value, datetime):
            return date_value.strftime(format)
        elif isinstance(date_value, date):
            return date_value.strftime(format)
        elif isinstance(date_value, str):
            try:
                # Try to parse common date formats
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        parsed = datetime.strptime(date_value, fmt)
                        return parsed.strftime(format)
                    except ValueError:
                        continue
            except Exception:
                pass
        
        return str(date_value)
    
    def normalize_currency(self, value: Union[str, int, float], currency: str = "USD") -> float:
        """Normalize currency data.
        
        Args:
            value: Input value
            currency: Target currency
            
        Returns:
            Normalized currency value
        """
        if isinstance(value, (int, float)):
            return float(value)
        
        # Remove currency symbols and formatting
        cleaned = re.sub(r'[^\d.-]', '', str(value))
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0


class DataEnricher:
    """Data enrichment transformations."""
    
    def __init__(self):
        """Initialize data enricher."""
        self.logger = get_logger(self.__class__.__name__)
        self.enrichment_cache: Dict[str, Any] = {}
        self.external_apis: Dict[str, Callable] = {}
    
    def add_external_api(self, name: str, api_func: Callable) -> None:
        """Add external API for enrichment.
        
        Args:
            name: API name
            api_func: API function
        """
        self.external_apis[name] = api_func
        self.logger.info(f"Added external API: {name}")
    
    async def enrich_with_geolocation(self, address: str) -> Dict[str, Any]:
        """Enrich address with geolocation data.
        
        Args:
            address: Address string
            
        Returns:
            Geolocation data
        """
        cache_key = f"geo_{hashlib.md5(address.encode()).hexdigest()}"
        
        if cache_key in self.enrichment_cache:
            return self.enrichment_cache[cache_key]
        
        # Simulate geolocation API call
        geolocation_data = {
            "latitude": 0.0,
            "longitude": 0.0,
            "country": "Unknown",
            "city": "Unknown",
            "postal_code": "Unknown"
        }
        
        self.enrichment_cache[cache_key] = geolocation_data
        return geolocation_data
    
    async def enrich_with_company_data(self, company_name: str) -> Dict[str, Any]:
        """Enrich company name with additional data.
        
        Args:
            company_name: Company name
            
        Returns:
            Company data
        """
        cache_key = f"company_{hashlib.md5(company_name.encode()).hexdigest()}"
        
        if cache_key in self.enrichment_cache:
            return self.enrichment_cache[cache_key]
        
        # Simulate company data API call
        company_data = {
            "industry": "Unknown",
            "size": "Unknown",
            "website": "",
            "description": ""
        }
        
        self.enrichment_cache[cache_key] = company_data
        return company_data
    
    async def enrich_with_sentiment(self, text: str) -> Dict[str, Any]:
        """Enrich text with sentiment analysis.
        
        Args:
            text: Input text
            
        Returns:
            Sentiment data
        """
        cache_key = f"sentiment_{hashlib.md5(text.encode()).hexdigest()}"
        
        if cache_key in self.enrichment_cache:
            return self.enrichment_cache[cache_key]
        
        # Simple sentiment analysis (placeholder)
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disgusting']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = 0.7
        elif negative_count > positive_count:
            sentiment = "negative"
            score = -0.7
        else:
            sentiment = "neutral"
            score = 0.0
        
        sentiment_data = {
            "sentiment": sentiment,
            "score": score,
            "confidence": 0.8
        }
        
        self.enrichment_cache[cache_key] = sentiment_data
        return sentiment_data


class DataAggregator:
    """Data aggregation transformations."""
    
    def __init__(self):
        """Initialize data aggregator."""
        self.logger = get_logger(self.__class__.__name__)
    
    def group_by(self, data: List[Dict[str, Any]], group_key: str) -> Dict[str, List[Dict[str, Any]]]:
        """Group data by key.
        
        Args:
            data: Input data
            group_key: Key to group by
            
        Returns:
            Grouped data
        """
        grouped = defaultdict(list)
        
        for item in data:
            key_value = item.get(group_key, "unknown")
            grouped[key_value].append(item)
        
        return dict(grouped)
    
    def aggregate_numeric(self, data: List[Dict[str, Any]], field: str, operation: str = "sum") -> float:
        """Aggregate numeric field.
        
        Args:
            data: Input data
            field: Field to aggregate
            operation: Aggregation operation (sum, avg, min, max, count)
            
        Returns:
            Aggregated value
        """
        values = [item.get(field, 0) for item in data if isinstance(item.get(field), (int, float))]
        
        if not values:
            return 0.0
        
        if operation == "sum":
            return sum(values)
        elif operation == "avg":
            return statistics.mean(values)
        elif operation == "min":
            return min(values)
        elif operation == "max":
            return max(values)
        elif operation == "count":
            return len(values)
        else:
            return 0.0
    
    def pivot_table(self, data: List[Dict[str, Any]], index: str, columns: str, values: str, aggfunc: str = "sum") -> Dict[str, Any]:
        """Create pivot table.
        
        Args:
            data: Input data
            index: Index column
            columns: Columns to pivot
            values: Values to aggregate
            aggfunc: Aggregation function
            
        Returns:
            Pivot table data
        """
        # Group by index and columns
        grouped = defaultdict(lambda: defaultdict(list))
        
        for item in data:
            index_val = item.get(index, "unknown")
            col_val = item.get(columns, "unknown")
            value = item.get(values, 0)
            
            if isinstance(value, (int, float)):
                grouped[index_val][col_val].append(value)
        
        # Create pivot table
        pivot_data = {}
        
        for index_val, cols in grouped.items():
            pivot_data[index_val] = {}
            for col_val, values_list in cols.items():
                if aggfunc == "sum":
                    pivot_data[index_val][col_val] = sum(values_list)
                elif aggfunc == "avg":
                    pivot_data[index_val][col_val] = statistics.mean(values_list)
                elif aggfunc == "count":
                    pivot_data[index_val][col_val] = len(values_list)
                else:
                    pivot_data[index_val][col_val] = sum(values_list)
        
        return pivot_data


class TransformationPipeline:
    """Advanced data transformation pipeline."""
    
    def __init__(self, config: PipelineConfig):
        """Initialize transformation pipeline.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.steps: List[TransformationStep] = []
        self.execution_history: deque = deque(maxlen=1000)
        self.performance_stats: Dict[str, List[float]] = defaultdict(list)
        
        # Initialize transformers
        self.cleaner = DataCleaner()
        self.normalizer = DataNormalizer()
        self.enricher = DataEnricher()
        self.aggregator = DataAggregator()
    
    def add_step(self, step: TransformationStep) -> None:
        """Add transformation step.
        
        Args:
            step: Transformation step
        """
        self.steps.append(step)
        self.logger.info(f"Added transformation step: {step.name}")
    
    def remove_step(self, step_name: str) -> bool:
        """Remove transformation step.
        
        Args:
            step_name: Step name
            
        Returns:
            True if removed, False if not found
        """
        for i, step in enumerate(self.steps):
            if step.name == step_name:
                del self.steps[i]
                self.logger.info(f"Removed transformation step: {step_name}")
                return True
        return False
    
    async def execute(self, data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> PipelineResult:
        """Execute transformation pipeline.
        
        Args:
            data: Input data
            
        Returns:
            Pipeline execution result
        """
        start_time = time.time()
        
        try:
            # Convert single item to list
            if isinstance(data, dict):
                data = [data]
            
            input_count = len(data)
            current_data = data.copy()
            errors = []
            warnings = []
            
            # Execute each step
            for step in self.steps:
                if not step.enabled:
                    continue
                
                try:
                    step_start = time.time()
                    
                    if step.parallel and len(current_data) > self.config.batch_size:
                        current_data = await self._execute_step_parallel(step, current_data)
                    else:
                        current_data = await self._execute_step_sequential(step, current_data)
                    
                    step_duration = time.time() - step_start
                    self.performance_stats[step.name].append(step_duration)
                    
                    self.logger.info(f"Step {step.name} completed in {step_duration:.3f}s")
                    
                except Exception as e:
                    error_msg = f"Step {step.name} failed: {str(e)}"
                    self.logger.error(error_msg)
                    
                    if step.error_handling == "fail":
                        raise
                    elif step.error_handling == "skip":
                        warnings.append(error_msg)
                    elif step.error_handling == "retry" and step.retry_count > 0:
                        step.retry_count -= 1
                        # Retry logic would go here
                        warnings.append(f"Retrying step {step.name}")
            
            output_count = len(current_data)
            duration = time.time() - start_time
            
            result = PipelineResult(
                success=True,
                input_count=input_count,
                output_count=output_count,
                errors=errors,
                warnings=warnings,
                duration=duration,
                metadata={
                    "steps_executed": len([s for s in self.steps if s.enabled]),
                    "pipeline_name": self.config.name
                }
            )
            
            # Record execution history
            self.execution_history.append({
                "timestamp": time.time(),
                "pipeline_name": self.config.name,
                "input_count": input_count,
                "output_count": output_count,
                "duration": duration,
                "success": True
            })
            
            self.logger.info(f"Pipeline {self.config.name} completed: {input_count} -> {output_count} items in {duration:.3f}s")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Pipeline execution failed: {str(e)}"
            self.logger.error(error_msg)
            
            result = PipelineResult(
                success=False,
                input_count=len(data) if isinstance(data, list) else 1,
                output_count=0,
                errors=[error_msg],
                duration=duration
            )
            
            return result
    
    async def _execute_step_sequential(self, step: TransformationStep, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute step sequentially.
        
        Args:
            step: Transformation step
            data: Input data
            
        Returns:
            Transformed data
        """
        result_data = []
        
        for item in data:
            try:
                if step.transformation_type == TransformationType.CLEAN:
                    transformed_item = await self._apply_clean_transformation(step, item)
                elif step.transformation_type == TransformationType.NORMALIZE:
                    transformed_item = await self._apply_normalize_transformation(step, item)
                elif step.transformation_type == TransformationType.ENRICH:
                    transformed_item = await self._apply_enrich_transformation(step, item)
                elif step.transformation_type == TransformationType.AGGREGATE:
                    transformed_item = await self._apply_aggregate_transformation(step, item)
                elif step.transformation_type == TransformationType.CUSTOM:
                    transformed_item = await self._apply_custom_transformation(step, item)
                else:
                    transformed_item = item
                
                result_data.append(transformed_item)
                
            except Exception as e:
                self.logger.warning(f"Item transformation failed in step {step.name}: {e}")
                if step.error_handling != "skip":
                    raise
                result_data.append(item)
        
        return result_data
    
    async def _execute_step_parallel(self, step: TransformationStep, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute step in parallel.
        
        Args:
            step: Transformation step
            data: Input data
            
        Returns:
            Transformed data
        """
        result_data = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Create batches
            batches = [data[i:i + self.config.batch_size] for i in range(0, len(data), self.config.batch_size)]
            
            # Submit batch tasks
            future_to_batch = {
                executor.submit(self._execute_step_sequential, step, batch): batch
                for batch in batches
            }
            
            # Collect results
            for future in as_completed(future_to_batch):
                try:
                    batch_result = future.result()
                    result_data.extend(batch_result)
                except Exception as e:
                    self.logger.error(f"Batch processing failed in step {step.name}: {e}")
                    if step.error_handling != "skip":
                        raise
        
        return result_data
    
    async def _apply_clean_transformation(self, step: TransformationStep, item: Dict[str, Any]) -> Dict[str, Any]:
        """Apply cleaning transformation.
        
        Args:
            step: Transformation step
            item: Data item
            
        Returns:
            Cleaned item
        """
        cleaned_item = item.copy()
        
        for field, value in item.items():
            if isinstance(value, str):
                cleaned_item[field] = self.cleaner.clean_text(
                    value,
                    remove_whitespace=step.parameters.get("remove_whitespace", True),
                    normalize_case=step.parameters.get("normalize_case", False)
                )
            elif isinstance(value, (int, float)):
                cleaned_item[field] = self.cleaner.clean_numeric(
                    value,
                    decimal_places=step.parameters.get("decimal_places", 2)
                )
        
        return cleaned_item
    
    async def _apply_normalize_transformation(self, step: TransformationStep, item: Dict[str, Any]) -> Dict[str, Any]:
        """Apply normalization transformation.
        
        Args:
            step: Transformation step
            item: Data item
            
        Returns:
            Normalized item
        """
        normalized_item = item.copy()
        
        for field, value in item.items():
            if isinstance(value, str):
                normalized_item[field] = self.normalizer.normalize_text(
                    value,
                    case=step.parameters.get("case", "lower"),
                    encoding=step.parameters.get("encoding", "utf-8")
                )
            elif isinstance(value, (int, float)):
                normalized_item[field] = self.normalizer.normalize_numeric(
                    value,
                    scale=step.parameters.get("scale", 1.0),
                    offset=step.parameters.get("offset", 0.0)
                )
        
        return normalized_item
    
    async def _apply_enrich_transformation(self, step: TransformationStep, item: Dict[str, Any]) -> Dict[str, Any]:
        """Apply enrichment transformation.
        
        Args:
            step: Transformation step
            item: Data item
            
        Returns:
            Enriched item
        """
        enriched_item = item.copy()
        
        # Add geolocation data
        if "address" in item:
            geo_data = await self.enricher.enrich_with_geolocation(item["address"])
            enriched_item.update({f"geo_{k}": v for k, v in geo_data.items()})
        
        # Add company data
        if "company" in item:
            company_data = await self.enricher.enrich_with_company_data(item["company"])
            enriched_item.update({f"company_{k}": v for k, v in company_data.items()})
        
        # Add sentiment data
        if "text" in item:
            sentiment_data = await self.enricher.enrich_with_sentiment(item["text"])
            enriched_item.update({f"sentiment_{k}": v for k, v in sentiment_data.items()})
        
        return enriched_item
    
    async def _apply_aggregate_transformation(self, step: TransformationStep, item: Dict[str, Any]) -> Dict[str, Any]:
        """Apply aggregation transformation.
        
        Args:
            step: Transformation step
            item: Data item
            
        Returns:
            Aggregated item
        """
        # This would typically work on a list of items, not a single item
        # For now, return the item as-is
        return item
    
    async def _apply_custom_transformation(self, step: TransformationStep, item: Dict[str, Any]) -> Dict[str, Any]:
        """Apply custom transformation.
        
        Args:
            step: Transformation step
            item: Data item
            
        Returns:
            Transformed item
        """
        if callable(step.function):
            return step.function(item, **step.parameters)
        else:
            return item
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics.
        
        Returns:
            Performance statistics
        """
        stats = {}
        
        for step_name, durations in self.performance_stats.items():
            if durations:
                stats[step_name] = {
                    "count": len(durations),
                    "avg_duration": statistics.mean(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "total_duration": sum(durations)
                }
        
        return stats
    
    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of execution records
        """
        return list(self.execution_history)[-limit:]
    
    def cleanup(self) -> None:
        """Cleanup pipeline."""
        self.execution_history.clear()
        self.performance_stats.clear()
        self.logger.info("Transformation pipeline cleaned up")
