import asyncio
from typing import Any

import httpx
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.llm_retry import with_retry
from app.db.storage import ensure_bucket, get_public_storage_client, get_storage_client

UPLOAD_URL_TTL_SECONDS = 900
DOWNLOAD_URL_TTL_SECONDS = 900


class ObjectStorageProvider:
    """Real S3-compatible object storage backed by MinIO (no external account needed)."""

    def __init__(self):
        self._client = get_storage_client()
        self._public_client = get_public_storage_client()

    async def generate_upload_url(self, *, storage_key: str, content_type: str) -> str:
        await ensure_bucket()
        return await asyncio.to_thread(
            self._public_client.generate_presigned_url,
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
            self._public_client.generate_presigned_url,
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

    async def put_object(self, *, storage_key: str, data: bytes, content_type: str) -> None:
        await ensure_bucket()
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=settings.minio_bucket_name,
            Key=storage_key,
            Body=data,
            ContentType=content_type,
        )

    async def delete_object(self, *, storage_key: str) -> None:
        await ensure_bucket()
        await asyncio.to_thread(
            self._client.delete_object, Bucket=settings.minio_bucket_name, Key=storage_key
        )


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


class OpenAICompatibleDocumentSummaryProvider:
    """Real LLM-backed document summarization via an OpenAI-compatible Chat
    Completions endpoint, same LLM_PROVIDER/LLM_BASE_URL convention as
    ai/provider.py and ai_chat/provider.py."""

    provider_name = "openai"

    def __init__(self) -> None:
        self.model_name = settings.llm_analysis_model
        self._base_url = settings.llm_base_url.rstrip("/")
        self._api_key = settings.llm_api_key
        self._timeout = settings.llm_timeout_seconds

    async def summarize(self, text: str) -> str:
        if not self._api_key:
            raise RuntimeError("LLM_API_KEY is required when LLM_PROVIDER is openai.")

        payload = {
            "model": self.model_name,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Belge metnini Türkçe olarak 2-4 kısa cümlede özetle. "
                        "Yalnızca metinde açıkça bulunan bilgileri kullan, ayrıntı uydurma. "
                        "OCR veya PDF çıkarımı bozuk görünüyorsa ham sembolleri kopyalama; "
                        "anlaşılabilen kişi, tarih, konu ve aksiyonları sade bir dille yaz. "
                        "Kullanıcıya gösterilecek metinde İngilizce başlık veya açıklama kullanma."
                    ),
                },
                {"role": "user", "content": text},
            ],
        }
        response = await with_retry(lambda: self._post_chat_completion(payload))
        return response["choices"][0]["message"]["content"].strip()

    async def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
        response.raise_for_status()
        return response.json()


def get_document_summary_provider():
    provider = settings.llm_provider.lower()
    if provider in {"mock", "local"}:
        return MockDocumentSummaryProvider()
    if provider in {"openai", "openai-compatible"}:
        return OpenAICompatibleDocumentSummaryProvider()
    raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")
