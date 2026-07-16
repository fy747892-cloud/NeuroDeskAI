import asyncio

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings

_s3_client = boto3.client(
    "s3",
    endpoint_url=settings.minio_endpoint_url,
    aws_access_key_id=settings.minio_access_key,
    aws_secret_access_key=settings.minio_secret_key,
    region_name="us-east-1",
    config=Config(signature_version="s3v4"),
)

_public_s3_client = boto3.client(
    "s3",
    endpoint_url=settings.minio_public_endpoint_url or settings.minio_endpoint_url,
    aws_access_key_id=settings.minio_access_key,
    aws_secret_access_key=settings.minio_secret_key,
    region_name="us-east-1",
    config=Config(signature_version="s3v4"),
)

_bucket_ensured = False
_bucket_lock = asyncio.Lock()


def get_storage_client():
    return _s3_client


def get_public_storage_client():
    return _public_s3_client


def _create_bucket_if_missing() -> None:
    try:
        _s3_client.head_bucket(Bucket=settings.minio_bucket_name)
    except ClientError:
        try:
            _s3_client.create_bucket(Bucket=settings.minio_bucket_name)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                raise


async def ensure_bucket() -> None:
    global _bucket_ensured
    if _bucket_ensured:
        return
    async with _bucket_lock:
        if _bucket_ensured:
            return
        await asyncio.to_thread(_create_bucket_if_missing)
        _bucket_ensured = True
