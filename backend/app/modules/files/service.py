import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ProviderError, ValidationAppError
from app.modules.files.extraction import extract_text
from app.modules.files.models import File
from app.modules.files.provider import (
    MockDocumentSummaryProvider,
    MockMalwareScanProvider,
    ObjectStorageProvider,
)
from app.modules.files.repository import (
    DocumentAnalysisRepository,
    DocumentTextRepository,
    FileRepository,
)

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/x-m4a",
    "message/rfc822",
}

UPLOAD_URL_EXPIRES_IN = 900


class FileService:
    def __init__(self, db: AsyncSession):
        self._files = FileRepository(db)
        self._texts = DocumentTextRepository(db)
        self._analyses = DocumentAnalysisRepository(db)
        self._storage = ObjectStorageProvider()
        self._scanner = MockMalwareScanProvider()
        self._summarizer = MockDocumentSummaryProvider()

    async def start_upload(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        filename: str,
        mime_type: str,
        size_bytes: int,
    ) -> dict:
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValidationAppError(f"File type '{mime_type}' is not allowed.")
        if size_bytes <= 0 or size_bytes > MAX_FILE_SIZE_BYTES:
            raise ValidationAppError(
                f"File size must be between 1 and {MAX_FILE_SIZE_BYTES} bytes."
            )

        storage_key = str(uuid.uuid4())
        file = await self._files.create(
            tenant_id=tenant_id,
            organization_id=organization_id,
            owner_user_id=owner_user_id,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_key=storage_key,
        )
        upload_url = await self._storage.generate_upload_url(
            storage_key=storage_key, content_type=mime_type
        )
        return {"file": file, "upload_url": upload_url, "expires_in": UPLOAD_URL_EXPIRES_IN}

    async def complete_upload(self, *, file: File) -> File:
        if file.status in ("ready", "infected", "rejected"):
            return file

        head = await self._storage.head_object(storage_key=file.storage_key)
        if head is None:
            raise NotFoundError(
                "Upload not found yet. Upload the file to the signed URL before completing."
            )

        actual_size = head["ContentLength"]
        if actual_size > MAX_FILE_SIZE_BYTES:
            await self._files.update_status(file=file, status="rejected")
            raise ValidationAppError("Uploaded file exceeds the maximum allowed size.")
        await self._files.update_size(file=file, size_bytes=actual_size)

        content = await self._storage.get_object_bytes(storage_key=file.storage_key)
        is_clean = await self._scanner.scan(content)
        if not is_clean:
            await self._files.update_status(file=file, status="infected")
            return file

        extracted_text, extraction_status = extract_text(mime_type=file.mime_type, content=content)
        await self._texts.upsert(
            tenant_id=file.tenant_id,
            file_id=file.id,
            extracted_text=extracted_text,
            status=extraction_status,
        )
        await self._files.update_status(file=file, status="ready")
        return file

    async def get_download_url(self, *, file: File) -> str:
        if file.status != "ready":
            raise ValidationAppError(
                "Only a successfully scanned and processed file can be downloaded."
            )
        return await self._storage.generate_download_url(storage_key=file.storage_key)

    async def analyze(self, *, file: File) -> None:
        if file.status != "ready":
            raise ValidationAppError("Only a ready file can be analyzed.")

        document_text = await self._texts.get_by_file(file_id=file.id)
        if (
            document_text is None
            or document_text.status != "extracted"
            or not document_text.extracted_text
        ):
            raise ValidationAppError("This file has no extracted text to summarize.")

        try:
            summary = await self._summarizer.summarize(document_text.extracted_text)
        except RuntimeError as exc:
            await self._analyses.upsert(
                tenant_id=file.tenant_id, file_id=file.id, summary=None, status="failed"
            )
            raise ProviderError(str(exc)) from exc

        await self._analyses.upsert(
            tenant_id=file.tenant_id, file_id=file.id, summary=summary, status="completed"
        )

    async def delete(self, *, file: File) -> File:
        return await self._files.soft_delete(file=file)
