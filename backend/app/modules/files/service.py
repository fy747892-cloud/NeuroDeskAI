import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ProviderError, ValidationAppError
from app.modules.ai.repository import AIRepository
from app.modules.files.extraction import extract_text
from app.modules.files.models import File
from app.modules.files.provider import (
    MockMalwareScanProvider,
    ObjectStorageProvider,
    get_document_summary_provider,
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
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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
        self._ai = AIRepository(db)
        self._storage = ObjectStorageProvider()
        self._scanner = MockMalwareScanProvider()
        self._summarizer = get_document_summary_provider()

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
        await self._create_action_approvals_from_document(file=file, text=document_text.extracted_text)

    async def delete(self, *, file: File) -> File:
        return await self._files.soft_delete(file=file)

    async def _create_action_approvals_from_document(self, *, file: File, text: str) -> None:
        suggestions = _extract_action_suggestions(text)
        if not suggestions["tasks"] and not suggestions["appointments"]:
            suggestions["tasks"].append(
                {
                    "title": f"Dosyayı takip et: {file.filename}",
                    "description": _document_excerpt(text),
                    "priority": "medium",
                    "reason": "Dosya analizi tamamlandı ancak net görev/randevu satırı bulunamadı.",
                    "confidence": 0.5,
                }
            )

        prompt = await self._ai.get_or_create_prompt_version(
            name="document_action_extraction",
            version=f"{self._summarizer.provider_name}-{self._summarizer.model_name}",
        )
        job = await self._ai.create_job(
            tenant_id=file.tenant_id,
            organization_id=file.organization_id,
            requested_by=file.owner_user_id,
            source_type="file",
            source_id=file.id,
        )
        await self._ai.mark_processing(job=job)
        task_result = await self._ai.create_result(
            tenant_id=file.tenant_id,
            job_id=job.id,
            result_type="document_task_extraction",
            result_payload={"items": suggestions["tasks"]},
            prompt_version_id=prompt.id,
            model_config={"provider": self._summarizer.provider_name, "model": self._summarizer.model_name},
        )
        appointment_result = await self._ai.create_result(
            tenant_id=file.tenant_id,
            job_id=job.id,
            result_type="document_appointment_extraction",
            result_payload={"items": suggestions["appointments"]},
            prompt_version_id=prompt.id,
            model_config={"provider": self._summarizer.provider_name, "model": self._summarizer.model_name},
        )
        for item in suggestions["tasks"]:
            await self._ai.create_action_approval(
                tenant_id=file.tenant_id,
                organization_id=file.organization_id,
                requested_by=file.owner_user_id,
                analysis_result_id=task_result.id,
                action_type="task",
                source_type="file",
                source_id=file.id,
                suggested_payload=item,
                confidence_score=item.get("confidence"),
            )
        for item in suggestions["appointments"]:
            await self._ai.create_action_approval(
                tenant_id=file.tenant_id,
                organization_id=file.organization_id,
                requested_by=file.owner_user_id,
                analysis_result_id=appointment_result.id,
                action_type="appointment",
                source_type="file",
                source_id=file.id,
                suggested_payload=item,
                confidence_score=item.get("confidence"),
            )
        await self._ai.mark_completed(job=job)


def _extract_action_suggestions(text: str) -> dict[str, list[dict]]:
    tasks: list[dict] = []
    appointments: list[dict] = []
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) < 2:
            continue

        kind = cells[0].lower()
        title = cells[1]
        raw_date = cells[2] if len(cells) > 2 else None
        if kind == "task" and title:
            tasks.append(
                {
                    "title": title,
                    "description": "Dosya analizinden çıkarıldı.",
                    "priority": "medium",
                    "due_at": _parse_document_datetime(raw_date),
                    "confidence": 0.7,
                }
            )
        if kind == "appointment" and title:
            start_at = _parse_document_datetime(raw_date) or _default_future_datetime()
            appointments.append(
                {
                    "title": title,
                    "description": "Dosya analizinden çıkarıldı.",
                    "proposed_datetime": start_at,
                    "end_datetime": _add_minutes(start_at, 30),
                    "confidence": 0.7,
                }
            )
    return {"tasks": tasks, "appointments": appointments}


def _parse_document_datetime(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().replace(" ", "T")
    for candidate in (normalized, f"{normalized}T09:00:00"):
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.isoformat()
        except ValueError:
            continue
    return None


def _default_future_datetime() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0).isoformat()


def _add_minutes(value: str, minutes: int) -> str:
    parsed = datetime.fromisoformat(value)
    return (parsed + timedelta(minutes=minutes)).isoformat()


def _document_excerpt(text: str) -> str:
    excerpt = " ".join(text.split())[:240]
    return excerpt or "Dosya içeriğini inceleyip sonraki adımı belirle."
