from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UploadUrlIn(BaseModel):
    filename: str
    mime_type: str
    size_bytes: int


class UploadUrlOut(BaseModel):
    file_id: UUID
    upload_url: str
    expires_in: int


class CompleteUploadIn(BaseModel):
    file_id: UUID


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    owner_user_id: UUID
    filename: str
    mime_type: str
    size_bytes: int
    status: str
    created_at: datetime


class DownloadUrlOut(BaseModel):
    download_url: str
    expires_in: int


class DocumentTextOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_id: UUID
    extracted_text: str | None
    status: str


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_id: UUID
    summary: str | None
    status: str
