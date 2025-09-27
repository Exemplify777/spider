"""Storage handlers for SPIDER framework."""

import json
import csv
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import asyncio

from ..core.exceptions import StorageError
from ..core.logger import get_logger


class BaseStorage(ABC):
    """Base class for all storage handlers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize storage handler.
        
        Args:
            config: Storage-specific configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    async def save(self, data: List[Dict[str, Any]], path: str) -> None:
        """Save data to storage.
        
        Args:
            data: Data to save
            path: Storage path
        """
        pass
    
    @abstractmethod
    async def load(self, path: str) -> List[Dict[str, Any]]:
        """Load data from storage.
        
        Args:
            path: Storage path
            
        Returns:
            Loaded data
        """
        pass
    
    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if path exists.
        
        Args:
            path: Path to check
            
        Returns:
            True if path exists
        """
        pass


class FileStorage(BaseStorage):
    """File-based storage handler."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize file storage.
        
        Args:
            config: File storage configuration
        """
        super().__init__(config)
        self.data_dir = Path(config.get('data_dir', 'data'))
        self.format = config.get('format', 'json')
        self.encoding = config.get('encoding', 'utf-8')
        
        # Create data directory
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def save(self, data: List[Dict[str, Any]], path: str) -> None:
        """Save data to file.
        
        Args:
            data: Data to save
            path: File path
        """
        try:
            file_path = self.data_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.format == 'json':
                await self._save_json(data, file_path)
            elif self.format == 'csv':
                await self._save_csv(data, file_path)
            elif self.format == 'txt':
                await self._save_txt(data, file_path)
            else:
                raise StorageError(f"Unsupported format: {self.format}")
            
            self.logger.info(f"Data saved to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save data to {path}: {e}")
            raise StorageError(f"File save failed: {e}")
    
    async def load(self, path: str) -> List[Dict[str, Any]]:
        """Load data from file.
        
        Args:
            path: File path
            
        Returns:
            Loaded data
        """
        try:
            file_path = self.data_dir / path
            
            if not file_path.exists():
                raise StorageError(f"File not found: {file_path}")
            
            if self.format == 'json':
                return await self._load_json(file_path)
            elif self.format == 'csv':
                return await self._load_csv(file_path)
            elif self.format == 'txt':
                return await self._load_txt(file_path)
            else:
                raise StorageError(f"Unsupported format: {self.format}")
                
        except Exception as e:
            self.logger.error(f"Failed to load data from {path}: {e}")
            raise StorageError(f"File load failed: {e}")
    
    async def exists(self, path: str) -> bool:
        """Check if file exists.
        
        Args:
            path: File path
            
        Returns:
            True if file exists
        """
        file_path = self.data_dir / path
        return file_path.exists()
    
    async def _save_json(self, data: List[Dict[str, Any]], file_path: Path) -> None:
        """Save data as JSON."""
        def _write():
            with open(file_path, 'w', encoding=self.encoding) as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        await asyncio.get_event_loop().run_in_executor(None, _write)
    
    async def _save_csv(self, data: List[Dict[str, Any]], file_path: Path) -> None:
        """Save data as CSV."""
        def _write():
            if not data:
                return
            
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            
            with open(file_path, 'w', newline='', encoding=self.encoding) as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                writer.writerows(data)
        
        await asyncio.get_event_loop().run_in_executor(None, _write)
    
    async def _save_txt(self, data: List[Dict[str, Any]], file_path: Path) -> None:
        """Save data as text."""
        def _write():
            with open(file_path, 'w', encoding=self.encoding) as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        await asyncio.get_event_loop().run_in_executor(None, _write)
    
    async def _load_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load data from JSON."""
        def _read():
            with open(file_path, 'r', encoding=self.encoding) as f:
                return json.load(f)
        
        return await asyncio.get_event_loop().run_in_executor(None, _read)
    
    async def _load_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load data from CSV."""
        def _read():
            with open(file_path, 'r', encoding=self.encoding) as f:
                reader = csv.DictReader(f)
                return list(reader)
        
        return await asyncio.get_event_loop().run_in_executor(None, _read)
    
    async def _load_txt(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load data from text."""
        def _read():
            data = []
            with open(file_path, 'r', encoding=self.encoding) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data.append(json.loads(line))
            return data
        
        return await asyncio.get_event_loop().run_in_executor(None, _read)


class DatabaseStorage(BaseStorage):
    """Database storage handler."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize database storage.
        
        Args:
            config: Database configuration
        """
        super().__init__(config)
        self.db_url = config.get('url', 'sqlite:///spider.db')
        self.table_name = config.get('table_name', 'scraping_results')
        self._connection = None
    
    async def save(self, data: List[Dict[str, Any]], path: str) -> None:
        """Save data to database.
        
        Args:
            data: Data to save
            path: Table name (overrides config)
        """
        try:
            table_name = path or self.table_name
            
            if not data:
                return
            
            # Get connection
            conn = await self._get_connection()
            
            # Create table if not exists
            await self._create_table(conn, table_name)
            
            # Insert data
            await self._insert_data(conn, table_name, data)
            
            self.logger.info(f"Data saved to database table {table_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to save data to database: {e}")
            raise StorageError(f"Database save failed: {e}")
    
    async def load(self, path: str) -> List[Dict[str, Any]]:
        """Load data from database.
        
        Args:
            path: Table name
            
        Returns:
            Loaded data
        """
        try:
            table_name = path or self.table_name
            conn = await self._get_connection()
            
            # Query data
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Fetch data
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in rows]
            
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to load data from database: {e}")
            raise StorageError(f"Database load failed: {e}")
    
    async def exists(self, path: str) -> bool:
        """Check if table exists.
        
        Args:
            path: Table name
            
        Returns:
            True if table exists
        """
        try:
            table_name = path or self.table_name
            conn = await self._get_connection()
            
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            
            return cursor.fetchone() is not None
            
        except Exception as e:
            self.logger.error(f"Failed to check table existence: {e}")
            return False
    
    async def _get_connection(self):
        """Get database connection."""
        if self._connection is None:
            if self.db_url.startswith('sqlite'):
                db_path = self.db_url.replace('sqlite:///', '')
                self._connection = sqlite3.connect(db_path)
            else:
                # For other databases, you'd use appropriate drivers
                raise StorageError(f"Unsupported database URL: {self.db_url}")
        
        return self._connection
    
    async def _create_table(self, conn, table_name: str) -> None:
        """Create table if not exists."""
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                status_code INTEGER,
                success BOOLEAN,
                content_length INTEGER,
                extracted_data TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    
    async def _insert_data(self, conn, table_name: str, data: List[Dict[str, Any]]) -> None:
        """Insert data into table."""
        cursor = conn.cursor()
        
        for item in data:
            cursor.execute(f"""
                INSERT INTO {table_name} 
                (url, status_code, success, content_length, extracted_data, error)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item.get('url', ''),
                item.get('status_code', 0),
                item.get('success', False),
                item.get('content_length', 0),
                json.dumps(item.get('extracted_data', {})),
                item.get('error', '')
            ))
        
        conn.commit()


class CloudStorage(BaseStorage):
    """Cloud storage handler (AWS S3, Google Cloud, etc.)."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize cloud storage.
        
        Args:
            config: Cloud storage configuration
        """
        super().__init__(config)
        self.provider = config.get('provider', 's3')
        self.bucket = config.get('bucket')
        self.region = config.get('region', 'us-east-1')
        self.access_key = config.get('access_key')
        self.secret_key = config.get('secret_key')
    
    async def save(self, data: List[Dict[str, Any]], path: str) -> None:
        """Save data to cloud storage.
        
        Args:
            data: Data to save
            path: Cloud storage path
        """
        try:
            if self.provider == 's3':
                await self._save_to_s3(data, path)
            else:
                raise StorageError(f"Unsupported cloud provider: {self.provider}")
            
            self.logger.info(f"Data saved to cloud storage: {path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save data to cloud storage: {e}")
            raise StorageError(f"Cloud storage save failed: {e}")
    
    async def load(self, path: str) -> List[Dict[str, Any]]:
        """Load data from cloud storage.
        
        Args:
            path: Cloud storage path
            
        Returns:
            Loaded data
        """
        try:
            if self.provider == 's3':
                return await self._load_from_s3(path)
            else:
                raise StorageError(f"Unsupported cloud provider: {self.provider}")
                
        except Exception as e:
            self.logger.error(f"Failed to load data from cloud storage: {e}")
            raise StorageError(f"Cloud storage load failed: {e}")
    
    async def exists(self, path: str) -> bool:
        """Check if path exists in cloud storage.
        
        Args:
            path: Cloud storage path
            
        Returns:
            True if path exists
        """
        try:
            if self.provider == 's3':
                return await self._exists_in_s3(path)
            else:
                raise StorageError(f"Unsupported cloud provider: {self.provider}")
                
        except Exception as e:
            self.logger.error(f"Failed to check cloud storage path: {e}")
            return False
    
    async def _save_to_s3(self, data: List[Dict[str, Any]], path: str) -> None:
        """Save data to AWS S3."""
        import boto3
        from botocore.exceptions import ClientError
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        
        # Convert data to JSON
        json_data = json.dumps(data, indent=2)
        
        # Upload to S3
        s3_client.put_object(
            Bucket=self.bucket,
            Key=path,
            Body=json_data,
            ContentType='application/json'
        )
    
    async def _load_from_s3(self, path: str) -> List[Dict[str, Any]]:
        """Load data from AWS S3."""
        import boto3
        from botocore.exceptions import ClientError
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        
        # Download from S3
        response = s3_client.get_object(Bucket=self.bucket, Key=path)
        json_data = response['Body'].read().decode('utf-8')
        
        return json.loads(json_data)
    
    async def _exists_in_s3(self, path: str) -> bool:
        """Check if path exists in AWS S3."""
        import boto3
        from botocore.exceptions import ClientError
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        
        try:
            s3_client.head_object(Bucket=self.bucket, Key=path)
            return True
        except ClientError:
            return False
