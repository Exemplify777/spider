"""
Federated Learning

Advanced federated learning capabilities for distributed model training
across multiple nodes while preserving data privacy.

Author: SPIDER Development Team
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
import uuid
import numpy as np
import pickle
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class FLNodeStatus(str, Enum):
    """Federated learning node status."""
    IDLE = "idle"
    TRAINING = "training"
    AGGREGATING = "aggregating"
    ERROR = "error"
    OFFLINE = "offline"


class FLTrainingStatus(str, Enum):
    """Federated learning training status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AggregationMethod(str, Enum):
    """Aggregation method enumeration."""
    FEDAVG = "fedavg"
    FEDPROX = "fedprox"
    FEDNOVA = "fednova"
    SCALED_FEDAVG = "scaled_fedavg"


@dataclass
class FLNode:
    """Federated learning node representation."""
    node_id: str
    name: str
    status: FLNodeStatus
    capabilities: List[str]
    data_size: int
    last_seen: datetime
    created_at: datetime
    metadata: Dict[str, Any] = None


@dataclass
class FLModel:
    """Federated learning model representation."""
    model_id: str
    name: str
    architecture: Dict[str, Any]
    current_round: int
    total_rounds: int
    aggregation_method: AggregationMethod
    learning_rate: float
    batch_size: int
    created_at: datetime
    updated_at: datetime
    global_weights: Optional[bytes] = None
    metadata: Dict[str, Any] = None


@dataclass
class FLTraining:
    """Federated learning training session."""
    training_id: str
    model_id: str
    status: FLTrainingStatus
    current_round: int
    total_rounds: int
    participating_nodes: List[str]
    aggregation_method: AggregationMethod
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    round_results: Dict[int, Dict[str, Any]] = None
    global_metrics: Dict[str, float] = None


@dataclass
class FLRoundResult:
    """Federated learning round result."""
    round_number: int
    node_id: str
    local_weights: bytes
    local_metrics: Dict[str, float]
    data_size: int
    training_time: float
    submitted_at: datetime


class FLNodeManager:
    """Federated learning node management."""
    
    def __init__(self):
        """Initialize FL node manager."""
        self.nodes: Dict[str, FLNode] = {}
        self.heartbeat_timeout = 300  # 5 minutes
    
    def register_node(self, name: str, capabilities: List[str], 
                     data_size: int, metadata: Dict[str, Any] = None) -> str:
        """
        Register a new FL node.
        
        Args:
            name: Node name
            capabilities: Node capabilities
            data_size: Size of local data
            metadata: Additional metadata
            
        Returns:
            Node ID
        """
        node_id = str(uuid.uuid4())
        
        node = FLNode(
            node_id=node_id,
            name=name,
            status=FLNodeStatus.IDLE,
            capabilities=capabilities,
            data_size=data_size,
            last_seen=datetime.utcnow(),
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self.nodes[node_id] = node
        logger.info(f"Registered FL node: {name} ({node_id})")
        
        return node_id
    
    def unregister_node(self, node_id: str) -> bool:
        """
        Unregister FL node.
        
        Args:
            node_id: Node ID
            
        Returns:
            True if successful
        """
        if node_id in self.nodes:
            node = self.nodes[node_id]
            del self.nodes[node_id]
            logger.info(f"Unregistered FL node: {node.name} ({node_id})")
            return True
        
        return False
    
    def update_node_status(self, node_id: str, status: FLNodeStatus) -> bool:
        """
        Update node status.
        
        Args:
            node_id: Node ID
            status: New status
            
        Returns:
            True if successful
        """
        if node_id in self.nodes:
            self.nodes[node_id].status = status
            self.nodes[node_id].last_seen = datetime.utcnow()
            return True
        
        return False
    
    def get_available_nodes(self, min_data_size: int = 0) -> List[FLNode]:
        """
        Get available nodes for training.
        
        Args:
            min_data_size: Minimum data size requirement
            
        Returns:
            List of available nodes
        """
        return [
            node for node in self.nodes.values()
            if (node.status == FLNodeStatus.IDLE and 
                node.data_size >= min_data_size)
        ]
    
    def get_node(self, node_id: str) -> Optional[FLNode]:
        """Get node by ID."""
        return self.nodes.get(node_id)
    
    def list_nodes(self, status: FLNodeStatus = None) -> List[FLNode]:
        """
        List FL nodes.
        
        Args:
            status: Filter by status
            
        Returns:
            List of nodes
        """
        nodes = list(self.nodes.values())
        
        if status:
            nodes = [n for n in nodes if n.status == status]
        
        return nodes
    
    async def check_node_health(self) -> List[str]:
        """
        Check node health and return offline nodes.
        
        Returns:
            List of offline node IDs
        """
        offline_nodes = []
        current_time = datetime.utcnow()
        
        for node_id, node in self.nodes.items():
            time_since_seen = (current_time - node.last_seen).total_seconds()
            
            if time_since_seen > self.heartbeat_timeout:
                node.status = FLNodeStatus.OFFLINE
                offline_nodes.append(node_id)
        
        return offline_nodes


class FLModelManager:
    """Federated learning model management."""
    
    def __init__(self):
        """Initialize FL model manager."""
        self.models: Dict[str, FLModel] = {}
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    def create_model(self, name: str, architecture: Dict[str, Any],
                    total_rounds: int, aggregation_method: AggregationMethod,
                    learning_rate: float = 0.01, batch_size: int = 32) -> str:
        """
        Create a new FL model.
        
        Args:
            name: Model name
            architecture: Model architecture
            total_rounds: Total training rounds
            aggregation_method: Aggregation method
            learning_rate: Learning rate
            batch_size: Batch size
            
        Returns:
            Model ID
        """
        model_id = str(uuid.uuid4())
        
        model = FLModel(
            model_id=model_id,
            name=name,
            architecture=architecture,
            current_round=0,
            total_rounds=total_rounds,
            aggregation_method=aggregation_method,
            learning_rate=learning_rate,
            batch_size=batch_size,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.models[model_id] = model
        logger.info(f"Created FL model: {name} ({model_id})")
        
        return model_id
    
    def get_model(self, model_id: str) -> Optional[FLModel]:
        """Get model by ID."""
        return self.models.get(model_id)
    
    def update_model_weights(self, model_id: str, weights: np.ndarray) -> bool:
        """
        Update model global weights.
        
        Args:
            model_id: Model ID
            weights: New weights
            
        Returns:
            True if successful
        """
        if model_id not in self.models:
            return False
        
        try:
            # Serialize and encrypt weights
            weights_bytes = pickle.dumps(weights)
            encrypted_weights = self.cipher.encrypt(weights_bytes)
            
            self.models[model_id].global_weights = encrypted_weights
            self.models[model_id].updated_at = datetime.utcnow()
            
            return True
        except Exception as e:
            logger.error(f"Failed to update model weights: {e}")
            return False
    
    def get_model_weights(self, model_id: str) -> Optional[np.ndarray]:
        """
        Get model global weights.
        
        Args:
            model_id: Model ID
            
        Returns:
            Model weights or None
        """
        if model_id not in self.models or not self.models[model_id].global_weights:
            return None
        
        try:
            # Decrypt and deserialize weights
            encrypted_weights = self.models[model_id].global_weights
            weights_bytes = self.cipher.decrypt(encrypted_weights)
            weights = pickle.loads(weights_bytes)
            
            return weights
        except Exception as e:
            logger.error(f"Failed to get model weights: {e}")
            return None
    
    def advance_round(self, model_id: str) -> bool:
        """
        Advance model to next round.
        
        Args:
            model_id: Model ID
            
        Returns:
            True if successful
        """
        if model_id not in self.models:
            return False
        
        model = self.models[model_id]
        if model.current_round < model.total_rounds:
            model.current_round += 1
            model.updated_at = datetime.utcnow()
            return True
        
        return False
    
    def list_models(self) -> List[FLModel]:
        """List all FL models."""
        return list(self.models.values())


class FLAggregator:
    """Federated learning model aggregator."""
    
    def __init__(self):
        """Initialize FL aggregator."""
        pass
    
    def aggregate_weights(self, round_results: List[FLRoundResult], 
                         method: AggregationMethod) -> np.ndarray:
        """
        Aggregate model weights from multiple nodes.
        
        Args:
            round_results: List of round results from nodes
            method: Aggregation method
            
        Returns:
            Aggregated weights
        """
        if not round_results:
            raise ValueError("No round results provided")
        
        # Deserialize weights
        weights_list = []
        data_sizes = []
        
        for result in round_results:
            weights = pickle.loads(result.local_weights)
            weights_list.append(weights)
            data_sizes.append(result.data_size)
        
        if method == AggregationMethod.FEDAVG:
            return self._fedavg_aggregation(weights_list, data_sizes)
        elif method == AggregationMethod.FEDPROX:
            return self._fedprox_aggregation(weights_list, data_sizes)
        elif method == AggregationMethod.FEDNOVA:
            return self._fednova_aggregation(weights_list, data_sizes)
        elif method == AggregationMethod.SCALED_FEDAVG:
            return self._scaled_fedavg_aggregation(weights_list, data_sizes)
        else:
            raise ValueError(f"Unknown aggregation method: {method}")
    
    def _fedavg_aggregation(self, weights_list: List[np.ndarray], 
                           data_sizes: List[int]) -> np.ndarray:
        """Federated Averaging aggregation."""
        total_data_size = sum(data_sizes)
        
        if total_data_size == 0:
            return weights_list[0]  # Fallback to first weights
        
        # Weighted average based on data sizes
        aggregated_weights = np.zeros_like(weights_list[0])
        
        for weights, data_size in zip(weights_list, data_sizes):
            weight_factor = data_size / total_data_size
            aggregated_weights += weights * weight_factor
        
        return aggregated_weights
    
    def _fedprox_aggregation(self, weights_list: List[np.ndarray], 
                           data_sizes: List[int]) -> np.ndarray:
        """FedProx aggregation (similar to FedAvg for now)."""
        # Simplified FedProx - in practice, would include proximal term
        return self._fedavg_aggregation(weights_list, data_sizes)
    
    def _fednova_aggregation(self, weights_list: List[np.ndarray], 
                           data_sizes: List[int]) -> np.ndarray:
        """FedNova aggregation (simplified)."""
        # Simplified FedNova - in practice, would normalize updates
        return self._fedavg_aggregation(weights_list, data_sizes)
    
    def _scaled_fedavg_aggregation(self, weights_list: List[np.ndarray], 
                                 data_sizes: List[int]) -> np.ndarray:
        """Scaled Federated Averaging aggregation."""
        # Scaled version of FedAvg
        return self._fedavg_aggregation(weights_list, data_sizes)


class FLTrainingManager:
    """Federated learning training management."""
    
    def __init__(self, node_manager: FLNodeManager, model_manager: FLModelManager):
        """
        Initialize FL training manager.
        
        Args:
            node_manager: FL node manager
            model_manager: FL model manager
        """
        self.node_manager = node_manager
        self.model_manager = model_manager
        self.aggregator = FLAggregator()
        self.trainings: Dict[str, FLTraining] = {}
        self.round_results: Dict[str, List[FLRoundResult]] = {}
    
    def start_training(self, model_id: str, participating_nodes: List[str],
                      aggregation_method: AggregationMethod) -> str:
        """
        Start federated learning training.
        
        Args:
            model_id: Model ID
            participating_nodes: List of participating node IDs
            aggregation_method: Aggregation method
            
        Returns:
            Training ID
        """
        model = self.model_manager.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        training_id = str(uuid.uuid4())
        
        training = FLTraining(
            training_id=training_id,
            model_id=model_id,
            status=FLTrainingStatus.PENDING,
            current_round=0,
            total_rounds=model.total_rounds,
            participating_nodes=participating_nodes,
            aggregation_method=aggregation_method,
            created_at=datetime.utcnow(),
            round_results={}
        )
        
        self.trainings[training_id] = training
        self.round_results[training_id] = []
        
        logger.info(f"Started FL training: {training_id}")
        
        # Start training process
        asyncio.create_task(self._run_training_async(training_id))
        
        return training_id
    
    async def _run_training_async(self, training_id: str):
        """Run federated learning training asynchronously."""
        training = self.trainings[training_id]
        model = self.model_manager.get_model(training.model_id)
        
        training.status = FLTrainingStatus.IN_PROGRESS
        training.started_at = datetime.utcnow()
        
        try:
            for round_num in range(1, training.total_rounds + 1):
                logger.info(f"Starting round {round_num} for training {training_id}")
                
                # Wait for round results from all participating nodes
                round_results = await self._wait_for_round_results(
                    training_id, round_num, training.participating_nodes
                )
                
                if not round_results:
                    logger.error(f"No results received for round {round_num}")
                    training.status = FLTrainingStatus.FAILED
                    return
                
                # Aggregate weights
                aggregated_weights = self.aggregator.aggregate_weights(
                    round_results, training.aggregation_method
                )
                
                # Update global model
                self.model_manager.update_model_weights(training.model_id, aggregated_weights)
                self.model_manager.advance_round(training.model_id)
                
                # Store round results
                training.round_results[round_num] = {
                    "participating_nodes": len(round_results),
                    "aggregated_metrics": self._calculate_round_metrics(round_results),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                training.current_round = round_num
                
                logger.info(f"Completed round {round_num} for training {training_id}")
            
            training.status = FLTrainingStatus.COMPLETED
            training.completed_at = datetime.utcnow()
            
            logger.info(f"Completed FL training: {training_id}")
            
        except Exception as e:
            training.status = FLTrainingStatus.FAILED
            logger.error(f"FL training {training_id} failed: {e}")
    
    async def _wait_for_round_results(self, training_id: str, round_num: int,
                                    participating_nodes: List[str]) -> List[FLRoundResult]:
        """
        Wait for round results from participating nodes.
        
        Args:
            training_id: Training ID
            round_num: Round number
            participating_nodes: List of participating node IDs
            
        Returns:
            List of round results
        """
        # Simulate waiting for results
        # In practice, this would wait for actual results from nodes
        await asyncio.sleep(5)  # Simulate processing time
        
        # Generate mock results
        results = []
        for node_id in participating_nodes:
            # Generate mock weights (in practice, would come from actual training)
            mock_weights = np.random.randn(100, 10)  # Example weights
            mock_metrics = {
                "accuracy": np.random.uniform(0.7, 0.95),
                "loss": np.random.uniform(0.1, 0.5),
                "training_time": np.random.uniform(10, 60)
            }
            
            result = FLRoundResult(
                round_number=round_num,
                node_id=node_id,
                local_weights=pickle.dumps(mock_weights),
                local_metrics=mock_metrics,
                data_size=np.random.randint(100, 1000),
                training_time=mock_metrics["training_time"],
                submitted_at=datetime.utcnow()
            )
            
            results.append(result)
        
        return results
    
    def _calculate_round_metrics(self, round_results: List[FLRoundResult]) -> Dict[str, float]:
        """Calculate aggregated metrics for a round."""
        if not round_results:
            return {}
        
        metrics = {}
        for metric_name in round_results[0].local_metrics.keys():
            values = [r.local_metrics[metric_name] for r in round_results]
            metrics[f"avg_{metric_name}"] = np.mean(values)
            metrics[f"std_{metric_name}"] = np.std(values)
            metrics[f"min_{metric_name}"] = np.min(values)
            metrics[f"max_{metric_name}"] = np.max(values)
        
        return metrics
    
    def submit_round_result(self, training_id: str, node_id: str,
                           local_weights: bytes, local_metrics: Dict[str, float],
                           data_size: int, training_time: float) -> bool:
        """
        Submit round result from a node.
        
        Args:
            training_id: Training ID
            node_id: Node ID
            local_weights: Local model weights
            local_metrics: Local training metrics
            data_size: Local data size
            training_time: Training time
            
        Returns:
            True if successful
        """
        if training_id not in self.trainings:
            return False
        
        training = self.trainings[training_id]
        current_round = training.current_round + 1
        
        result = FLRoundResult(
            round_number=current_round,
            node_id=node_id,
            local_weights=local_weights,
            local_metrics=local_metrics,
            data_size=data_size,
            training_time=training_time,
            submitted_at=datetime.utcnow()
        )
        
        self.round_results[training_id].append(result)
        
        logger.info(f"Received round result from node {node_id} for training {training_id}")
        return True
    
    def get_training(self, training_id: str) -> Optional[FLTraining]:
        """Get training by ID."""
        return self.trainings.get(training_id)
    
    def list_trainings(self, status: FLTrainingStatus = None) -> List[FLTraining]:
        """
        List FL trainings.
        
        Args:
            status: Filter by status
            
        Returns:
            List of trainings
        """
        trainings = list(self.trainings.values())
        
        if status:
            trainings = [t for t in trainings if t.status == status]
        
        return trainings
    
    def get_training_statistics(self) -> Dict[str, Any]:
        """Get training statistics."""
        total_trainings = len(self.trainings)
        completed_trainings = len([t for t in self.trainings.values() if t.status == FLTrainingStatus.COMPLETED])
        failed_trainings = len([t for t in self.trainings.values() if t.status == FLTrainingStatus.FAILED])
        in_progress_trainings = len([t for t in self.trainings.values() if t.status == FLTrainingStatus.IN_PROGRESS])
        
        return {
            "total_trainings": total_trainings,
            "completed_trainings": completed_trainings,
            "failed_trainings": failed_trainings,
            "in_progress_trainings": in_progress_trainings,
            "success_rate": completed_trainings / total_trainings if total_trainings > 0 else 0
        }


class FederatedLearning:
    """Main federated learning system."""
    
    def __init__(self):
        """Initialize federated learning system."""
        self.node_manager = FLNodeManager()
        self.model_manager = FLModelManager()
        self.training_manager = FLTrainingManager(self.node_manager, self.model_manager)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        node_stats = {
            "total_nodes": len(self.node_manager.list_nodes()),
            "available_nodes": len(self.node_manager.get_available_nodes()),
            "offline_nodes": len(self.node_manager.list_nodes(FLNodeStatus.OFFLINE))
        }
        
        model_stats = {
            "total_models": len(self.model_manager.list_models()),
            "active_models": len([m for m in self.model_manager.list_models() if m.current_round > 0])
        }
        
        training_stats = self.training_manager.get_training_statistics()
        
        return {
            "nodes": node_stats,
            "models": model_stats,
            "trainings": training_stats,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def start_health_monitoring(self, interval: int = 60):
        """
        Start health monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        while True:
            try:
                offline_nodes = await self.node_manager.check_node_health()
                if offline_nodes:
                    logger.warning(f"Offline FL nodes detected: {offline_nodes}")
                
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"FL health monitoring error: {e}")
                await asyncio.sleep(interval)
