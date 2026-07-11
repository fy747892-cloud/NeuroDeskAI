import asyncio

from botocore.exceptions import ClientError

from app.core.config import settings
from app.db.storage import ensure_bucket, get_storage_client

UPLOAD_URL_TTL_SECONDS = 900
DOWNLOAD_URL_TTL_SECONDS = 900


class ObjectStorageProvider:
    """Real S3-compatible object storage backed by MinIO (no external account needed)."""

    def __init__(self):
        self._client = get_storage_client()

    async def generate_upload_url(self, *, storage_key: str, content_type: str) -> str:
        await ensure_bucket()
        return await asyncio.to_thread(
            self._client.generate_presigned_url,
            "put_object",
            Params={
                "Bucket": settings.minio_bucket_name,
                "Key": storage_key,
                "ContentType": content_type,
            },
            ExpiresIn=UPLOAD_URL_TTL_SECONDS,
        )

    async def generate_download_url(self, *, storage_key: str) -> str:
        await ensure_bucket()
        return await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": settings.minio_bucket_name, "Key": storage_key},
            ExpiresIn=DOWNLOAD_URL_TTL_SECONDS,
        )

    async def head_object(self, *, storage_key: str) -> dict | None:
        await ensure_bucket()
        try:
            return await asyncio.to_thread(
                self._client.head_object, Bucket=settings.minio_bucket_name, Key=storage_key
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchKey"):
                return None
            raise

    async def get_object_bytes(self, *, storage_key: str) -> bytes:
        await ensure_bucket()
        response = await asyncio.to_thread(
            self._client.get_object, Bucket=settings.minio_bucket_name, Key=storage_key
        )
        return await asyncio.to_thread(response["Body"].read)


class MockMalwareScanProvider:
    """Stands in for a real AV/malware scanning engine — CILT_11 explicitly scopes this
    sprint to a "hook", not a real scan engine."""

    provider_name = "mock"

    async def scan(self, content: bytes) -> bool:
        return b"[mock-fail]" not in content


class MockDocumentSummaryProvider:
    """Stands in for a real LLM-backed document summarization provider (no external
    credentials configured yet), same lineage as MockAIProvider/MockChatProvider."""

    provider_name = "mock"
    model_name = "mock-summary-v1"

    async def summarize(self, text: str) -> str:
        if "[mock-fail]" in text.lower():
            raise RuntimeError("Mock document summary provider failed to summarize.")

        clean_text = " ".join(text.split())
        preview = clean_text[:280]
        return preview if preview else "Document has no extractable content to summarize."
