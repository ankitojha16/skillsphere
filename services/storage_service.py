"""
SkillSphere Provider-Independent Object Storage Framework
Supports multi-instance, stateless application scaling across cloud providers
(AWS S3, Cloudflare R2, MinIO, Supabase Storage) and local filesystem storage.

ARCHITECTURAL PRINCIPLES:
1. Provider Independence: No hard lock-in to AWS/GCP proprietary APIs.
2. Safe Degradation: Defaults cleanly to local storage if cloud credentials are absent.
3. Access Control: Enforces strict user ownership checks before serving private assets.
4. Zero Data Loss: Preserves existing local files without destructive migrations.
"""

import os
import io
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

logger = logging.getLogger('skillsphere.storage')


class StoragePermissionDenied(Exception):
    """Raised when an unauthorized user attempts to access a protected file."""
    pass


class BaseStorageService(ABC):
    """Abstract base class defining uniform object storage semantics."""

    @abstractmethod
    def save_file(
        self,
        path: str,
        content: bytes,
        content_type: str = 'application/octet-stream',
        is_public: bool = False
    ) -> str:
        """Saves content to the given path and returns the resolved storage path or URL."""
        pass

    @abstractmethod
    def get_file(self, path: str) -> Optional[bytes]:
        """Retrieves raw file bytes or returns None if the file does not exist."""
        pass

    @abstractmethod
    def get_file_stream(self, path: str) -> Optional[io.BytesIO]:
        """Returns a binary stream of the stored file, or None."""
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """Deletes the file at the given path. Returns True if deleted or already absent."""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Returns True if the file exists in storage."""
        pass

    @abstractmethod
    def get_url(self, path: str) -> str:
        """Returns a publicly accessible or signed URL for the given path."""
        pass

    def verify_ownership_and_get(
        self,
        path: str,
        user: Any,
        resource_type: str,
        resource_id: Any
    ) -> bytes:
        """
        Enforces user ownership validation prior to retrieving file bytes.
        Prevents unauthorized direct-object reference (IDOR) across instances.
        """
        if not self.check_access_permission(user, resource_type, resource_id):
            logger.warning(
                f"[StorageService] Unauthorized file access attempt: "
                f"user={getattr(user, 'username', 'anonymous')}, "
                f"resource_type={resource_type}, resource_id={resource_id}"
            )
            raise StoragePermissionDenied("You do not have permission to access this resource.")
        
        data = self.get_file(path)
        if data is None:
            raise FileNotFoundError(f"Stored file '{path}' not found.")
        return data

    @staticmethod
    def check_access_permission(user, resource_type: str, resource_id: Any) -> bool:
        """
        Validates whether the given user has permission to view the resource.
        Public resources (e.g. course thumbnails, public certificates) return True.
        """
        if user and getattr(user, 'is_staff', False):
            return True

        if resource_type in ('public_certificate', 'course_thumbnail', 'public_avatar'):
            return True

        if not user or not user.is_authenticated:
            return False

        if resource_type == 'student_avatar':
            from accounts.models import StudentProfile
            return StudentProfile.objects.filter(user=user, id=resource_id).exists()

        elif resource_type == 'resume_export':
            from resumes.models import Resume
            return Resume.objects.filter(user=user, id=resource_id).exists()

        elif resource_type == 'private_certificate':
            from certificates.models import Certificate
            return Certificate.objects.filter(user=user, id=resource_id).exists()

        elif resource_type == 'feedback_screenshot':
            from analytics.models import UserFeedback
            return UserFeedback.objects.filter(user=user, id=resource_id).exists()

        return False


class LocalStorageService(BaseStorageService):
    """
    Local filesystem storage backend using Django's default_storage.
    Safe for local development, single-instance nodes, or mountable volumes.
    Prevents path traversal vulnerabilities.
    """

    def _sanitize_path(self, path: str) -> str:
        cleaned = os.path.normpath(str(path)).lstrip('/')
        if '..' in cleaned.split(os.path.sep):
            raise ValueError(f"Path traversal detected in path '{path}'")
        return cleaned

    def save_file(
        self,
        path: str,
        content: bytes,
        content_type: str = 'application/octet-stream',
        is_public: bool = False
    ) -> str:
        sanitized = self._sanitize_path(path)
        if default_storage.exists(sanitized):
            default_storage.delete(sanitized)
        saved_path = default_storage.save(sanitized, ContentFile(content))
        return saved_path

    def get_file(self, path: str) -> Optional[bytes]:
        sanitized = self._sanitize_path(path)
        if not default_storage.exists(sanitized):
            return None
        with default_storage.open(sanitized, 'rb') as f:
            return f.read()

    def get_file_stream(self, path: str) -> Optional[io.BytesIO]:
        data = self.get_file(path)
        if data is None:
            return None
        return io.BytesIO(data)

    def delete_file(self, path: str) -> bool:
        sanitized = self._sanitize_path(path)
        if default_storage.exists(sanitized):
            default_storage.delete(sanitized)
        return True

    def exists(self, path: str) -> bool:
        sanitized = self._sanitize_path(path)
        return default_storage.exists(sanitized)

    def get_url(self, path: str) -> str:
        sanitized = self._sanitize_path(path)
        return default_storage.url(sanitized)


class S3CompatibleStorageService(BaseStorageService):
    """
    Provider-independent S3-compatible cloud object storage service.
    Works natively with AWS S3, Cloudflare R2, MinIO, and Supabase Storage.
    Gracefully degrades to LocalStorageService if credentials or boto3 are absent.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region_name: Optional[str] = None,
        public_url_base: Optional[str] = None
    ):
        self.bucket_name = bucket_name or os.getenv('STORAGE_BUCKET_NAME', 'skillsphere-media')
        self.endpoint_url = endpoint_url or os.getenv('STORAGE_ENDPOINT_URL')
        self.access_key = access_key or os.getenv('STORAGE_ACCESS_KEY')
        self.secret_key = secret_key or os.getenv('STORAGE_SECRET_KEY')
        self.region_name = region_name or os.getenv('STORAGE_REGION_NAME', 'us-east-1')
        self.public_url_base = public_url_base or os.getenv('STORAGE_PUBLIC_URL_BASE')
        self._s3_client = None
        self._local_fallback = LocalStorageService()

    def _get_client(self):
        if self._s3_client is not None:
            return self._s3_client

        if not (self.access_key and self.secret_key):
            logger.warning("[S3CompatibleStorage] Missing cloud credentials; falling back to local storage.")
            return None

        try:
            import boto3
            from botocore.config import Config
            config = Config(
                retries={'max_attempts': 3, 'mode': 'standard'},
                connect_timeout=3,
                read_timeout=10
            )
            self._s3_client = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                endpoint_url=self.endpoint_url,
                region_name=self.region_name,
                config=config
            )
            return self._s3_client
        except Exception as e:
            logger.warning(f"[S3CompatibleStorage] boto3 initialization failed ({e}); falling back to local.")
            return None

    def save_file(
        self,
        path: str,
        content: bytes,
        content_type: str = 'application/octet-stream',
        is_public: bool = False
    ) -> str:
        client = self._get_client()
        if not client:
            return self._local_fallback.save_file(path, content, content_type, is_public)

        sanitized = path.lstrip('/')
        extra_args = {'ContentType': content_type}
        if is_public:
            extra_args['ACL'] = 'public-read'

        try:
            client.put_object(
                Bucket=self.bucket_name,
                Key=sanitized,
                Body=content,
                **extra_args
            )
            return sanitized
        except Exception as e:
            logger.error(f"[S3CompatibleStorage] Failed to upload {sanitized}: {e}. Storing locally.")
            return self._local_fallback.save_file(path, content, content_type, is_public)

    def get_file(self, path: str) -> Optional[bytes]:
        client = self._get_client()
        if not client:
            return self._local_fallback.get_file(path)

        sanitized = path.lstrip('/')
        try:
            resp = client.get_object(Bucket=self.bucket_name, Key=sanitized)
            return resp['Body'].read()
        except Exception as e:
            logger.warning(f"[S3CompatibleStorage] Failed to get object {sanitized}: {e}")
            return self._local_fallback.get_file(path)

    def get_file_stream(self, path: str) -> Optional[io.BytesIO]:
        data = self.get_file(path)
        if data is None:
            return None
        return io.BytesIO(data)

    def delete_file(self, path: str) -> bool:
        client = self._get_client()
        if not client:
            return self._local_fallback.delete_file(path)

        sanitized = path.lstrip('/')
        try:
            client.delete_object(Bucket=self.bucket_name, Key=sanitized)
            return True
        except Exception as e:
            logger.warning(f"[S3CompatibleStorage] Failed to delete object {sanitized}: {e}")
            return self._local_fallback.delete_file(path)

    def exists(self, path: str) -> bool:
        client = self._get_client()
        if not client:
            return self._local_fallback.exists(path)

        sanitized = path.lstrip('/')
        try:
            client.head_object(Bucket=self.bucket_name, Key=sanitized)
            return True
        except Exception:
            return False

    def get_url(self, path: str) -> str:
        sanitized = path.lstrip('/')
        if self.public_url_base:
            return f"{self.public_url_base.rstrip('/')}/{sanitized}"
        client = self._get_client()
        if client:
            try:
                return client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': sanitized},
                    ExpiresIn=3600
                )
            except Exception:
                pass
        return self._local_fallback.get_url(path)


_STORAGE_INSTANCE: Optional[BaseStorageService] = None

def get_storage_service() -> BaseStorageService:
    """Returns active provider-independent storage service instance."""
    global _STORAGE_INSTANCE
    if _STORAGE_INSTANCE is not None:
        return _STORAGE_INSTANCE

    backend_type = getattr(settings, 'STORAGE_BACKEND', os.getenv('STORAGE_BACKEND', 'local')).lower()
    if backend_type in ('s3', 'r2', 'supabase', 'minio'):
        _STORAGE_INSTANCE = S3CompatibleStorageService()
    else:
        _STORAGE_INSTANCE = LocalStorageService()

    return _STORAGE_INSTANCE


def reset_storage_service():
    """Resets the singleton instance (primarily for unit tests)."""
    global _STORAGE_INSTANCE
    _STORAGE_INSTANCE = None
