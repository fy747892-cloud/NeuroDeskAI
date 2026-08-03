import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.files.models import DocumentAnalysisResult, DocumentText, File


class FileRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        owner_user_id: uuid.UUID,
        filename: str,
        mime_type: str,
        size_bytes: int,
        storage_key: str,
    ) -> File:
        file = File(
            tenant_id=tenant_id,
            organization_id=organization_id,
            owner_user_id=owner_user_id,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_key=storage_key,
            status="pending_upload",
        )
        self._db.add(file)
        await self._db.flush()
        return file

    async def get_by_id(
        self, *, tenant_id: uuid.UUID, organization_id: uuid.UUID, file_id: uuid.UUID
    ) -> File | None:
        result = await self._db.execute(
            select(File).where(
                File.tenant_id == tenant_id,
                File.organization_id == organization_id,
                File.id == file_id,
                File.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_files(
        self,
        *,
        tenant_id: uuid.UUID,
        organization_id: uuid.UUID,
        search: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[File], int]:
        statement = select(File).where(
            File.tenant_id == tenant_id,
            File.organization_id == organization_id,
            File.is_deleted.is_(False),
        )
        if status is not None:
            statement = statement.where(File.status == status)
        if search is not None:
            statement = statement.where(File.filename.ilike(f"%{search}%"))

        total = (
            await self._db.execute(select(func.count()).select_from(statement.subquery()))
        ).scalar_one()

        ordered_statement = statement.order_by(
            File.created_at.desc(), File.id.desc()
        ).offset(offset)
        if limit is not None:
            ordered_statement = ordered_statement.limit(limit)
        result = await self._db.execute(ordered_statement)
        return list(result.scalars().all()), total

    async def update_status(self, *, file: File, status: str) -> File:
        file.status = status
        await self._db.flush()
        return file

    async def update_size(self, *, file: File, size_bytes: int) -> File:
        file.size_bytes = size_bytes
        await self._db.flush()
        return file

    async def update_filename(self, *, file: File, filename: str) -> File:
        file.filename = filename
        await self._db.flush()
        return file

    async def soft_delete(self, *, file: File) -> File:
        file.is_deleted = True
        file.deleted_at = datetime.now(timezone.utc)
        file.status = "deleted"
        await self._db.flush()
        return file


class DocumentTextRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_file(self, *, file_id: uuid.UUID) -> DocumentText | None:
        result = await self._db.execute(select(DocumentText).where(DocumentText.file_id == file_id))
        return result.scalar_one_or_none()

    async def upsert(
        self, *, tenant_id: uuid.UUID, file_id: uuid.UUID, extracted_text: str | None, status: str
    ) -> DocumentText:
        existing = await self.get_by_file(file_id=file_id)
        if existing is not None:
            existing.extracted_text = extracted_text
            existing.status = status
            await self._db.flush()
            return existing

        document_text = DocumentText(
            tenant_id=tenant_id, file_id=file_id, extracted_text=extracted_text, status=status
        )
        self._db.add(document_text)
        await self._db.flush()
        return document_text


class DocumentAnalysisRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_file(self, *, file_id: uuid.UUID) -> DocumentAnalysisResult | None:
        result = await self._db.execute(
            select(DocumentAnalysisResult).where(DocumentAnalysisResult.file_id == file_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self, *, tenant_id: uuid.UUID, file_id: uuid.UUID, summary: str | None, status: str
    ) -> DocumentAnalysisResult:
        existing = await self.get_by_file(file_id=file_id)
        if existing is not None:
            existing.summary = summary
            existing.status = status
            await self._db.flush()
            return existing

        result = DocumentAnalysisResult(
            tenant_id=tenant_id, file_id=file_id, summary=summary, status=status
        )
        self._db.add(result)
        await self._db.flush()
        return result
