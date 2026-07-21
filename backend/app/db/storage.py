import asyncio
from functools import lru_cache

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings

_bucket_ensured = False
_bucket_lock = asyncio.Lock()


def _create_client(endpoint_url: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        region_name="us-east-1",
        config=Config(signature_version="s3v4"),
    )


@lru_cache(maxsize=1)
def get_storage_client():
    return _create_client(settings.minio_endpoint_url)


@lru_cache(maxsize=1)
def get_public_storage_client():
    return _create_client(settings.minio_public_endpoint_url or settings.minio_endpoint_url)


def reset_storage_clients() -> None:
    get_storage_client.cache_clear()
    get_public_storage_client.cache_clear()


def _create_bucket_if_missing() -> None:
    client = get_storage_client()
    try:
        client.head_bucket(Bucket=settings.minio_bucket_name)
    except ClientError:
        try:
            client.create_bucket(Bucket=settings.minio_bucket_name)
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
