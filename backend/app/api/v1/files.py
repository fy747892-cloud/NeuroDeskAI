import uuid

from fastapi import APIRouter, Depends, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError, ValidationAppError
from app.core.pagination import Page, PaginationParams
from app.core.permissions import Permission
from app.core.rate_limit import RateLimiter
from app.db.redis import get_redis
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.files.models import File
from app.modules.files.repository import DocumentAnalysisRepository, DocumentTextRepository, FileRepository
from app.modules.files.schemas import (
    AnalysisOut,
    CompleteUploadIn,
    DocumentTextOut,
    DownloadUrlOut,
    FileOut,
    FileUpdateIn,
    UploadUrlIn,
    UploadUrlOut,
)
from app.modules.users.consent import get_consent
from app.modules.files.service import FileService
from app.modules.users.models import User

router = APIRouter(prefix="/files", tags=["files"])

DAILY_UPLOAD_LIMIT = 50


@router.post("/upload-url", response_model=UploadUrlOut, status_code=status.HTTP_201_CREATED)
async def start_file_upload(
    body: UploadUrlIn,
    current_user: User = Depends(require_permission(Permission.FILES_MANAGE)),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> UploadUrlOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    await RateLimiter(redis).check(
        key=f"file_upload:{current_user.tenant_id}", limit=DAILY_UPLOAD_LIMIT, window_seconds=86400
    )

    result = await FileService(db).start_upload(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        owner_user_id=current_user.id,
        filename=body.filename,
        mime_type=body.mime_type,
        size_bytes=body.size_bytes,
    )
    await db.commit()
    return UploadUrlOut(
        file_id=result["file"].id,
        upload_url=result["upload_url"],
        expires_in=result["expires_in"],
    )


@router.post("/complete-upload", response_model=FileOut)
async def complete_file_upload(
    body: CompleteUploadIn,
    request: Request,
    current_user: User = Depends(require_permission(Permission.FILES_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> File:
    file = await _get_current_file(db, current_user, body.file_id)
    file = await FileService(db).complete_upload(file=file)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="file.uploaded",
        entity_type="file",
        entity_id=file.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"status": file.status, "mime_type": file.mime_type},
    )
    await db.commit()
    return file


@router.get("", response_model=Page[FileOut])
async def list_files(
    search: str | None = None,
    status_filter: str | None = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_permission(Permission.FILES_READ)),
    db: AsyncSession = Depends(get_db),
) -> Page[FileOut]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    items, total = await FileRepository(db).list_files(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        search=search,
        status=status_filter,
        limit=pagination.page_size,
        offset=pagination.offset,
    )
    # response_model=Page[FileOut] performs the actual ORM->schema conversion at
    # request time; Page[File] can't be used as a static annotation here since
    # instantiating a Pydantic generic with a non-Pydantic ORM class crashes at import.
    return Page.create(items, total, pagination.page, pagination.page_size)  # type: ignore[arg-type]


@router.get("/{file_id}", response_model=FileOut)
async def get_file(
    file_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.FILES_READ)),
    db: AsyncSession = Depends(get_db),
) -> File:
    return await _get_current_file(db, current_user, file_id)


@router.patch("/{file_id}", response_model=FileOut)
async def update_file(
    file_id: uuid.UUID,
    body: FileUpdateIn,
    request: Request,
    current_user: User = Depends(require_permission(Permission.FILES_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> File:
    file = await _get_current_file(db, current_user, file_id)
    filename = body.filename.strip()
    if not filename:
        raise ValidationAppError("Dosya adı boş olamaz.")
    file = await FileRepository(db).update_filename(file=file, filename=filename)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="file.updated",
        entity_type="file",
        entity_id=file.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"filename": file.filename},
    )
    await db.commit()
    return file


@router.get("/{file_id}/text", response_model=DocumentTextOut)
async def get_file_text(
    file_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.FILES_READ)),
    db: AsyncSession = Depends(get_db),
):
    file = await _get_current_file(db, current_user, file_id)
    document_text = await DocumentTextRepository(db).get_by_file(file_id=file.id)
    if document_text is None:
        raise NotFoundError("No extracted text found for this file.")
    return document_text


@router.get("/{file_id}/download-url", response_model=DownloadUrlOut)
async def get_file_download_url(
    file_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.FILES_READ)),
    db: AsyncSession = Depends(get_db),
) -> DownloadUrlOut:
    file = await _get_current_file(db, current_user, file_id)
    download_url = await FileService(db).get_download_url(file=file)
    return DownloadUrlOut(download_url=download_url, expires_in=900)


@router.post("/{file_id}/analyze", response_model=AnalysisOut)
async def analyze_file(
    file_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.FILES_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    if not get_consent(current_user)["ai_processing"]:
        raise ValidationAppError(
            "AI processing is turned off in your settings. Turn it back on in "
            "Settings to analyze files."
        )
    file = await _get_current_file(db, current_user, file_id)
    await FileService(db).analyze(file=file)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="file.analyzed",
        entity_type="file",
        entity_id=file.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    analysis = await DocumentAnalysisRepository(db).get_by_file(file_id=file.id)
    if analysis is None:
        raise NotFoundError("Analysis result not found.")
    return analysis


@router.get("/{file_id}/analysis", response_model=AnalysisOut)
async def get_file_analysis(
    file_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.FILES_READ)),
    db: AsyncSession = Depends(get_db),
):
    file = await _get_current_file(db, current_user, file_id)
    analysis = await DocumentAnalysisRepository(db).get_by_file(file_id=file.id)
    if analysis is None:
        raise NotFoundError("This file has not been analyzed yet.")
    return analysis


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.FILES_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    file = await _get_current_file(db, current_user, file_id)
    await FileService(db).delete(file=file)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="file.deleted",
        entity_type="file",
        entity_id=file.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()


async def _get_current_file(db: AsyncSession, current_user: User, file_id: uuid.UUID) -> File:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")
    file = await FileRepository(db).get_by_id(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        file_id=file_id,
    )
    if file is None:
        raise NotFoundError("File not found.")
    return file
