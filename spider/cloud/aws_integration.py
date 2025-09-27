"""
AWS Integration

Comprehensive AWS services integration for the SPIDER framework.
Includes S3, EC2, Lambda, SageMaker, and other AWS services.

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
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class AWSRegion(str, Enum):
    """AWS region enumeration."""
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"


@dataclass
class AWSConfig:
    """AWS configuration."""
    access_key_id: str
    secret_access_key: str
    region: AWSRegion = AWSRegion.US_EAST_1
    session_token: Optional[str] = None
    profile_name: Optional[str] = None


@dataclass
class S3Object:
    """S3 object representation."""
    key: str
    bucket: str
    size: int
    last_modified: datetime
    etag: str
    content_type: str
    metadata: Dict[str, str] = None


class S3Storage:
    """AWS S3 storage integration."""
    
    def __init__(self, config: AWSConfig):
        """
        Initialize S3 storage.
        
        Args:
            config: AWS configuration
        """
        self.config = config
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region.value,
            aws_session_token=config.session_token
        )
    
    async def create_bucket(self, bucket_name: str, region: str = None) -> bool:
        """
        Create S3 bucket.
        
        Args:
            bucket_name: Bucket name
            region: AWS region
            
        Returns:
            True if successful
        """
        try:
            region = region or self.config.region.value
            if region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            logger.info(f"Created S3 bucket: {bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            return False
    
    async def upload_file(self, file_path: str, bucket: str, key: str, 
                         metadata: Dict[str, str] = None) -> bool:
        """
        Upload file to S3.
        
        Args:
            file_path: Local file path
            bucket: S3 bucket name
            key: S3 object key
            metadata: Object metadata
            
        Returns:
            True if successful
        """
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.upload_file(file_path, bucket, key, ExtraArgs=extra_args)
            logger.info(f"Uploaded file to S3: s3://{bucket}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return False
    
    async def download_file(self, bucket: str, key: str, file_path: str) -> bool:
        """
        Download file from S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            file_path: Local file path
            
        Returns:
            True if successful
        """
        try:
            self.s3_client.download_file(bucket, key, file_path)
            logger.info(f"Downloaded file from S3: s3://{bucket}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to download file from S3: {e}")
            return False
    
    async def list_objects(self, bucket: str, prefix: str = "") -> List[S3Object]:
        """
        List objects in S3 bucket.
        
        Args:
            bucket: S3 bucket name
            prefix: Object key prefix
            
        Returns:
            List of S3 objects
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            objects = []
            
            for obj in response.get('Contents', []):
                objects.append(S3Object(
                    key=obj['Key'],
                    bucket=bucket,
                    size=obj['Size'],
                    last_modified=obj['LastModified'],
                    etag=obj['ETag'],
                    content_type=obj.get('ContentType', 'binary/octet-stream'),
                    metadata=obj.get('Metadata', {})
                ))
            
            return objects
        except ClientError as e:
            logger.error(f"Failed to list objects in S3: {e}")
            return []
    
    async def delete_object(self, bucket: str, key: str) -> bool:
        """
        Delete object from S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            True if successful
        """
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted object from S3: s3://{bucket}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete object from S3: {e}")
            return False
    
    async def generate_presigned_url(self, bucket: str, key: str, 
                                   expiration: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for S3 object.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL or None
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None


class EC2Compute:
    """AWS EC2 compute integration."""
    
    def __init__(self, config: AWSConfig):
        """
        Initialize EC2 compute.
        
        Args:
            config: AWS configuration
        """
        self.config = config
        self.ec2_client = boto3.client(
            'ec2',
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region.value,
            aws_session_token=config.session_token
        )
    
    async def create_instance(self, image_id: str, instance_type: str,
                            key_name: str, security_group_ids: List[str],
                            user_data: str = None) -> Optional[str]:
        """
        Create EC2 instance.
        
        Args:
            image_id: AMI ID
            instance_type: Instance type
            key_name: Key pair name
            security_group_ids: Security group IDs
            user_data: User data script
            
        Returns:
            Instance ID or None
        """
        try:
            kwargs = {
                'ImageId': image_id,
                'MinCount': 1,
                'MaxCount': 1,
                'InstanceType': instance_type,
                'KeyName': key_name,
                'SecurityGroupIds': security_group_ids
            }
            
            if user_data:
                kwargs['UserData'] = user_data
            
            response = self.ec2_client.run_instances(**kwargs)
            instance_id = response['Instances'][0]['InstanceId']
            
            logger.info(f"Created EC2 instance: {instance_id}")
            return instance_id
        except ClientError as e:
            logger.error(f"Failed to create EC2 instance: {e}")
            return None
    
    async def terminate_instance(self, instance_id: str) -> bool:
        """
        Terminate EC2 instance.
        
        Args:
            instance_id: Instance ID
            
        Returns:
            True if successful
        """
        try:
            self.ec2_client.terminate_instances(InstanceIds=[instance_id])
            logger.info(f"Terminated EC2 instance: {instance_id}")
            return True
        except ClientError as e:
            logger.error(f"Failed to terminate EC2 instance: {e}")
            return False
    
    async def get_instance_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Get instance status.
        
        Args:
            instance_id: Instance ID
            
        Returns:
            Instance status or None
        """
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            instance = response['Reservations'][0]['Instances'][0]
            
            return {
                'instance_id': instance_id,
                'state': instance['State']['Name'],
                'public_ip': instance.get('PublicIpAddress'),
                'private_ip': instance.get('PrivateIpAddress'),
                'instance_type': instance['InstanceType'],
                'launch_time': instance['LaunchTime']
            }
        except ClientError as e:
            logger.error(f"Failed to get instance status: {e}")
            return None


class LambdaFunctions:
    """AWS Lambda functions integration."""
    
    def __init__(self, config: AWSConfig):
        """
        Initialize Lambda functions.
        
        Args:
            config: AWS configuration
        """
        self.config = config
        self.lambda_client = boto3.client(
            'lambda',
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region.value,
            aws_session_token=config.session_token
        )
    
    async def create_function(self, function_name: str, runtime: str,
                            role_arn: str, handler: str, code_zip: bytes,
                            description: str = None) -> bool:
        """
        Create Lambda function.
        
        Args:
            function_name: Function name
            runtime: Runtime (e.g., python3.9)
            role_arn: IAM role ARN
            handler: Handler function
            code_zip: Function code as ZIP bytes
            description: Function description
            
        Returns:
            True if successful
        """
        try:
            kwargs = {
                'FunctionName': function_name,
                'Runtime': runtime,
                'Role': role_arn,
                'Handler': handler,
                'Code': {'ZipFile': code_zip}
            }
            
            if description:
                kwargs['Description'] = description
            
            self.lambda_client.create_function(**kwargs)
            logger.info(f"Created Lambda function: {function_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to create Lambda function: {e}")
            return False
    
    async def invoke_function(self, function_name: str, payload: Dict[str, Any],
                            invocation_type: str = 'RequestResponse') -> Optional[Dict[str, Any]]:
        """
        Invoke Lambda function.
        
        Args:
            function_name: Function name
            payload: Function payload
            invocation_type: Invocation type
            
        Returns:
            Function response or None
        """
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload)
            )
            
            if invocation_type == 'RequestResponse':
                payload = json.loads(response['Payload'].read())
                return payload
            else:
                return {'StatusCode': response['StatusCode']}
        except ClientError as e:
            logger.error(f"Failed to invoke Lambda function: {e}")
            return None
    
    async def update_function_code(self, function_name: str, code_zip: bytes) -> bool:
        """
        Update Lambda function code.
        
        Args:
            function_name: Function name
            code_zip: New function code as ZIP bytes
            
        Returns:
            True if successful
        """
        try:
            self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=code_zip
            )
            logger.info(f"Updated Lambda function code: {function_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to update Lambda function code: {e}")
            return False


class SageMakerML:
    """AWS SageMaker ML integration."""
    
    def __init__(self, config: AWSConfig):
        """
        Initialize SageMaker ML.
        
        Args:
            config: AWS configuration
        """
        self.config = config
        self.sagemaker_client = boto3.client(
            'sagemaker',
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region.value,
            aws_session_token=config.session_token
        )
    
    async def create_training_job(self, job_name: str, role_arn: str,
                                training_image: str, input_data: Dict[str, str],
                                output_data: str, instance_type: str,
                                instance_count: int = 1) -> bool:
        """
        Create SageMaker training job.
        
        Args:
            job_name: Training job name
            role_arn: IAM role ARN
            training_image: Training container image
            input_data: Input data configuration
            output_data: Output data S3 path
            instance_type: Instance type
            instance_count: Number of instances
            
        Returns:
            True if successful
        """
        try:
            training_job_config = {
                'TrainingJobName': job_name,
                'RoleArn': role_arn,
                'AlgorithmSpecification': {
                    'TrainingImage': training_image,
                    'TrainingInputMode': 'File'
                },
                'InputDataConfig': [
                    {
                        'ChannelName': 'training',
                        'DataSource': {
                            'S3DataSource': {
                                'S3DataType': 'S3Prefix',
                                'S3Uri': input_data['training'],
                                'S3DataDistributionType': 'FullyReplicated'
                            }
                        }
                    }
                ],
                'OutputDataConfig': {
                    'S3OutputPath': output_data
                },
                'ResourceConfig': {
                    'InstanceType': instance_type,
                    'InstanceCount': instance_count,
                    'VolumeSizeInGB': 30
                },
                'StoppingCondition': {
                    'MaxRuntimeInSeconds': 3600
                }
            }
            
            self.sagemaker_client.create_training_job(**training_job_config)
            logger.info(f"Created SageMaker training job: {job_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to create SageMaker training job: {e}")
            return False
    
    async def create_model(self, model_name: str, model_data: str,
                          image: str, role_arn: str) -> bool:
        """
        Create SageMaker model.
        
        Args:
            model_name: Model name
            model_data: Model data S3 path
            image: Model container image
            role_arn: IAM role ARN
            
        Returns:
            True if successful
        """
        try:
            model_config = {
                'ModelName': model_name,
                'PrimaryContainer': {
                    'Image': image,
                    'ModelDataUrl': model_data
                },
                'ExecutionRoleArn': role_arn
            }
            
            self.sagemaker_client.create_model(**model_config)
            logger.info(f"Created SageMaker model: {model_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to create SageMaker model: {e}")
            return False
    
    async def create_endpoint(self, endpoint_name: str, model_name: str,
                            instance_type: str, instance_count: int = 1) -> bool:
        """
        Create SageMaker endpoint.
        
        Args:
            endpoint_name: Endpoint name
            model_name: Model name
            instance_type: Instance type
            instance_count: Number of instances
            
        Returns:
            True if successful
        """
        try:
            endpoint_config_name = f"{endpoint_name}-config"
            
            # Create endpoint configuration
            endpoint_config = {
                'EndpointConfigName': endpoint_config_name,
                'ProductionVariants': [
                    {
                        'VariantName': 'primary',
                        'ModelName': model_name,
                        'InitialInstanceCount': instance_count,
                        'InstanceType': instance_type
                    }
                ]
            }
            
            self.sagemaker_client.create_endpoint_config(**endpoint_config)
            
            # Create endpoint
            endpoint_config = {
                'EndpointName': endpoint_name,
                'EndpointConfigName': endpoint_config_name
            }
            
            self.sagemaker_client.create_endpoint(**endpoint_config)
            logger.info(f"Created SageMaker endpoint: {endpoint_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to create SageMaker endpoint: {e}")
            return False


class AWSIntegration:
    """Main AWS integration class."""
    
    def __init__(self, config: AWSConfig):
        """
        Initialize AWS integration.
        
        Args:
            config: AWS configuration
        """
        self.config = config
        self.s3 = S3Storage(config)
        self.ec2 = EC2Compute(config)
        self.lambda_functions = LambdaFunctions(config)
        self.sagemaker = SageMakerML(config)
    
    async def test_connection(self) -> bool:
        """
        Test AWS connection.
        
        Returns:
            True if connection successful
        """
        try:
            # Test S3 connection
            self.s3_client.list_buckets()
            logger.info("AWS connection test successful")
            return True
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return False
        except ClientError as e:
            logger.error(f"AWS connection test failed: {e}")
            return False
    
    def get_available_services(self) -> List[str]:
        """Get list of available AWS services."""
        return [
            "s3", "ec2", "lambda", "sagemaker", "rds", "dynamodb",
            "cloudwatch", "iam", "sns", "sqs", "api_gateway"
        ]
    
    def get_service_status(self, service: str) -> Dict[str, Any]:
        """
        Get service status.
        
        Args:
            service: Service name
            
        Returns:
            Service status information
        """
        try:
            if service == "s3":
                response = self.s3.s3_client.list_buckets()
                return {
                    "service": "s3",
                    "status": "available",
                    "bucket_count": len(response['Buckets'])
                }
            elif service == "ec2":
                response = self.ec2.ec2_client.describe_instances()
                return {
                    "service": "ec2",
                    "status": "available",
                    "instance_count": len(response['Reservations'])
                }
            else:
                return {
                    "service": service,
                    "status": "unknown",
                    "message": "Service not implemented"
                }
        except ClientError as e:
            return {
                "service": service,
                "status": "error",
                "error": str(e)
            }
