"""
Test Suite for Cloud Integration Module

Comprehensive tests for the SPIDER cloud integration module including
AWS, Azure, GCP integration, edge computing, and federated learning.

Author: SPIDER Development Team
Version: 1.0.0
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from spider.cloud.aws_integration import (
    AWSIntegration, AWSConfig, S3Storage, EC2Compute, LambdaFunctions, SageMakerML
)
from spider.cloud.azure_integration import (
    AzureIntegration, AzureConfig, BlobStorage, VMCompute, Functions, MLStudio
)
from spider.cloud.gcp_integration import (
    GCPIntegration, GCPConfig, CloudStorage, ComputeEngine, CloudFunctions, VertexAI
)
from spider.cloud.cloud_manager import (
    CloudManager, CloudConfig, CloudProvider, ServiceType, CloudResource
)
from spider.cloud.edge_computing import (
    EdgeComputing, EdgeNodeManager, EdgeDeploymentManager, EdgeTaskManager,
    EdgeMonitoring, EdgeNodeStatus, EdgeNodeType, DeploymentStatus
)
from spider.cloud.federated_learning import (
    FederatedLearning, FLNodeManager, FLModelManager, FLTrainingManager,
    FLNodeStatus, FLTrainingStatus, AggregationMethod
)


class TestAWSIntegration:
    """Test AWS integration functionality."""
    
    @pytest.fixture
    def aws_config(self):
        """Create AWS configuration for testing."""
        return AWSConfig(
            access_key_id="test_key",
            secret_access_key="test_secret",
            region="us-east-1"
        )
    
    def test_aws_config(self, aws_config):
        """Test AWS configuration."""
        assert aws_config.access_key_id == "test_key"
        assert aws_config.secret_access_key == "test_secret"
        assert aws_config.region.value == "us-east-1"
    
    @patch('boto3.client')
    def test_s3_storage_initialization(self, mock_boto3, aws_config):
        """Test S3 storage initialization."""
        mock_s3_client = Mock()
        mock_boto3.return_value = mock_s3_client
        
        s3_storage = S3Storage(aws_config)
        assert s3_storage.config == aws_config
        mock_boto3.assert_called_once()
    
    @patch('boto3.client')
    async def test_s3_create_bucket(self, mock_boto3, aws_config):
        """Test S3 bucket creation."""
        mock_s3_client = Mock()
        mock_s3_client.create_bucket.return_value = {}
        mock_boto3.return_value = mock_s3_client
        
        s3_storage = S3Storage(aws_config)
        result = await s3_storage.create_bucket("test-bucket")
        
        assert result is True
        mock_s3_client.create_bucket.assert_called_once()
    
    @patch('boto3.client')
    async def test_s3_upload_file(self, mock_boto3, aws_config):
        """Test S3 file upload."""
        mock_s3_client = Mock()
        mock_s3_client.upload_file.return_value = None
        mock_boto3.return_value = mock_s3_client
        
        s3_storage = S3Storage(aws_config)
        
        # Mock file existence
        with patch('os.path.exists', return_value=True):
            result = await s3_storage.upload_file("test.txt", "test-bucket", "test-key")
        
        assert result is True
        mock_s3_client.upload_file.assert_called_once()
    
    @patch('boto3.client')
    def test_ec2_compute_initialization(self, mock_boto3, aws_config):
        """Test EC2 compute initialization."""
        mock_ec2_client = Mock()
        mock_boto3.return_value = mock_ec2_client
        
        ec2_compute = EC2Compute(aws_config)
        assert ec2_compute.config == aws_config
        mock_boto3.assert_called_once()
    
    @patch('boto3.client')
    async def test_ec2_create_instance(self, mock_boto3, aws_config):
        """Test EC2 instance creation."""
        mock_ec2_client = Mock()
        mock_ec2_client.run_instances.return_value = {
            'Instances': [{'InstanceId': 'i-1234567890abcdef0'}]
        }
        mock_boto3.return_value = mock_ec2_client
        
        ec2_compute = EC2Compute(aws_config)
        result = await ec2_compute.create_instance(
            "ami-12345678", "t2.micro", "test-key", ["sg-12345678"]
        )
        
        assert result == "i-1234567890abcdef0"
        mock_ec2_client.run_instances.assert_called_once()
    
    @patch('boto3.client')
    def test_lambda_functions_initialization(self, mock_boto3, aws_config):
        """Test Lambda functions initialization."""
        mock_lambda_client = Mock()
        mock_boto3.return_value = mock_lambda_client
        
        lambda_functions = LambdaFunctions(aws_config)
        assert lambda_functions.config == aws_config
        mock_boto3.assert_called_once()
    
    @patch('boto3.client')
    def test_sagemaker_ml_initialization(self, mock_boto3, aws_config):
        """Test SageMaker ML initialization."""
        mock_sagemaker_client = Mock()
        mock_boto3.return_value = mock_sagemaker_client
        
        sagemaker_ml = SageMakerML(aws_config)
        assert sagemaker_ml.config == aws_config
        mock_boto3.assert_called_once()


class TestAzureIntegration:
    """Test Azure integration functionality."""
    
    @pytest.fixture
    def azure_config(self):
        """Create Azure configuration for testing."""
        return AzureConfig(
            subscription_id="test-subscription",
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret",
            region="eastus"
        )
    
    def test_azure_config(self, azure_config):
        """Test Azure configuration."""
        assert azure_config.subscription_id == "test-subscription"
        assert azure_config.tenant_id == "test-tenant"
        assert azure_config.region.value == "eastus"
    
    @patch('azure.storage.blob.BlobServiceClient')
    def test_blob_storage_initialization(self, mock_blob_client, azure_config):
        """Test Blob Storage initialization."""
        mock_client = Mock()
        mock_blob_client.return_value = mock_client
        
        blob_storage = BlobStorage(azure_config)
        assert blob_storage.config == azure_config
        mock_blob_client.assert_called_once()
    
    @patch('azure.storage.blob.BlobServiceClient')
    async def test_blob_storage_create_container(self, mock_blob_client, azure_config):
        """Test Blob Storage container creation."""
        mock_client = Mock()
        mock_blob_client.return_value = mock_client
        
        blob_storage = BlobStorage(azure_config)
        result = await blob_storage.create_container("test-container")
        
        assert result is True
        mock_client.create_container.assert_called_once_with("test-container")
    
    @patch('azure.storage.blob.BlobServiceClient')
    async def test_blob_storage_upload_blob(self, mock_blob_client, azure_config):
        """Test Blob Storage blob upload."""
        mock_client = Mock()
        mock_blob_client.return_value = mock_client
        
        blob_storage = BlobStorage(azure_config)
        
        # Mock file existence
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()):
            result = await blob_storage.upload_blob("test.txt", "test-container", "test-blob")
        
        assert result is True


class TestGCPIntegration:
    """Test GCP integration functionality."""
    
    @pytest.fixture
    def gcp_config(self):
        """Create GCP configuration for testing."""
        return GCPConfig(
            project_id="test-project",
            service_account_path="test-key.json",
            region="us-central1"
        )
    
    def test_gcp_config(self, gcp_config):
        """Test GCP configuration."""
        assert gcp_config.project_id == "test-project"
        assert gcp_config.service_account_path == "test-key.json"
        assert gcp_config.region.value == "us-central1"
    
    @patch('google.cloud.storage.Client')
    def test_cloud_storage_initialization(self, mock_storage_client, gcp_config):
        """Test Cloud Storage initialization."""
        mock_client = Mock()
        mock_storage_client.return_value = mock_client
        
        cloud_storage = CloudStorage(gcp_config)
        assert cloud_storage.config == gcp_config
        mock_storage_client.assert_called_once()
    
    @patch('google.cloud.storage.Client')
    async def test_cloud_storage_create_bucket(self, mock_storage_client, gcp_config):
        """Test Cloud Storage bucket creation."""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_storage_client.return_value = mock_client
        
        cloud_storage = CloudStorage(gcp_config)
        result = await cloud_storage.create_bucket("test-bucket")
        
        assert result is True
        mock_client.bucket.assert_called_once_with("test-bucket")
        mock_bucket.create.assert_called_once()


class TestCloudManager:
    """Test cloud manager functionality."""
    
    @pytest.fixture
    def cloud_manager(self):
        """Create cloud manager for testing."""
        return CloudManager()
    
    def test_cloud_manager_initialization(self, cloud_manager):
        """Test cloud manager initialization."""
        assert isinstance(cloud_manager.providers, dict)
        assert isinstance(cloud_manager.resources, dict)
        assert isinstance(cloud_manager.costs, list)
    
    def test_add_aws_provider(self, cloud_manager):
        """Test adding AWS provider."""
        config = CloudConfig(
            provider=CloudProvider.AWS,
            region="us-east-1",
            credentials={
                "access_key_id": "test_key",
                "secret_access_key": "test_secret"
            }
        )
        
        with patch('spider.cloud.aws_integration.AWSIntegration') as mock_aws:
            result = cloud_manager.add_provider(config)
            assert result is True
            assert CloudProvider.AWS in cloud_manager.providers
    
    def test_add_azure_provider(self, cloud_manager):
        """Test adding Azure provider."""
        config = CloudConfig(
            provider=CloudProvider.AZURE,
            region="eastus",
            credentials={
                "subscription_id": "test-sub",
                "tenant_id": "test-tenant",
                "client_id": "test-client",
                "client_secret": "test-secret"
            },
            resource_group="test-rg"
        )
        
        with patch('spider.cloud.azure_integration.AzureIntegration') as mock_azure:
            result = cloud_manager.add_provider(config)
            assert result is True
            assert CloudProvider.AZURE in cloud_manager.providers
    
    def test_add_gcp_provider(self, cloud_manager):
        """Test adding GCP provider."""
        config = CloudConfig(
            provider=CloudProvider.GCP,
            region="us-central1",
            credentials={
                "service_account_path": "test-key.json"
            },
            project_id="test-project"
        )
        
        with patch('spider.cloud.gcp_integration.GCPIntegration') as mock_gcp:
            result = cloud_manager.add_provider(config)
            assert result is True
            assert CloudProvider.GCP in cloud_manager.providers
    
    async def test_test_all_connections(self, cloud_manager):
        """Test connection testing for all providers."""
        # Mock providers
        mock_aws = Mock()
        mock_aws.test_connection.return_value = True
        cloud_manager.providers[CloudProvider.AWS] = mock_aws
        
        mock_azure = Mock()
        mock_azure.test_connection.return_value = True
        cloud_manager.providers[CloudProvider.AZURE] = mock_azure
        
        results = await cloud_manager.test_all_connections()
        
        assert CloudProvider.AWS in results
        assert CloudProvider.AZURE in results
        assert results[CloudProvider.AWS] is True
        assert results[CloudProvider.AZURE] is True
    
    async def test_create_storage_resource(self, cloud_manager):
        """Test storage resource creation."""
        # Mock AWS provider
        mock_aws = Mock()
        mock_aws.s3.create_bucket.return_value = True
        cloud_manager.providers[CloudProvider.AWS] = mock_aws
        
        resource = await cloud_manager.create_storage_resource(
            CloudProvider.AWS, "test-bucket"
        )
        
        assert resource is not None
        assert resource.provider == CloudProvider.AWS
        assert resource.service_type == ServiceType.STORAGE
        assert resource.name == "test-bucket"
    
    def test_get_cloud_summary(self, cloud_manager):
        """Test cloud summary generation."""
        # Add some mock data
        cloud_manager.providers[CloudProvider.AWS] = Mock()
        cloud_manager.resources["test-resource"] = CloudResource(
            resource_id="test-resource",
            provider=CloudProvider.AWS,
            service_type=ServiceType.STORAGE,
            name="test-resource",
            region="us-east-1",
            status="created",
            created_at=datetime.utcnow()
        )
        
        summary = cloud_manager.get_cloud_summary()
        
        assert "total_providers" in summary
        assert "total_resources" in summary
        assert "providers" in summary
        assert summary["total_providers"] == 1
        assert summary["total_resources"] == 1


class TestEdgeComputing:
    """Test edge computing functionality."""
    
    @pytest.fixture
    def edge_computing(self):
        """Create edge computing system for testing."""
        return EdgeComputing()
    
    def test_edge_node_manager_initialization(self, edge_computing):
        """Test edge node manager initialization."""
        assert isinstance(edge_computing.node_manager, EdgeNodeManager)
        assert isinstance(edge_computing.node_manager.nodes, dict)
    
    def test_register_node(self, edge_computing):
        """Test node registration."""
        node_id = edge_computing.node_manager.register_node(
            name="test-node",
            node_type=EdgeNodeType.CPU_ONLY,
            location="test-location",
            ip_address="192.168.1.100",
            port=8080,
            capabilities=["inference", "training"],
            resources={"cpu_cores": 4, "memory_gb": 8}
        )
        
        assert node_id is not None
        assert node_id in edge_computing.node_manager.nodes
        
        node = edge_computing.node_manager.get_node(node_id)
        assert node.name == "test-node"
        assert node.node_type == EdgeNodeType.CPU_ONLY
        assert node.status == EdgeNodeStatus.ONLINE
    
    def test_find_best_node(self, edge_computing):
        """Test finding best node for requirements."""
        # Register multiple nodes
        node1_id = edge_computing.node_manager.register_node(
            name="node1",
            node_type=EdgeNodeType.CPU_ONLY,
            location="location1",
            ip_address="192.168.1.1",
            port=8080,
            capabilities=["inference"],
            resources={"cpu_cores": 2, "memory_gb": 4}
        )
        
        node2_id = edge_computing.node_manager.register_node(
            name="node2",
            node_type=EdgeNodeType.GPU_ENABLED,
            location="location2",
            ip_address="192.168.1.2",
            port=8080,
            capabilities=["inference", "training"],
            resources={"cpu_cores": 8, "memory_gb": 16, "gpu_available": True}
        )
        
        # Test requirements
        requirements = {
            "cpu_cores": 4,
            "memory_gb": 8,
            "gpu_required": True,
            "capabilities": ["training"]
        }
        
        best_node = edge_computing.node_manager.find_best_node(requirements)
        assert best_node is not None
        assert best_node.node_id == node2_id  # Should select GPU-enabled node
    
    def test_edge_deployment_manager(self, edge_computing):
        """Test edge deployment manager."""
        # Register a node first
        node_id = edge_computing.node_manager.register_node(
            name="test-node",
            node_type=EdgeNodeType.CPU_ONLY,
            location="test-location",
            ip_address="192.168.1.100",
            port=8080,
            capabilities=["inference"],
            resources={"cpu_cores": 4, "memory_gb": 8}
        )
        
        # Create deployment
        deployment_id = edge_computing.deployment_manager.create_deployment(
            model_id="test-model",
            model_version="1.0.0",
            node_id=node_id,
            configuration={"batch_size": 32}
        )
        
        assert deployment_id is not None
        assert deployment_id in edge_computing.deployment_manager.deployments
        
        deployment = edge_computing.deployment_manager.get_deployment(deployment_id)
        assert deployment.model_id == "test-model"
        assert deployment.node_id == node_id
        assert deployment.status == DeploymentStatus.PENDING
    
    def test_edge_task_manager(self, edge_computing):
        """Test edge task manager."""
        # Register a node first
        node_id = edge_computing.node_manager.register_node(
            name="test-node",
            node_type=EdgeNodeType.CPU_ONLY,
            location="test-location",
            ip_address="192.168.1.100",
            port=8080,
            capabilities=["inference"],
            resources={"cpu_cores": 4, "memory_gb": 8}
        )
        
        # Submit task
        task_id = edge_computing.task_manager.submit_task(
            node_id=node_id,
            task_type="inference",
            payload={"input_data": "test"}
        )
        
        assert task_id is not None
        assert task_id in edge_computing.task_manager.tasks
        
        task = edge_computing.task_manager.get_task(task_id)
        assert task.node_id == node_id
        assert task.task_type == "inference"
        assert task.status == "pending"
    
    def test_edge_monitoring(self, edge_computing):
        """Test edge monitoring."""
        # Register some nodes
        edge_computing.node_manager.register_node(
            name="node1",
            node_type=EdgeNodeType.CPU_ONLY,
            location="location1",
            ip_address="192.168.1.1",
            port=8080,
            capabilities=["inference"],
            resources={"cpu_cores": 4, "memory_gb": 8}
        )
        
        # Get system status
        status = edge_computing.get_system_status()
        
        assert "health" in status
        assert "tasks" in status
        assert "nodes" in status
        assert "deployments" in status
        assert status["nodes"] == 1


class TestFederatedLearning:
    """Test federated learning functionality."""
    
    @pytest.fixture
    def fl_system(self):
        """Create federated learning system for testing."""
        return FederatedLearning()
    
    def test_fl_node_manager_initialization(self, fl_system):
        """Test FL node manager initialization."""
        assert isinstance(fl_system.node_manager, FLNodeManager)
        assert isinstance(fl_system.node_manager.nodes, dict)
    
    def test_register_fl_node(self, fl_system):
        """Test FL node registration."""
        node_id = fl_system.node_manager.register_node(
            name="test-fl-node",
            capabilities=["training", "inference"],
            data_size=1000,
            metadata={"location": "test-location"}
        )
        
        assert node_id is not None
        assert node_id in fl_system.node_manager.nodes
        
        node = fl_system.node_manager.get_node(node_id)
        assert node.name == "test-fl-node"
        assert "training" in node.capabilities
        assert node.data_size == 1000
    
    def test_get_available_nodes(self, fl_system):
        """Test getting available nodes."""
        # Register nodes with different data sizes
        node1_id = fl_system.node_manager.register_node(
            name="node1",
            capabilities=["training"],
            data_size=500
        )
        
        node2_id = fl_system.node_manager.register_node(
            name="node2",
            capabilities=["training"],
            data_size=1500
        )
        
        # Test with minimum data size requirement
        available_nodes = fl_system.node_manager.get_available_nodes(min_data_size=1000)
        assert len(available_nodes) == 1
        assert available_nodes[0].node_id == node2_id
    
    def test_fl_model_manager(self, fl_system):
        """Test FL model manager."""
        # Create model
        model_id = fl_system.model_manager.create_model(
            name="test-model",
            architecture={"layers": 3, "neurons": 100},
            total_rounds=10,
            aggregation_method=AggregationMethod.FEDAVG,
            learning_rate=0.01
        )
        
        assert model_id is not None
        assert model_id in fl_system.model_manager.models
        
        model = fl_system.model_manager.get_model(model_id)
        assert model.name == "test-model"
        assert model.total_rounds == 10
        assert model.aggregation_method == AggregationMethod.FEDAVG
    
    def test_fl_training_manager(self, fl_system):
        """Test FL training manager."""
        # Register nodes
        node1_id = fl_system.node_manager.register_node(
            name="node1",
            capabilities=["training"],
            data_size=1000
        )
        
        node2_id = fl_system.node_manager.register_node(
            name="node2",
            capabilities=["training"],
            data_size=1000
        )
        
        # Create model
        model_id = fl_system.model_manager.create_model(
            name="test-model",
            architecture={"layers": 3},
            total_rounds=5,
            aggregation_method=AggregationMethod.FEDAVG
        )
        
        # Start training
        training_id = fl_system.training_manager.start_training(
            model_id=model_id,
            participating_nodes=[node1_id, node2_id],
            aggregation_method=AggregationMethod.FEDAVG
        )
        
        assert training_id is not None
        assert training_id in fl_system.training_manager.trainings
        
        training = fl_system.training_manager.get_training(training_id)
        assert training.model_id == model_id
        assert len(training.participating_nodes) == 2
        assert training.status == FLTrainingStatus.PENDING
    
    def test_get_system_status(self, fl_system):
        """Test getting system status."""
        # Register some nodes and models
        fl_system.node_manager.register_node(
            name="node1",
            capabilities=["training"],
            data_size=1000
        )
        
        fl_system.model_manager.create_model(
            name="model1",
            architecture={"layers": 3},
            total_rounds=10,
            aggregation_method=AggregationMethod.FEDAVG
        )
        
        status = fl_system.get_system_status()
        
        assert "nodes" in status
        assert "models" in status
        assert "trainings" in status
        assert status["nodes"]["total_nodes"] == 1
        assert status["models"]["total_models"] == 1


class TestIntegration:
    """Integration tests for cloud module."""
    
    def test_cloud_edge_integration(self):
        """Test cloud and edge computing integration."""
        # Create cloud manager
        cloud_manager = CloudManager()
        
        # Create edge computing system
        edge_computing = EdgeComputing()
        
        # Register edge node
        node_id = edge_computing.node_manager.register_node(
            name="edge-node-1",
            node_type=EdgeNodeType.GPU_ENABLED,
            location="edge-location",
            ip_address="192.168.1.100",
            port=8080,
            capabilities=["inference", "training"],
            resources={"cpu_cores": 8, "memory_gb": 16, "gpu_available": True}
        )
        
        # Create deployment on edge node
        deployment_id = edge_computing.deployment_manager.create_deployment(
            model_id="test-model",
            model_version="1.0.0",
            node_id=node_id,
            configuration={"batch_size": 32}
        )
        
        # Verify integration
        assert node_id is not None
        assert deployment_id is not None
        
        # Get system status
        edge_status = edge_computing.get_system_status()
        cloud_summary = cloud_manager.get_cloud_summary()
        
        assert edge_status["nodes"] == 1
        assert edge_status["deployments"] == 1
        assert cloud_summary["total_providers"] == 0  # No cloud providers added yet
    
    def test_federated_learning_integration(self):
        """Test federated learning integration."""
        # Create FL system
        fl_system = FederatedLearning()
        
        # Register multiple nodes
        node1_id = fl_system.node_manager.register_node(
            name="node1",
            capabilities=["training"],
            data_size=1000
        )
        
        node2_id = fl_system.node_manager.register_node(
            name="node2",
            capabilities=["training"],
            data_size=1500
        )
        
        # Create model
        model_id = fl_system.model_manager.create_model(
            name="distributed-model",
            architecture={"layers": 4, "neurons": 128},
            total_rounds=20,
            aggregation_method=AggregationMethod.FEDAVG
        )
        
        # Start training
        training_id = fl_system.training_manager.start_training(
            model_id=model_id,
            participating_nodes=[node1_id, node2_id],
            aggregation_method=AggregationMethod.FEDAVG
        )
        
        # Verify integration
        assert model_id is not None
        assert training_id is not None
        
        # Get system status
        status = fl_system.get_system_status()
        
        assert status["nodes"]["total_nodes"] == 2
        assert status["models"]["total_models"] == 1
        assert status["trainings"]["total_trainings"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
