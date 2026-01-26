# utils.py
"""
Utility functions for the AFCARE platform.
Includes S3 file upload, hashing, and other helpers.
"""
import hashlib
import logging
from typing import Optional

from fastapi import UploadFile, HTTPException

from backend.config import settings

logger = logging.getLogger(__name__)

# Initialize S3 client lazily
_s3_client = None


def _get_s3_client():
    """Get or create S3 client with lazy initialization."""
    global _s3_client
    if _s3_client is None:
        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            raise HTTPException(
                status_code=503,
                detail="S3 storage not configured"
            )
        try:
            import boto3
            _s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.s3_region,
            )
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="S3 client library not available"
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise HTTPException(
                status_code=503,
                detail="Failed to initialize storage service"
            )
    return _s3_client


async def upload_to_s3(
    file: UploadFile,
    key: str,
    content_type: Optional[str] = None
) -> str:
    """
    Upload a file to S3.

    Args:
        file: FastAPI UploadFile object
        key: S3 object key (path/filename)
        content_type: Optional content type override

    Returns:
        URL of the uploaded file

    Raises:
        HTTPException: If upload fails
    """
    if not settings.s3_bucket_name:
        raise HTTPException(
            status_code=503,
            detail="S3 bucket not configured"
        )

    s3_client = _get_s3_client()

    try:
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        elif file.content_type:
            extra_args['ContentType'] = file.content_type

        s3_client.upload_fileobj(
            file.file,
            settings.s3_bucket_name,
            key,
            ExtraArgs=extra_args if extra_args else None
        )

        url = get_s3_url(key)
        logger.info(f"Uploaded file to S3: {key}")
        return url

    except Exception as e:
        logger.error(f"S3 upload failed for {key}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to upload file to storage"
        )


def get_s3_url(key: str) -> str:
    """
    Get the public URL for an S3 object.

    Args:
        key: S3 object key

    Returns:
        Public URL for the object
    """
    if not settings.s3_bucket_name:
        raise ValueError("S3 bucket not configured")

    region = settings.s3_region or "us-east-1"
    if region == "us-east-1":
        return f"https://{settings.s3_bucket_name}.s3.amazonaws.com/{key}"
    return f"https://{settings.s3_bucket_name}.s3.{region}.amazonaws.com/{key}"


def generate_presigned_url(
    key: str,
    expiration: int = 3600,
    http_method: str = "GET"
) -> str:
    """
    Generate a presigned URL for S3 object access.

    Args:
        key: S3 object key
        expiration: URL expiration time in seconds (default 1 hour)
        http_method: HTTP method (GET for download, PUT for upload)

    Returns:
        Presigned URL string

    Raises:
        HTTPException: If URL generation fails
    """
    if not settings.s3_bucket_name:
        raise HTTPException(
            status_code=503,
            detail="S3 bucket not configured"
        )

    s3_client = _get_s3_client()

    try:
        if http_method == "PUT":
            url = s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': settings.s3_bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
        else:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.s3_bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
        return url
    except Exception as e:
        logger.error(f"Failed to generate presigned URL for {key}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate file access URL"
        )


def delete_from_s3(key: str) -> bool:
    """
    Delete a file from S3.

    Args:
        key: S3 object key

    Returns:
        True if deletion successful

    Raises:
        HTTPException: If deletion fails
    """
    if not settings.s3_bucket_name:
        raise HTTPException(
            status_code=503,
            detail="S3 bucket not configured"
        )

    s3_client = _get_s3_client()

    try:
        s3_client.delete_object(
            Bucket=settings.s3_bucket_name,
            Key=key
        )
        logger.info(f"Deleted file from S3: {key}")
        return True
    except Exception as e:
        logger.error(f"S3 delete failed for {key}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete file from storage"
        )


# -------- Hashing Utilities --------

def generate_hash(data: str, algorithm: str = "sha256") -> str:
    """
    Generate a hash of the given data.

    Args:
        data: String data to hash
        algorithm: Hash algorithm (sha256, sha512, md5)

    Returns:
        Hexadecimal hash string
    """
    if algorithm == "sha256":
        return hashlib.sha256(data.encode()).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(data.encode()).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(data.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def generate_audit_hash(event_data: dict) -> str:
    """
    Generate a SHA-256 hash for audit events.
    Used for blockchain anchoring and tamper detection.

    Args:
        event_data: Dictionary containing audit event data

    Returns:
        SHA-256 hash string
    """
    import json
    # Sort keys for consistent hashing
    data_str = json.dumps(event_data, sort_keys=True, default=str)
    return hashlib.sha256(data_str.encode()).hexdigest()


def anchor_to_chain(hash_str: str) -> str:
    """
    Anchor a hash to the blockchain (Phase 2 feature).
    Currently logs the hash; will integrate with permissioned chain later.

    Args:
        hash_str: Hash string to anchor

    Returns:
        The anchored hash string
    """
    if settings.blockchain_node:
        # TODO: Integrate with actual blockchain node
        logger.info(f"Would anchor to blockchain node: {settings.blockchain_node}")
    else:
        logger.debug(f"Blockchain not configured. Hash recorded: {hash_str}")

    return hash_str
