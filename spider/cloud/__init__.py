"""
SPIDER Cloud Integration Module

Advanced cloud integration capabilities for AWS, Azure, and GCP services.
Includes cloud storage, compute, AI/ML services, and monitoring integration.

Author: SPIDER Development Team
Version: 1.0.0
"""

from .aws_integration import AWSIntegration, S3Storage, EC2Compute, LambdaFunctions, SageMakerML
from .azure_integration import AzureIntegration, BlobStorage, VMCompute, Functions, MLStudio
from .gcp_integration import GCPIntegration, CloudStorage, ComputeEngine, CloudFunctions, VertexAI
from .cloud_manager import CloudManager, CloudProvider, CloudConfig
from .edge_computing import EdgeComputing, EdgeNode, EdgeDeployment, EdgeMonitoring
from .federated_learning import FederatedLearning, FLNode, FLTraining, FLModel

__all__ = [
    # AWS Integration
    "AWSIntegration",
    "S3Storage", 
    "EC2Compute",
    "LambdaFunctions",
    "SageMakerML",
    
    # Azure Integration
    "AzureIntegration",
    "BlobStorage",
    "VMCompute", 
    "Functions",
    "MLStudio",
    
    # GCP Integration
    "GCPIntegration",
    "CloudStorage",
    "ComputeEngine",
    "CloudFunctions",
    "VertexAI",
    
    # Cloud Management
    "CloudManager",
    "CloudProvider",
    "CloudConfig",
    
    # Edge Computing
    "EdgeComputing",
    "EdgeNode",
    "EdgeDeployment", 
    "EdgeMonitoring",
    
    # Federated Learning
    "FederatedLearning",
    "FLNode",
    "FLTraining",
    "FLModel",
]
