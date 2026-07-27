import uuid
import re
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, Form, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_permission
from app.core.errors import NotFoundError, ProviderError, ValidationAppError
from app.core.permissions import Permission
from app.db.session import get_db
from app.modules.ai.provider import get_ai_provider
from app.modules.audit.repository import AuditRepository
from app.modules.conversations.repository import ConversationRepository
from app.modules.conversations.models import Call
from app.modules.conversations.schemas import CallOut, CallTextCreate, CallTextOut, CallUpdate
from app.modules.files.repository import DocumentTextRepository, FileRepository
from app.modules.users.models import User

router = APIRouter(prefix="/calls", tags=["calls"])

MAX_AUDIO_BYTES = 25 * 1024 * 1024


@router.get("", response_model=list[CallOut])
async def list_calls(
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_READ)),
    db: AsyncSession = Depends(get_db),
) -> list[Call]:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    return await ConversationRepository(db).list_calls(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
    )


@router.post("/text", response_model=CallTextOut, status_code=status.HTTP_201_CREATED)
async def create_call_from_text(
    body: CallTextCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> CallTextOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    conversations = ConversationRepository(db)
    transcript_text = _format_transcript_text(body.transcript_text)
    conversation, call, transcription = await conversations.create_call_with_transcription(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        title=body.title,
        transcript_text=transcript_text,
        participant_names=body.participant_names,
        call_direction=body.call_direction,
        phone_number=body.phone_number,
        started_at=body.started_at,
        duration_seconds=body.duration_seconds,
        language=body.language,
    )
    await _create_transcript_file(
        db=db,
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        owner_user_id=current_user.id,
        transcript_text=transcription.transcript_text,
        created_at=call.started_at or call.created_at,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="call.text_uploaded",
        entity_type="call",
        entity_id=call.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"conversation_id": str(conversation.id)},
    )
    await db.commit()
    return CallTextOut(conversation=conversation, call=call, transcription=transcription)


@router.post("/audio", response_model=CallTextOut, status_code=status.HTTP_201_CREATED)
async def create_call_from_audio(
    request: Request,
    audio: UploadFile,
    title: str = Form(...),
    participant_names: str = Form(""),
    call_direction: str | None = Form(None),
    phone_number: str | None = Form(None),
    started_at: datetime | None = Form(None),
    duration_seconds: int | None = Form(None),
    language: str | None = Form(None),
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> CallTextOut:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise ValidationAppError("Uploaded audio file is empty.")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise ValidationAppError("Uploaded audio file is too large.")

    provider = get_ai_provider()
    try:
        transcript_text = await provider.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=audio.filename or "recording.m4a",
            content_type=audio.content_type or "audio/mp4",
            language=language,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            raise ProviderError(
                "AI transkripsiyon kotas\u0131 dolu. OpenAI plan\u0131n\u0131/faturaland\u0131rmas\u0131n\u0131 kontrol edin "
                "veya backend\'i ge\u00e7ici olarak LLM_PROVIDER=mock ile \u00e7al\u0131\u015ft\u0131r\u0131n."
            ) from exc
        if exc.response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }:
            raise ProviderError(
                "AI transkripsiyon anahtar\u0131 yetkisiz. OpenAI API anahtar\u0131n\u0131 ve model eri\u015fimini kontrol edin."
            ) from exc
        raise ProviderError(
            "Ses metne \u00e7evrilemedi. AI sa\u011flay\u0131c\u0131s\u0131 iste\u011fi kabul etmedi; kota, anahtar veya ses format\u0131n\u0131 kontrol edin."
        ) from exc
    except Exception as exc:
        raise ProviderError(
            "Ses metne \u00e7evrilemedi. AI sa\u011flay\u0131c\u0131s\u0131n\u0131, kotay\u0131 veya ses dosyas\u0131 format\u0131n\u0131 kontrol edin."
        ) from exc

    names = [name.strip() for name in participant_names.split(",") if name.strip()]

    conversations = ConversationRepository(db)
    conversation, call, transcription = await conversations.create_call_with_transcription(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        title=title,
        transcript_text=_format_transcript_text(transcript_text),
        participant_names=names,
        call_direction=call_direction,
        phone_number=phone_number,
        started_at=started_at,
        duration_seconds=duration_seconds,
        language=language,
    )
    await _create_transcript_file(
        db=db,
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        owner_user_id=current_user.id,
        transcript_text=transcription.transcript_text,
        created_at=call.started_at or call.created_at,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="call.audio_uploaded",
        entity_type="call",
        entity_id=call.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={
            "conversation_id": str(conversation.id),
            "provider": provider.provider_name,
        },
    )
    await db.commit()
    return CallTextOut(conversation=conversation, call=call, transcription=transcription)


async def _create_transcript_file(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    organization_id: uuid.UUID,
    owner_user_id: uuid.UUID,
    transcript_text: str,
    created_at: datetime,
) -> None:
    local_label = created_at.strftime("%d.%m.%Y, %H:%M")
    filename = f"{local_label} - isim eklemek i\u00e7in d\u00fczenleyin.txt"
    file = await FileRepository(db).create(
        tenant_id=tenant_id,
        organization_id=organization_id,
        owner_user_id=owner_user_id,
        filename=filename,
        mime_type="text/plain",
        size_bytes=len(transcript_text.encode("utf-8")),
        storage_key=f"call-transcripts/{uuid.uuid4()}.txt",
    )
    await FileRepository(db).update_status(file=file, status="ready")
    await DocumentTextRepository(db).upsert(
        tenant_id=tenant_id,
        file_id=file.id,
        extracted_text=transcript_text,
        status="extracted",
    )


def _format_transcript_text(text: str) -> str:
    cleaned = " ".join(text.split()).strip()
    cleaned = re.sub(r"\s+([,.!?;:])", r"\1", cleaned)
    cleaned = re.sub(r"([.!?])\s+(?=[A-ZÇĞİÖŞÜ0-9])", r"\1\n", cleaned)
    cleaned = re.sub(
        r"\s+(?=(Müşteri|Temsilci|Konuşmacı|Kişi|Kisi)\s*:)",
        "\n",
        cleaned,
        flags=re.IGNORECASE,
    )
    lines = [" ".join(line.split()) for line in cleaned.splitlines()]
    return "\n".join(line for line in lines if line)


@router.get("/{call_id}", response_model=CallOut)
async def get_call(
    call_id: uuid.UUID,
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Call:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    call = await ConversationRepository(db).get_call(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        call_id=call_id,
    )
    if call is None:
        raise NotFoundError("Call not found.")
    return call


@router.patch("/{call_id}", response_model=CallOut)
async def update_call(
    call_id: uuid.UUID,
    body: CallUpdate,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Call:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    conversations = ConversationRepository(db)
    call = await conversations.get_call(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        call_id=call_id,
    )
    if call is None:
        raise NotFoundError("Call not found.")

    await conversations.update_call(
        call=call,
        call_direction=body.call_direction,
        phone_number=body.phone_number,
        started_at=body.started_at,
        duration_seconds=body.duration_seconds,
        status=body.status,
    )
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="call.updated",
        entity_type="call",
        entity_id=call.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return call


@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call(
    call_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_permission(Permission.CONVERSATIONS_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> None:
    if current_user.organization_id is None:
        raise NotFoundError("Current organization not found.")

    conversations = ConversationRepository(db)
    call = await conversations.get_call(
        tenant_id=current_user.tenant_id,
        organization_id=current_user.organization_id,
        call_id=call_id,
    )
    if call is None:
        raise NotFoundError("Call not found.")

    await conversations.soft_delete_call(call=call)
    await AuditRepository(db).record(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action="call.deleted",
        entity_type="call",
        entity_id=call.id,
        request_id=request.headers.get("x-request-id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
