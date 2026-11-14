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
    def save_file_stream(
        self,
        path: str,
        stream: io.IOBase,
        content_type: str = 'application/octet-stream',
        is_public: bool = False,
        content_length: Optional[int] = None
    ) -> str:
        """Streams content to the given path and returns the resolved storage path or URL."""
        pass

    @abstractmethod
    def get_file(self, path: str) -> Optional[bytes]:
        """Retrieves raw file bytes or returns None if the file does not exist."""
        pass

    @abstractmethod
    def get_file_stream(self, path: str) -> Optional[Any]:
        """Returns a binary stream of the stored file, or None."""
        pass

    def get_file_chunks(self, path: str, chunk_size: int = 65536):
        """Yields file content in chunks for memory-efficient streaming of large assets."""
        stream = self.get_file_stream(path)
        if stream is None:
            return
        try:
            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            if hasattr(stream, 'close'):
                try:
                    stream.close()
                except Exception:
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
        """Returns a publicly accessible or default URL for the given path."""
        pass

    def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """Returns a time-limited signed URL for private asset access."""
        return self.get_url(path)

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

    def verify_ownership_and_get_signed_url(
        self,
        path: str,
        user: Any,
        resource_type: str,
        resource_id: Any,
        expires_in: int = 3600
    ) -> str:
        """
        Enforces user ownership validation prior to issuing a secure pre-signed download URL.
        Allows offloading large file transfers directly to object storage without Django memory consumption.
        """
        if not self.check_access_permission(user, resource_type, resource_id):
            logger.warning(
                f"[StorageService] Unauthorized signed URL request: "
                f"user={getattr(user, 'username', 'anonymous')}, "
                f"resource_type={resource_type}, resource_id={resource_id}"
            )
            raise StoragePermissionDenied("You do not have permission to access this resource.")
        return self.get_signed_url(path, expires_in=expires_in)

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

    def save_file_stream(
        self,
        path: str,
        stream: io.IOBase,
        content_type: str = 'application/octet-stream',
        is_public: bool = False,
        content_length: Optional[int] = None
    ) -> str:
        sanitized = self._sanitize_path(path)
        if default_storage.exists(sanitized):
            default_storage.delete(sanitized)
        from django.core.files import File
        saved_path = default_storage.save(sanitized, File(stream))
        return saved_path

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
    Supports streaming upload/download, presigned download URLs, and path-style addressing.
    Gracefully degrades to LocalStorageService in development if credentials or boto3 are absent.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region_name: Optional[str] = None,
        public_url_base: Optional[str] = None,
        addressing_style: Optional[str] = None
    ):
        self.bucket_name = bucket_name or os.getenv('STORAGE_BUCKET_NAME', 'skillsphere-media')
        self.endpoint_url = endpoint_url or os.getenv('STORAGE_ENDPOINT_URL')
        self.access_key = access_key or os.getenv('STORAGE_ACCESS_KEY')
        self.secret_key = secret_key or os.getenv('STORAGE_SECRET_KEY')
        self.region_name = region_name or os.getenv('STORAGE_REGION_NAME', 'us-east-1')
        self.public_url_base = public_url_base or os.getenv('STORAGE_PUBLIC_URL_BASE')
        self.addressing_style = addressing_style or os.getenv('STORAGE_S3_ADDRESSING_STYLE')
        if not self.addressing_style and self.endpoint_url:
            self.addressing_style = 'path'
        self._s3_client = None
        self._local_fallback = LocalStorageService()

    @property
    def is_production(self) -> bool:
        return not getattr(settings, 'DEBUG', True) or os.getenv('ENVIRONMENT') == 'production'

    def _get_client(self):
        if self._s3_client is not None:
            return self._s3_client

        if not (self.access_key and self.secret_key):
            msg = (
                f"[S3CompatibleStorage] Missing cloud credentials (STORAGE_ACCESS_KEY / STORAGE_SECRET_KEY). "
                f"Bucket: '{self.bucket_name}'."
            )
            if self.is_production:
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured(f"Production storage configuration error: {msg} Ephemeral local fallback is disallowed in production.")
            logger.warning(f"{msg} Falling back to local storage in development.")
            return None

        try:
            import boto3
            from botocore.config import Config
            s3_config_args = {
                'retries': {'max_attempts': 3, 'mode': 'standard'},
                'connect_timeout': 3,
                'read_timeout': 10
            }
            if self.addressing_style:
                s3_config_args['s3'] = {'addressing_style': self.addressing_style}
            config = Config(**s3_config_args)
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
            if self.is_production:
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured(f"[S3CompatibleStorage] boto3 client initialization failed in production: {e}")
            logger.warning(f"[S3CompatibleStorage] boto3 initialization failed ({e}); falling back to local.")
            return None

    def save_file_stream(
        self,
        path: str,
        stream: io.IOBase,
        content_type: str = 'application/octet-stream',
        is_public: bool = False,
        content_length: Optional[int] = None
    ) -> str:
        client = self._get_client()
        if not client:
            return self._local_fallback.save_file_stream(path, stream, content_type, is_public, content_length)

        sanitized = path.lstrip('/')
        extra_args = {'ContentType': content_type}
        if is_public:
            extra_args['ACL'] = 'public-read'

        try:
            client.upload_fileobj(
                Fileobj=stream,
                Bucket=self.bucket_name,
                Key=sanitized,
                ExtraArgs=extra_args
            )
            return sanitized
        except Exception as e:
            logger.error(f"[S3CompatibleStorage] Failed to stream upload {sanitized}: {e}.")
            if self.is_production:
                raise IOError(f"Cloud storage stream upload to {sanitized} failed: {e}")
            return self._local_fallback.save_file_stream(path, stream, content_type, is_public, content_length)

    def save_file(
        self,
        path: str,
        content: bytes,
        content_type: str = 'application/octet-stream',
        is_public: bool = False
    ) -> str:
        return self.save_file_stream(
            path=path,
            stream=io.BytesIO(content),
            content_type=content_type,
            is_public=is_public,
            content_length=len(content)
        )

    def get_file_stream(self, path: str) -> Optional[Any]:
        client = self._get_client()
        if not client:
            return self._local_fallback.get_file_stream(path)

        sanitized = path.lstrip('/')
        try:
            resp = client.get_object(Bucket=self.bucket_name, Key=sanitized)
            return resp['Body']
        except Exception as e:
            logger.warning(f"[S3CompatibleStorage] Failed to get object {sanitized}: {e}")
            return self._local_fallback.get_file_stream(path)

    def get_file(self, path: str) -> Optional[bytes]:
        stream = self.get_file_stream(path)
        if stream is None:
            return None
        try:
            return stream.read()
        finally:
            if hasattr(stream, 'close'):
                try:
                    stream.close()
                except Exception:
                    pass

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

    def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        sanitized = path.lstrip('/')
        client = self._get_client()
        if client:
            try:
                return client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': sanitized},
                    ExpiresIn=expires_in
                )
            except Exception as e:
                logger.error(f"[S3CompatibleStorage] Presigned URL generation failed: {e}")
                if self.is_production:
                    raise IOError(f"Failed to generate secure signed URL for {sanitized}: {e}")
        return self._local_fallback.get_url(path)


def validate_storage_configuration() -> bool:
    """
    Validates storage configuration against the active runtime environment.
    In production (DEBUG=False or ENVIRONMENT=production), if STORAGE_BACKEND is cloud (s3/r2/minio/supabase)
    and credentials are missing, raises ImproperlyConfigured to prevent silent ephemeral data loss.
    """
    is_prod = not getattr(settings, 'DEBUG', True) or os.getenv('ENVIRONMENT') == 'production'
    backend_type = (os.getenv('STORAGE_BACKEND') or getattr(settings, 'STORAGE_BACKEND', 'local')).lower()

    if backend_type in ('s3', 'r2', 'supabase', 'minio'):
        access_key = os.getenv('STORAGE_ACCESS_KEY') or getattr(settings, 'STORAGE_ACCESS_KEY', None)
        secret_key = os.getenv('STORAGE_SECRET_KEY') or getattr(settings, 'STORAGE_SECRET_KEY', None)
        bucket_name = os.getenv('STORAGE_BUCKET_NAME') or getattr(settings, 'STORAGE_BUCKET_NAME', None)
        if not (access_key and secret_key and bucket_name):
            msg = (
                f"Production storage configuration error: STORAGE_BACKEND='{backend_type}' "
                f"requires STORAGE_ACCESS_KEY, STORAGE_SECRET_KEY, and STORAGE_BUCKET_NAME to be set. "
                f"Silent fallback to local ephemeral storage is disabled in production to protect student data."
            )
            if is_prod:
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured(msg)
            logger.warning(f"{msg} Using local fallback for development only.")
            return False
    elif backend_type == 'local' and is_prod:
        allow_local = os.getenv('ALLOW_LOCAL_STORAGE_IN_PRODUCTION', 'False').lower() in ('true', '1')
        if not allow_local:
            logger.warning(
                "[StorageService] Running LocalStorageService in production without ALLOW_LOCAL_STORAGE_IN_PRODUCTION=True. "
                "Uploaded files will NOT be shared across independent container instances unless MEDIA_ROOT is on a shared volume."
            )
    return True


_STORAGE_INSTANCE: Optional[BaseStorageService] = None

def get_storage_service() -> BaseStorageService:
    """Returns active provider-independent storage service instance after configuration validation."""
    global _STORAGE_INSTANCE
    if _STORAGE_INSTANCE is not None:
        return _STORAGE_INSTANCE

    validate_storage_configuration()

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
