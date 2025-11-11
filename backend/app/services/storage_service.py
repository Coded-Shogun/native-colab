"""
File Storage Service
Handles file upload/download with MinIO/S3 backend
"""

import logging
import os
import uuid
from typing import BinaryIO, Optional, Tuple
from datetime import datetime
import aiofiles
import aioboto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for file storage operations using S3-compatible storage"""

    def __init__(self):
        """Initialize S3 client configuration"""
        self.session = aioboto3.Session()
        self.endpoint_url = settings.S3_ENDPOINT
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.bucket_name = settings.S3_BUCKET
        self.region = settings.S3_REGION
        self.use_ssl = settings.S3_USE_SSL

    async def _get_client(self):
        """Get async S3 client"""
        return self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            use_ssl=self.use_ssl
        )

    async def ensure_bucket_exists(self) -> bool:
        """
        Ensure the S3 bucket exists, create if it doesn't.

        Returns:
            bool: True if bucket exists or was created successfully
        """
        try:
            async with await self._get_client() as s3:
                try:
                    await s3.head_bucket(Bucket=self.bucket_name)
                    logger.info(f"Bucket {self.bucket_name} exists")
                    return True
                except ClientError as e:
                    if e.response['Error']['Code'] == '404':
                        # Bucket doesn't exist, create it
                        await s3.create_bucket(Bucket=self.bucket_name)
                        logger.info(f"Bucket {self.bucket_name} created")
                        return True
                    else:
                        logger.error(f"Error checking bucket: {e}")
                        return False
        except Exception as e:
            logger.error(f"Failed to ensure bucket exists: {e}", exc_info=True)
            return False

    def generate_storage_path(
        self,
        workspace_id: int,
        filename: str,
        folder: str = "documents"
    ) -> str:
        """
        Generate a unique storage path for a file.

        Args:
            workspace_id: Workspace ID
            filename: Original filename
            folder: Folder type (documents, avatars, etc.)

        Returns:
            str: Storage path (e.g., "documents/workspace_1/2025/11/uuid_filename.pdf")
        """
        # Get file extension
        _, ext = os.path.splitext(filename)

        # Generate unique ID
        unique_id = uuid.uuid4().hex[:8]

        # Create path structure: folder/workspace_X/YYYY/MM/uuid_filename.ext
        now = datetime.utcnow()
        path = f"{folder}/workspace_{workspace_id}/{now.year}/{now.month:02d}/{unique_id}_{filename}"

        return path

    async def upload_file(
        self,
        file_data: bytes,
        storage_path: str,
        content_type: str = "application/octet-stream"
    ) -> bool:
        """
        Upload a file to S3 storage.

        Args:
            file_data: File content as bytes
            storage_path: Path where file will be stored
            content_type: MIME type of the file

        Returns:
            bool: True if upload successful
        """
        try:
            async with await self._get_client() as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=storage_path,
                    Body=file_data,
                    ContentType=content_type
                )
                logger.info(f"File uploaded successfully to {storage_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to upload file to {storage_path}: {e}", exc_info=True)
            return False

    async def download_file(self, storage_path: str) -> Optional[bytes]:
        """
        Download a file from S3 storage.

        Args:
            storage_path: Path to the file in storage

        Returns:
            Optional[bytes]: File content or None if error
        """
        try:
            async with await self._get_client() as s3:
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=storage_path
                )
                async with response['Body'] as stream:
                    file_data = await stream.read()
                logger.info(f"File downloaded successfully from {storage_path}")
                return file_data
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"File not found: {storage_path}")
            else:
                logger.error(f"Failed to download file from {storage_path}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Failed to download file from {storage_path}: {e}", exc_info=True)
            return None

    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete a file from S3 storage.

        Args:
            storage_path: Path to the file in storage

        Returns:
            bool: True if deletion successful
        """
        try:
            async with await self._get_client() as s3:
                await s3.delete_object(
                    Bucket=self.bucket_name,
                    Key=storage_path
                )
                logger.info(f"File deleted successfully from {storage_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete file from {storage_path}: {e}", exc_info=True)
            return False

    async def file_exists(self, storage_path: str) -> bool:
        """
        Check if a file exists in S3 storage.

        Args:
            storage_path: Path to the file in storage

        Returns:
            bool: True if file exists
        """
        try:
            async with await self._get_client() as s3:
                await s3.head_object(
                    Bucket=self.bucket_name,
                    Key=storage_path
                )
                return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking if file exists: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Error checking if file exists: {e}", exc_info=True)
            return False

    async def get_file_size(self, storage_path: str) -> Optional[int]:
        """
        Get the size of a file in S3 storage.

        Args:
            storage_path: Path to the file in storage

        Returns:
            Optional[int]: File size in bytes or None if error
        """
        try:
            async with await self._get_client() as s3:
                response = await s3.head_object(
                    Bucket=self.bucket_name,
                    Key=storage_path
                )
                return response['ContentLength']
        except Exception as e:
            logger.error(f"Failed to get file size for {storage_path}: {e}", exc_info=True)
            return None

    async def copy_file(self, source_path: str, destination_path: str) -> bool:
        """
        Copy a file within S3 storage (useful for versioning).

        Args:
            source_path: Source file path
            destination_path: Destination file path

        Returns:
            bool: True if copy successful
        """
        try:
            async with await self._get_client() as s3:
                copy_source = {'Bucket': self.bucket_name, 'Key': source_path}
                await s3.copy_object(
                    CopySource=copy_source,
                    Bucket=self.bucket_name,
                    Key=destination_path
                )
                logger.info(f"File copied from {source_path} to {destination_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to copy file: {e}", exc_info=True)
            return False

    async def generate_presigned_url(
        self,
        storage_path: str,
        expiration: int = 3600,
        download_filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a presigned URL for temporary file access.

        Args:
            storage_path: Path to the file in storage
            expiration: URL expiration time in seconds (default: 1 hour)
            download_filename: Optional filename for Content-Disposition header

        Returns:
            Optional[str]: Presigned URL or None if error
        """
        try:
            async with await self._get_client() as s3:
                params = {
                    'Bucket': self.bucket_name,
                    'Key': storage_path,
                }

                if download_filename:
                    params['ResponseContentDisposition'] = f'attachment; filename="{download_filename}"'

                url = await s3.generate_presigned_url(
                    'get_object',
                    Params=params,
                    ExpiresIn=expiration
                )
                logger.info(f"Presigned URL generated for {storage_path}")
                return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}", exc_info=True)
            return None

    def validate_file_type(self, filename: str) -> bool:
        """
        Validate file type based on extension.

        Args:
            filename: Filename to validate

        Returns:
            bool: True if file type is allowed
        """
        _, ext = os.path.splitext(filename)
        ext = ext.lower().lstrip('.')
        return ext in settings.allowed_file_types_list

    def validate_file_size(self, file_size: int) -> bool:
        """
        Validate file size.

        Args:
            file_size: File size in bytes

        Returns:
            bool: True if file size is within limits
        """
        return file_size <= settings.MAX_UPLOAD_SIZE

    def get_file_type_from_extension(self, filename: str) -> str:
        """
        Get file type from extension.

        Args:
            filename: Filename

        Returns:
            str: File type (e.g., "pdf", "docx")
        """
        _, ext = os.path.splitext(filename)
        return ext.lower().lstrip('.')


# Export singleton instance
storage_service = StorageService()
