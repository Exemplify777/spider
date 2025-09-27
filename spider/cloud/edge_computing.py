"""
Edge Computing

Advanced edge computing capabilities for distributed AI/ML processing.
Includes edge node management, deployment, and monitoring.

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

logger = logging.getLogger(__name__)


class EdgeNodeStatus(str, Enum):
    """Edge node status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class EdgeNodeType(str, Enum):
    """Edge node type enumeration."""
    CPU_ONLY = "cpu_only"
    GPU_ENABLED = "gpu_enabled"
    MOBILE = "mobile"
    IOT = "iot"
    GATEWAY = "gateway"


class DeploymentStatus(str, Enum):
    """Deployment status enumeration."""
    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    UPDATING = "updating"
    ROLLING_BACK = "rolling_back"


@dataclass
class EdgeNode:
    """Edge node representation."""
    node_id: str
    name: str
    node_type: EdgeNodeType
    status: EdgeNodeStatus
    location: str
    ip_address: str
    port: int
    capabilities: List[str]
    resources: Dict[str, Any]
    last_heartbeat: datetime
    created_at: datetime
    metadata: Dict[str, Any] = None


@dataclass
class EdgeDeployment:
    """Edge deployment representation."""
    deployment_id: str
    model_id: str
    model_version: str
    node_id: str
    status: DeploymentStatus
    created_at: datetime
    updated_at: datetime
    configuration: Dict[str, Any]
    performance_metrics: Dict[str, float] = None
    error_logs: List[str] = None


@dataclass
class EdgeTask:
    """Edge task representation."""
    task_id: str
    node_id: str
    task_type: str
    payload: Dict[str, Any]
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class EdgeNodeManager:
    """Edge node management system."""
    
    def __init__(self):
        """Initialize edge node manager."""
        self.nodes: Dict[str, EdgeNode] = {}
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 120  # seconds
    
    def register_node(self, name: str, node_type: EdgeNodeType, 
                     location: str, ip_address: str, port: int,
                     capabilities: List[str], resources: Dict[str, Any],
                     metadata: Dict[str, Any] = None) -> str:
        """
        Register a new edge node.
        
        Args:
            name: Node name
            node_type: Node type
            location: Node location
            ip_address: Node IP address
            port: Node port
            capabilities: Node capabilities
            resources: Node resources
            metadata: Additional metadata
            
        Returns:
            Node ID
        """
        node_id = str(uuid.uuid4())
        
        node = EdgeNode(
            node_id=node_id,
            name=name,
            node_type=node_type,
            status=EdgeNodeStatus.ONLINE,
            location=location,
            ip_address=ip_address,
            port=port,
            capabilities=capabilities,
            resources=resources,
            last_heartbeat=datetime.utcnow(),
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self.nodes[node_id] = node
        logger.info(f"Registered edge node: {name} ({node_id})")
        
        return node_id
    
    def unregister_node(self, node_id: str) -> bool:
        """
        Unregister an edge node.
        
        Args:
            node_id: Node ID
            
        Returns:
            True if successful
        """
        if node_id in self.nodes:
            node = self.nodes[node_id]
            del self.nodes[node_id]
            logger.info(f"Unregistered edge node: {node.name} ({node_id})")
            return True
        
        return False
    
    def update_node_status(self, node_id: str, status: EdgeNodeStatus) -> bool:
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
            self.nodes[node_id].last_heartbeat = datetime.utcnow()
            logger.info(f"Updated node {node_id} status to {status.value}")
            return True
        
        return False
    
    def update_heartbeat(self, node_id: str) -> bool:
        """
        Update node heartbeat.
        
        Args:
            node_id: Node ID
            
        Returns:
            True if successful
        """
        if node_id in self.nodes:
            self.nodes[node_id].last_heartbeat = datetime.utcnow()
            return True
        
        return False
    
    def get_node(self, node_id: str) -> Optional[EdgeNode]:
        """Get node by ID."""
        return self.nodes.get(node_id)
    
    def list_nodes(self, status: EdgeNodeStatus = None, 
                   node_type: EdgeNodeType = None) -> List[EdgeNode]:
        """
        List edge nodes.
        
        Args:
            status: Filter by status
            node_type: Filter by node type
            
        Returns:
            List of edge nodes
        """
        nodes = list(self.nodes.values())
        
        if status:
            nodes = [n for n in nodes if n.status == status]
        
        if node_type:
            nodes = [n for n in nodes if n.node_type == node_type]
        
        return nodes
    
    def find_best_node(self, requirements: Dict[str, Any]) -> Optional[EdgeNode]:
        """
        Find the best node for given requirements.
        
        Args:
            requirements: Resource requirements
            
        Returns:
            Best matching node or None
        """
        available_nodes = [
            n for n in self.nodes.values() 
            if n.status == EdgeNodeStatus.ONLINE
        ]
        
        if not available_nodes:
            return None
        
        # Simple scoring algorithm
        best_node = None
        best_score = -1
        
        for node in available_nodes:
            score = 0
            
            # Check CPU requirements
            required_cpu = requirements.get('cpu_cores', 1)
            available_cpu = node.resources.get('cpu_cores', 0)
            if available_cpu >= required_cpu:
                score += available_cpu / required_cpu
            else:
                continue  # Skip nodes that don't meet requirements
            
            # Check memory requirements
            required_memory = requirements.get('memory_gb', 1)
            available_memory = node.resources.get('memory_gb', 0)
            if available_memory >= required_memory:
                score += available_memory / required_memory
            else:
                continue
            
            # Check GPU requirements
            required_gpu = requirements.get('gpu_required', False)
            has_gpu = node.resources.get('gpu_available', False)
            if required_gpu and not has_gpu:
                continue
            elif has_gpu:
                score += 2  # Bonus for GPU availability
            
            # Check capabilities
            required_capabilities = requirements.get('capabilities', [])
            for capability in required_capabilities:
                if capability in node.capabilities:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_node = node
        
        return best_node
    
    async def check_node_health(self) -> Dict[str, List[str]]:
        """
        Check health of all nodes.
        
        Returns:
            Dictionary of unhealthy nodes by status
        """
        unhealthy_nodes = {
            "offline": [],
            "timeout": [],
            "error": []
        }
        
        current_time = datetime.utcnow()
        
        for node_id, node in self.nodes.items():
            time_since_heartbeat = (current_time - node.last_heartbeat).total_seconds()
            
            if node.status == EdgeNodeStatus.ERROR:
                unhealthy_nodes["error"].append(node_id)
            elif time_since_heartbeat > self.heartbeat_timeout:
                node.status = EdgeNodeStatus.OFFLINE
                unhealthy_nodes["timeout"].append(node_id)
            elif node.status == EdgeNodeStatus.OFFLINE:
                unhealthy_nodes["offline"].append(node_id)
        
        return unhealthy_nodes


class EdgeDeploymentManager:
    """Edge deployment management system."""
    
    def __init__(self, node_manager: EdgeNodeManager):
        """
        Initialize edge deployment manager.
        
        Args:
            node_manager: Edge node manager instance
        """
        self.node_manager = node_manager
        self.deployments: Dict[str, EdgeDeployment] = {}
    
    def create_deployment(self, model_id: str, model_version: str,
                         node_id: str, configuration: Dict[str, Any]) -> str:
        """
        Create edge deployment.
        
        Args:
            model_id: Model ID
            model_version: Model version
            node_id: Target node ID
            configuration: Deployment configuration
            
        Returns:
            Deployment ID
        """
        deployment_id = str(uuid.uuid4())
        
        deployment = EdgeDeployment(
            deployment_id=deployment_id,
            model_id=model_id,
            model_version=model_version,
            node_id=node_id,
            status=DeploymentStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            configuration=configuration
        )
        
        self.deployments[deployment_id] = deployment
        logger.info(f"Created edge deployment: {deployment_id}")
        
        # Start deployment process
        asyncio.create_task(self._deploy_model_async(deployment_id))
        
        return deployment_id
    
    async def _deploy_model_async(self, deployment_id: str):
        """Asynchronous model deployment."""
        deployment = self.deployments[deployment_id]
        deployment.status = DeploymentStatus.DEPLOYING
        deployment.updated_at = datetime.utcnow()
        
        try:
            # Simulate deployment process
            await asyncio.sleep(5)  # Simulate deployment time
            
            # Check if node is still available
            node = self.node_manager.get_node(deployment.node_id)
            if not node or node.status != EdgeNodeStatus.ONLINE:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_logs = ["Target node is not available"]
            else:
                deployment.status = DeploymentStatus.DEPLOYED
                deployment.performance_metrics = {
                    "deployment_time": 5.0,
                    "model_size_mb": 50.0,
                    "memory_usage_mb": 100.0
                }
            
            deployment.updated_at = datetime.utcnow()
            logger.info(f"Deployment {deployment_id} status: {deployment.status.value}")
            
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_logs = [str(e)]
            deployment.updated_at = datetime.utcnow()
            logger.error(f"Deployment {deployment_id} failed: {e}")
    
    def get_deployment(self, deployment_id: str) -> Optional[EdgeDeployment]:
        """Get deployment by ID."""
        return self.deployments.get(deployment_id)
    
    def list_deployments(self, node_id: str = None, 
                        status: DeploymentStatus = None) -> List[EdgeDeployment]:
        """
        List deployments.
        
        Args:
            node_id: Filter by node ID
            status: Filter by status
            
        Returns:
            List of deployments
        """
        deployments = list(self.deployments.values())
        
        if node_id:
            deployments = [d for d in deployments if d.node_id == node_id]
        
        if status:
            deployments = [d for d in deployments if d.status == status]
        
        return deployments
    
    def delete_deployment(self, deployment_id: str) -> bool:
        """
        Delete deployment.
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            True if successful
        """
        if deployment_id in self.deployments:
            del self.deployments[deployment_id]
            logger.info(f"Deleted deployment: {deployment_id}")
            return True
        
        return False


class EdgeTaskManager:
    """Edge task management system."""
    
    def __init__(self, node_manager: EdgeNodeManager):
        """
        Initialize edge task manager.
        
        Args:
            node_manager: Edge node manager instance
        """
        self.node_manager = node_manager
        self.tasks: Dict[str, EdgeTask] = {}
        self.task_queue: List[str] = []
    
    def submit_task(self, node_id: str, task_type: str, 
                   payload: Dict[str, Any]) -> str:
        """
        Submit task to edge node.
        
        Args:
            node_id: Target node ID
            task_type: Task type
            payload: Task payload
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        task = EdgeTask(
            task_id=task_id,
            node_id=node_id,
            task_type=task_type,
            payload=payload,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self.tasks[task_id] = task
        self.task_queue.append(task_id)
        
        logger.info(f"Submitted task: {task_id} to node {node_id}")
        
        # Start task processing
        asyncio.create_task(self._process_task_async(task_id))
        
        return task_id
    
    async def _process_task_async(self, task_id: str):
        """Asynchronous task processing."""
        task = self.tasks[task_id]
        task.status = "running"
        task.started_at = datetime.utcnow()
        
        try:
            # Check if node is available
            node = self.node_manager.get_node(task.node_id)
            if not node or node.status != EdgeNodeStatus.ONLINE:
                task.status = "failed"
                task.error = "Target node is not available"
                task.completed_at = datetime.utcnow()
                return
            
            # Simulate task processing
            await asyncio.sleep(2)  # Simulate processing time
            
            # Generate result based on task type
            if task.task_type == "inference":
                task.result = {
                    "predictions": [0.8, 0.2, 0.1],
                    "confidence": 0.85,
                    "processing_time": 2.0
                }
            elif task.task_type == "training":
                task.result = {
                    "accuracy": 0.92,
                    "loss": 0.15,
                    "training_time": 2.0
                }
            else:
                task.result = {
                    "status": "completed",
                    "processing_time": 2.0
                }
            
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            logger.error(f"Task {task_id} failed: {e}")
    
    def get_task(self, task_id: str) -> Optional[EdgeTask]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def list_tasks(self, node_id: str = None, status: str = None) -> List[EdgeTask]:
        """
        List tasks.
        
        Args:
            node_id: Filter by node ID
            status: Filter by status
            
        Returns:
            List of tasks
        """
        tasks = list(self.tasks.values())
        
        if node_id:
            tasks = [t for t in tasks if t.node_id == node_id]
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        return tasks
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task statistics."""
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.status == "completed"])
        failed_tasks = len([t for t in self.tasks.values() if t.status == "failed"])
        running_tasks = len([t for t in self.tasks.values() if t.status == "running"])
        pending_tasks = len([t for t in self.tasks.values() if t.status == "pending"])
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "pending_tasks": pending_tasks,
            "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0
        }


class EdgeMonitoring:
    """Edge computing monitoring system."""
    
    def __init__(self, node_manager: EdgeNodeManager,
                 deployment_manager: EdgeDeploymentManager,
                 task_manager: EdgeTaskManager):
        """
        Initialize edge monitoring.
        
        Args:
            node_manager: Edge node manager
            deployment_manager: Edge deployment manager
            task_manager: Edge task manager
        """
        self.node_manager = node_manager
        self.deployment_manager = deployment_manager
        self.task_manager = task_manager
        self.metrics_history: List[Dict[str, Any]] = []
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect edge computing metrics.
        
        Returns:
            Collected metrics
        """
        # Node metrics
        nodes = self.node_manager.list_nodes()
        online_nodes = len([n for n in nodes if n.status == EdgeNodeStatus.ONLINE])
        offline_nodes = len([n for n in nodes if n.status == EdgeNodeStatus.OFFLINE])
        
        # Deployment metrics
        deployments = self.deployment_manager.list_deployments()
        active_deployments = len([d for d in deployments if d.status == DeploymentStatus.DEPLOYED])
        
        # Task metrics
        task_stats = self.task_manager.get_task_statistics()
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "nodes": {
                "total": len(nodes),
                "online": online_nodes,
                "offline": offline_nodes,
                "health_percentage": (online_nodes / len(nodes) * 100) if nodes else 0
            },
            "deployments": {
                "total": len(deployments),
                "active": active_deployments,
                "pending": len([d for d in deployments if d.status == DeploymentStatus.PENDING]),
                "failed": len([d for d in deployments if d.status == DeploymentStatus.FAILED])
            },
            "tasks": task_stats
        }
        
        self.metrics_history.append(metrics)
        
        # Keep only last 1000 metrics
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return metrics
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get metrics history.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of historical metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            m for m in self.metrics_history
            if datetime.fromisoformat(m["timestamp"]) >= cutoff_time
        ]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary."""
        nodes = self.node_manager.list_nodes()
        deployments = self.deployment_manager.list_deployments()
        task_stats = self.task_manager.get_task_statistics()
        
        # Calculate overall health score
        node_health = len([n for n in nodes if n.status == EdgeNodeStatus.ONLINE]) / len(nodes) if nodes else 0
        deployment_health = len([d for d in deployments if d.status == DeploymentStatus.DEPLOYED]) / len(deployments) if deployments else 0
        task_health = task_stats.get("success_rate", 0)
        
        overall_health = (node_health + deployment_health + task_health) / 3
        
        return {
            "overall_health": overall_health,
            "status": "healthy" if overall_health > 0.8 else "degraded" if overall_health > 0.5 else "unhealthy",
            "node_health": node_health,
            "deployment_health": deployment_health,
            "task_health": task_health,
            "last_updated": datetime.utcnow().isoformat()
        }


class EdgeComputing:
    """Main edge computing system."""
    
    def __init__(self):
        """Initialize edge computing system."""
        self.node_manager = EdgeNodeManager()
        self.deployment_manager = EdgeDeploymentManager(self.node_manager)
        self.task_manager = EdgeTaskManager(self.node_manager)
        self.monitoring = EdgeMonitoring(
            self.node_manager, 
            self.deployment_manager, 
            self.task_manager
        )
    
    async def start_monitoring(self, interval: int = 60):
        """
        Start edge monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        while True:
            try:
                await self.collect_metrics()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Edge monitoring error: {e}")
                await asyncio.sleep(interval)
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect edge computing metrics."""
        return await self.monitoring.collect_metrics()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        health_summary = self.monitoring.get_health_summary()
        task_stats = self.task_manager.get_task_statistics()
        
        return {
            "health": health_summary,
            "tasks": task_stats,
            "nodes": len(self.node_manager.list_nodes()),
            "deployments": len(self.deployment_manager.list_deployments()),
            "last_updated": datetime.utcnow().isoformat()
        }
