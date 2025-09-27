"""
ML Model Registry

Comprehensive model registry system with versioning, metadata management,
and deployment tracking for the SPIDER framework.

Author: SPIDER Development Team
Version: 1.0.0
"""

import os
import json
import hashlib
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
import joblib

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Model type enumeration."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    TIME_SERIES = "time_series"
    ANOMALY_DETECTION = "anomaly_detection"
    RECOMMENDATION = "recommendation"


class ModelStatus(str, Enum):
    """Model status enumeration."""
    TRAINING = "training"
    TRAINED = "trained"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"


@dataclass
class ModelMetadata:
    """Model metadata container."""
    model_id: str
    name: str
    version: str
    model_type: ModelType
    description: str
    author: str
    created_at: datetime
    updated_at: datetime
    status: ModelStatus
    tags: List[str]
    metrics: Dict[str, float]
    parameters: Dict[str, Any]
    dependencies: List[str]
    file_size: int
    checksum: str
    training_data_hash: str
    validation_data_hash: str
    deployment_info: Optional[Dict[str, Any]] = None
    performance_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.performance_history is None:
            self.performance_history = []


@dataclass
class ModelVersion:
    """Model version container."""
    version: str
    model_id: str
    metadata: ModelMetadata
    model_path: str
    created_at: datetime
    is_latest: bool = False
    is_stable: bool = False
    parent_version: Optional[str] = None
    changes: List[str] = None
    
    def __post_init__(self):
        if self.changes is None:
            self.changes = []


class ModelRegistry:
    """
    ML Model Registry for managing model versions, metadata, and deployments.
    
    Features:
    - Model versioning and metadata management
    - Model storage and retrieval
    - Performance tracking and comparison
    - Model deployment management
    - Dependency tracking
    - Model validation and testing
    """
    
    def __init__(self, registry_path: str = "models/registry"):
        """
        Initialize the model registry.
        
        Args:
            registry_path: Path to store model registry data
        """
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        
        self.metadata_path = self.registry_path / "metadata.json"
        self.models_path = self.registry_path / "models"
        self.models_path.mkdir(exist_ok=True)
        
        self._metadata: Dict[str, List[ModelVersion]] = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """Load model metadata from disk."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r') as f:
                    data = json.load(f)
                    for model_id, versions in data.items():
                        self._metadata[model_id] = []
                        for version_data in versions:
                            # Convert datetime strings back to datetime objects
                            version_data['metadata']['created_at'] = datetime.fromisoformat(
                                version_data['metadata']['created_at']
                            )
                            version_data['metadata']['updated_at'] = datetime.fromisoformat(
                                version_data['metadata']['updated_at']
                            )
                            version_data['created_at'] = datetime.fromisoformat(
                                version_data['created_at']
                            )
                            
                            # Recreate ModelMetadata and ModelVersion objects
                            metadata = ModelMetadata(**version_data['metadata'])
                            version = ModelVersion(**version_data)
                            version.metadata = metadata
                            self._metadata[model_id].append(version)
            except Exception as e:
                logger.error(f"Failed to load model metadata: {e}")
                self._metadata = {}
    
    def _save_metadata(self):
        """Save model metadata to disk."""
        try:
            data = {}
            for model_id, versions in self._metadata.items():
                data[model_id] = []
                for version in versions:
                    version_data = asdict(version)
                    # Convert datetime objects to strings for JSON serialization
                    version_data['metadata']['created_at'] = version.metadata.created_at.isoformat()
                    version_data['metadata']['updated_at'] = version.metadata.updated_at.isoformat()
                    version_data['created_at'] = version.created_at.isoformat()
                    data[model_id].append(version_data)
            
            with open(self.metadata_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save model metadata: {e}")
    
    def register_model(
        self,
        model: Union[BaseEstimator, Any],
        name: str,
        model_type: ModelType,
        description: str = "",
        author: str = "unknown",
        tags: List[str] = None,
        parameters: Dict[str, Any] = None,
        dependencies: List[str] = None,
        training_data_hash: str = "",
        validation_data_hash: str = "",
        metrics: Dict[str, float] = None
    ) -> str:
        """
        Register a new model in the registry.
        
        Args:
            model: The trained model object
            name: Model name
            model_type: Type of the model
            description: Model description
            author: Model author
            tags: List of tags
            parameters: Model parameters
            dependencies: List of dependencies
            training_data_hash: Hash of training data
            validation_data_hash: Hash of validation data
            metrics: Model performance metrics
            
        Returns:
            Model ID
        """
        if tags is None:
            tags = []
        if parameters is None:
            parameters = {}
        if dependencies is None:
            dependencies = []
        if metrics is None:
            metrics = {}
        
        # Generate model ID and version
        model_id = self._generate_model_id(name)
        version = self._get_next_version(model_id)
        
        # Create model directory
        model_dir = self.models_path / model_id / version
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_path = model_dir / "model.pkl"
        try:
            joblib.dump(model, model_path)
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise
        
        # Calculate file size and checksum
        file_size = model_path.stat().st_size
        checksum = self._calculate_checksum(model_path)
        
        # Create metadata
        now = datetime.utcnow()
        metadata = ModelMetadata(
            model_id=model_id,
            name=name,
            version=version,
            model_type=model_type,
            description=description,
            author=author,
            created_at=now,
            updated_at=now,
            status=ModelStatus.TRAINED,
            tags=tags,
            metrics=metrics,
            parameters=parameters,
            dependencies=dependencies,
            file_size=file_size,
            checksum=checksum,
            training_data_hash=training_data_hash,
            validation_data_hash=validation_data_hash
        )
        
        # Create model version
        model_version = ModelVersion(
            version=version,
            model_id=model_id,
            metadata=metadata,
            model_path=str(model_path),
            created_at=now,
            is_latest=True,
            is_stable=False
        )
        
        # Update registry
        if model_id not in self._metadata:
            self._metadata[model_id] = []
        
        # Mark previous versions as not latest
        for v in self._metadata[model_id]:
            v.is_latest = False
        
        self._metadata[model_id].append(model_version)
        self._save_metadata()
        
        logger.info(f"Registered model {name} v{version} with ID {model_id}")
        return model_id
    
    def get_model(self, model_id: str, version: str = None) -> Optional[Any]:
        """
        Retrieve a model from the registry.
        
        Args:
            model_id: Model ID
            version: Model version (latest if None)
            
        Returns:
            Loaded model object or None
        """
        if model_id not in self._metadata:
            return None
        
        if version is None:
            # Get latest version
            versions = self._metadata[model_id]
            latest_version = max(versions, key=lambda v: v.created_at)
            version = latest_version.version
        
        # Find the specific version
        for v in self._metadata[model_id]:
            if v.version == version:
                try:
                    return joblib.load(v.model_path)
                except Exception as e:
                    logger.error(f"Failed to load model {model_id} v{version}: {e}")
                    return None
        
        return None
    
    def get_model_metadata(self, model_id: str, version: str = None) -> Optional[ModelMetadata]:
        """
        Get model metadata.
        
        Args:
            model_id: Model ID
            version: Model version (latest if None)
            
        Returns:
            Model metadata or None
        """
        if model_id not in self._metadata:
            return None
        
        if version is None:
            # Get latest version
            versions = self._metadata[model_id]
            latest_version = max(versions, key=lambda v: v.created_at)
            return latest_version.metadata
        
        # Find the specific version
        for v in self._metadata[model_id]:
            if v.version == version:
                return v.metadata
        
        return None
    
    def list_models(self, model_type: ModelType = None, status: ModelStatus = None) -> List[ModelMetadata]:
        """
        List models in the registry.
        
        Args:
            model_type: Filter by model type
            status: Filter by model status
            
        Returns:
            List of model metadata
        """
        models = []
        for model_id, versions in self._metadata.items():
            for version in versions:
                metadata = version.metadata
                if model_type and metadata.model_type != model_type:
                    continue
                if status and metadata.status != status:
                    continue
                models.append(metadata)
        
        return sorted(models, key=lambda m: m.created_at, reverse=True)
    
    def update_model_status(self, model_id: str, version: str, status: ModelStatus):
        """
        Update model status.
        
        Args:
            model_id: Model ID
            version: Model version
            status: New status
        """
        if model_id not in self._metadata:
            return
        
        for v in self._metadata[model_id]:
            if v.version == version:
                v.metadata.status = status
                v.metadata.updated_at = datetime.utcnow()
                self._save_metadata()
                logger.info(f"Updated model {model_id} v{version} status to {status}")
                break
    
    def add_performance_metrics(self, model_id: str, version: str, metrics: Dict[str, float]):
        """
        Add performance metrics to a model.
        
        Args:
            model_id: Model ID
            version: Model version
            metrics: Performance metrics
        """
        if model_id not in self._metadata:
            return
        
        for v in self._metadata[model_id]:
            if v.version == version:
                v.metadata.metrics.update(metrics)
                v.metadata.updated_at = datetime.utcnow()
                
                # Add to performance history
                performance_record = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": metrics
                }
                v.metadata.performance_history.append(performance_record)
                
                self._save_metadata()
                logger.info(f"Added performance metrics to model {model_id} v{version}")
                break
    
    def compare_models(self, model_id: str, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two model versions.
        
        Args:
            model_id: Model ID
            version1: First version
            version2: Second version
            
        Returns:
            Comparison results
        """
        metadata1 = self.get_model_metadata(model_id, version1)
        metadata2 = self.get_model_metadata(model_id, version2)
        
        if not metadata1 or not metadata2:
            return {}
        
        comparison = {
            "model_id": model_id,
            "version1": version1,
            "version2": version2,
            "metrics_comparison": {},
            "parameter_differences": {},
            "file_size_difference": metadata2.file_size - metadata1.file_size,
            "creation_time_difference": (metadata2.created_at - metadata1.created_at).total_seconds()
        }
        
        # Compare metrics
        all_metrics = set(metadata1.metrics.keys()) | set(metadata2.metrics.keys())
        for metric in all_metrics:
            val1 = metadata1.metrics.get(metric, 0)
            val2 = metadata2.metrics.get(metric, 0)
            comparison["metrics_comparison"][metric] = {
                "version1": val1,
                "version2": val2,
                "difference": val2 - val1,
                "improvement": val2 > val1 if metric in ["accuracy", "f1_score", "precision", "recall"] else val2 < val1
            }
        
        # Compare parameters
        all_params = set(metadata1.parameters.keys()) | set(metadata2.parameters.keys())
        for param in all_params:
            val1 = metadata1.parameters.get(param)
            val2 = metadata2.parameters.get(param)
            if val1 != val2:
                comparison["parameter_differences"][param] = {
                    "version1": val1,
                    "version2": val2
                }
        
        return comparison
    
    def delete_model(self, model_id: str, version: str = None):
        """
        Delete a model or model version.
        
        Args:
            model_id: Model ID
            version: Model version (all versions if None)
        """
        if model_id not in self._metadata:
            return
        
        if version is None:
            # Delete all versions
            model_dir = self.models_path / model_id
            if model_dir.exists():
                import shutil
                shutil.rmtree(model_dir)
            del self._metadata[model_id]
        else:
            # Delete specific version
            versions = self._metadata[model_id]
            for i, v in enumerate(versions):
                if v.version == version:
                    # Delete model file
                    model_path = Path(v.model_path)
                    if model_path.exists():
                        model_path.unlink()
                    
                    # Remove from registry
                    versions.pop(i)
                    break
            
            # If no versions left, remove model directory
            if not versions:
                model_dir = self.models_path / model_id
                if model_dir.exists():
                    import shutil
                    shutil.rmtree(model_dir)
                del self._metadata[model_id]
        
        self._save_metadata()
        logger.info(f"Deleted model {model_id} v{version or 'all'}")
    
    def _generate_model_id(self, name: str) -> str:
        """Generate a unique model ID."""
        base_id = hashlib.md5(name.encode()).hexdigest()[:8]
        counter = 1
        model_id = f"{base_id}_{counter}"
        
        while model_id in self._metadata:
            counter += 1
            model_id = f"{base_id}_{counter}"
        
        return model_id
    
    def _get_next_version(self, model_id: str) -> str:
        """Get the next version number for a model."""
        if model_id not in self._metadata:
            return "1.0.0"
        
        versions = [v.version for v in self._metadata[model_id]]
        if not versions:
            return "1.0.0"
        
        # Simple version increment (can be made more sophisticated)
        latest_version = max(versions, key=lambda v: [int(x) for x in v.split('.')])
        major, minor, patch = map(int, latest_version.split('.'))
        return f"{major}.{minor}.{patch + 1}"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_models = len(self._metadata)
        total_versions = sum(len(versions) for versions in self._metadata.values())
        
        model_types = {}
        statuses = {}
        
        for model_id, versions in self._metadata.items():
            for version in versions:
                model_type = version.metadata.model_type.value
                status = version.metadata.status.value
                
                model_types[model_type] = model_types.get(model_type, 0) + 1
                statuses[status] = statuses.get(status, 0) + 1
        
        return {
            "total_models": total_models,
            "total_versions": total_versions,
            "model_types": model_types,
            "statuses": statuses,
            "registry_size_mb": self._get_registry_size()
        }
    
    def _get_registry_size(self) -> float:
        """Get registry size in MB."""
        total_size = 0
        for model_id, versions in self._metadata.items():
            for version in versions:
                model_path = Path(version.model_path)
                if model_path.exists():
                    total_size += model_path.stat().st_size
        return total_size / (1024 * 1024)  # Convert to MB
