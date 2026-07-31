import re
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationAppError
from app.modules.ai.models import AIActionApproval, AIAnalysisJob
from app.modules.ai.provider import get_ai_provider
from app.modules.ai.repository import AIRepository
from app.modules.analytics.repository import AICostLogRepository
from app.modules.appointments.service import AppointmentService
from app.modules.billing.service import AI_ANALYSIS_REQUESTS_QUOTA_TYPE, BillingService
from app.modules.conversations.models import Call, DEFAULT_WEB_RECORDING_TITLE
from app.modules.conversations.repository import ConversationRepository
from app.modules.deals.service import DealService
from app.modules.tasks.service import TaskService


ACTION_PAYLOAD_DEFAULTS = {
    "task": {
        "title": "Görüşmeyi takip et",
        "description": "Görüşmeden çıkarılan görevi kontrol et.",
        "reason": "Bu görev görüşme içeriğinde geçen aksiyon ihtiyacından çıkarıldı.",
    },
    "appointment": {
        "title": "Takip randevusu planla",
        "description": "Görüşmeden çıkarılan randevu önerisini kontrol et.",
        "reason": "Bu randevu önerisi görüşmede geçen tarih veya takip ihtiyacından çıkarıldı.",
    },
    "deal": {
        "title": "Fırsatı değerlendir",
        "description": "Görüşmeden çıkarılan fırsat bilgisini kontrol et.",
        "reason": "Bu fırsat görüşmede geçen satış, teklif veya iş ihtimalinden çıkarıldı.",
    },
}


def _derive_title_from_summary(summary_text: str, *, max_length: int = 70) -> str:
    text = summary_text.strip()
    if not text:
        return ""
    # Prefer the first sentence when it reads as a standalone title.
    first_sentence = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0].strip()
    candidate = first_sentence or text
    if len(candidate) > max_length:
        candidate = candidate[: max_length - 1].rstrip() + "…"
    return candidate


class AIAnalysisService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._ai = AIRepository(db)
        self._conversations = ConversationRepository(db)
        self._cost_logs = AICostLogRepository(db)
        self._billing = BillingService(db)
        self._provider = get_ai_provider()

    async def request_conversation_analysis(
        self,
        *,
        tenant_id,
        organization_id,
        user_id,
        conversation_id,
    ) -> AIAnalysisJob:
        await self._billing.enforce_ai_usage_guard(
            tenant_id=tenant_id, quota_type=AI_ANALYSIS_REQUESTS_QUOTA_TYPE
        )

        conversation = await self._conversations.get_conversation(
            tenant_id=tenant_id,
            organization_id=organization_id,
            conversation_id=conversation_id,
        )
        if conversation is None:
            raise NotFoundError("Conversation not found.")

        job = await self._ai.create_job(
            tenant_id=tenant_id,
            organization_id=organization_id,
            requested_by=user_id,
            source_type="conversation",
            source_id=conversation.id,
        )
        await self._db.flush()
        await self.process_job(job=job)
        await self._db.commit()
        return await self._ai.get_job(
            tenant_id=tenant_id,
            organization_id=organization_id,
            job_id=job.id,
        ) or job

    async def retry_job(self, *, tenant_id, organization_id, job_id) -> AIAnalysisJob:
        job = await self._ai.get_job(
            tenant_id=tenant_id,
            organization_id=organization_id,
            job_id=job_id,
        )
        if job is None:
            raise NotFoundError("AI analysis job not found.")
        if job.status not in {"failed", "cancelled"}:
            raise ValidationAppError("Only failed or cancelled jobs can be retried.")

        await self._billing.enforce_ai_usage_guard(
            tenant_id=tenant_id, quota_type=AI_ANALYSIS_REQUESTS_QUOTA_TYPE
        )

        await self._ai.reset_for_retry(job=job)
        await self.process_job(job=job)
        await self._db.commit()
        return await self._ai.get_job(
            tenant_id=tenant_id,
            organization_id=organization_id,
            job_id=job.id,
        ) or job

    async def process_job(self, *, job: AIAnalysisJob) -> None:
        await self._ai.mark_processing(job=job)
        try:
            conversation = await self._conversations.get_conversation(
                tenant_id=job.tenant_id,
                organization_id=job.organization_id,
                conversation_id=job.source_id,
            )
            if conversation is None:
                raise NotFoundError("Conversation not found.")

            transcript_text = self._extract_transcript_text(conversation.calls)
            if not transcript_text:
                raise ValidationAppError("Conversation has no transcript text to analyze.")

            prompt = await self._ai.get_or_create_prompt_version(
                name="conversation_analysis",
                version=f"{self._provider.provider_name}-{self._provider.model_name}",
            )
            start_time = time.monotonic()
            output = await self._provider.analyze_conversation(
                title=conversation.title,
                transcript_text=transcript_text,
            )
            output = self._ensure_action_suggestions(
                output=output,
                title=conversation.title,
                transcript_text=transcript_text,
            )
            if conversation.title.strip() == DEFAULT_WEB_RECORDING_TITLE:
                derived_title = _derive_title_from_summary(
                    str(output.summary.get("summary_text") or "")
                )
                if derived_title:
                    await self._conversations.update_conversation(
                        conversation=conversation, title=derived_title
                    )
            latency_ms = int((time.monotonic() - start_time) * 1000)
            await self._cost_logs.record(
                tenant_id=job.tenant_id,
                user_id=job.requested_by,
                provider=self._provider.provider_name,
                model=self._provider.model_name,
                source_type="conversation_analysis",
                input_tokens=output.input_tokens,
                output_tokens=output.output_tokens,
                latency_ms=latency_ms,
            )
            await self._billing.record_ai_usage(
                tenant_id=job.tenant_id,
                user_id=job.requested_by,
                usage_type=AI_ANALYSIS_REQUESTS_QUOTA_TYPE,
            )
            model_config = {
                "provider": self._provider.provider_name,
                "model": self._provider.model_name,
            }
            await self._ai.create_result(
                tenant_id=job.tenant_id,
                job_id=job.id,
                result_type="conversation_summary",
                result_payload=output.summary,
                prompt_version_id=prompt.id,
                model_config=model_config,
            )
            task_result = await self._ai.create_result(
                tenant_id=job.tenant_id,
                job_id=job.id,
                result_type="task_extraction",
                result_payload=output.tasks,
                prompt_version_id=prompt.id,
                model_config=model_config,
            )
            appointment_result = await self._ai.create_result(
                tenant_id=job.tenant_id,
                job_id=job.id,
                result_type="appointment_extraction",
                result_payload=output.appointments,
                prompt_version_id=prompt.id,
                model_config=model_config,
            )
            deal_result = await self._ai.create_result(
                tenant_id=job.tenant_id,
                job_id=job.id,
                result_type="deal_extraction",
                result_payload=output.deals,
                prompt_version_id=prompt.id,
                model_config=model_config,
            )
            await self._create_action_approvals_for_payload(
                tenant_id=job.tenant_id,
                organization_id=job.organization_id,
                requested_by=job.requested_by,
                source_type=job.source_type,
                source_id=job.source_id,
                result_id=task_result.id,
                action_type="task",
                items=output.tasks.get("items", []),
            )
            await self._create_action_approvals_for_payload(
                tenant_id=job.tenant_id,
                organization_id=job.organization_id,
                requested_by=job.requested_by,
                source_type=job.source_type,
                source_id=job.source_id,
                result_id=appointment_result.id,
                action_type="appointment",
                items=output.appointments.get("items", []),
            )
            await self._create_action_approvals_for_payload(
                tenant_id=job.tenant_id,
                organization_id=job.organization_id,
                requested_by=job.requested_by,
                source_type=job.source_type,
                source_id=job.source_id,
                result_id=deal_result.id,
                action_type="deal",
                items=output.deals.get("items", []),
            )
            await self._ai.mark_completed(job=job)
        except Exception as exc:
            await self._ai.mark_failed(job=job, error_message=str(exc))

    async def approve_action(
        self,
        *,
        tenant_id,
        organization_id,
        approval_id,
        user_id,
        approved_payload: dict | None = None,
    ) -> AIActionApproval:
        approval = await self._ai.get_action_approval(
            tenant_id=tenant_id,
            organization_id=organization_id,
            approval_id=approval_id,
        )
        if approval is None:
            raise NotFoundError("AI action approval not found.")
        if approval.status == "approved":
            await self._materialize_approved_action(
                tenant_id=tenant_id,
                organization_id=organization_id,
                user_id=user_id,
                approval=approval,
            )
            return approval
        self._ensure_pending(approval)
        payload = approved_payload if approved_payload is not None else approval.suggested_payload
        self._validate_approved_payload(approval.action_type, payload)
        approval.status = "approved"
        approval.approved_payload = payload
        approval.decided_by = user_id
        approval.decided_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._materialize_approved_action(
            tenant_id=tenant_id,
            organization_id=organization_id,
            user_id=user_id,
            approval=approval,
        )
        return approval

    async def reject_action(
        self,
        *,
        tenant_id,
        organization_id,
        approval_id,
        user_id,
    ) -> AIActionApproval:
        approval = await self._ai.get_action_approval(
            tenant_id=tenant_id,
            organization_id=organization_id,
            approval_id=approval_id,
        )
        if approval is None:
            raise NotFoundError("AI action approval not found.")
        self._ensure_pending(approval)
        approval.status = "rejected"
        approval.approved_payload = None
        approval.decided_by = user_id
        approval.decided_at = datetime.now(timezone.utc)
        await self._db.flush()
        return approval

    def _extract_transcript_text(self, calls: list[Call]) -> str:
        chunks: list[str] = []
        for call in calls:
            for transcription in call.transcriptions:
                if not transcription.is_deleted:
                    chunks.append(transcription.transcript_text)
        return "\n\n".join(chunks)

    async def _create_action_approvals_for_payload(
        self,
        *,
        tenant_id,
        organization_id,
        requested_by,
        source_type,
        source_id,
        result_id,
        action_type: str,
        items: list[dict],
    ) -> None:
        for item in items:
            item = _prepare_approval_payload(item, action_type=action_type)
            if item is None:
                continue
            await self._ai.create_action_approval(
                tenant_id=tenant_id,
                organization_id=organization_id,
                requested_by=requested_by,
                analysis_result_id=result_id,
                action_type=action_type,
                source_type=source_type,
                source_id=source_id,
                suggested_payload=item,
                confidence_score=item.get("confidence"),
            )

    def _ensure_pending(self, approval: AIActionApproval) -> None:
        if approval.status != "pending":
            raise ValidationAppError("Only pending AI action approvals can be decided.")
        if approval.expires_at is not None and approval.expires_at <= datetime.now(timezone.utc):
            approval.status = "expired"
            raise ValidationAppError("Expired AI action approvals cannot be applied.")

    def _ensure_action_suggestions(
        self,
        *,
        output,
        title: str,
        transcript_text: str,
    ):
        has_task_items = isinstance(output.tasks, dict) and bool(output.tasks.get("items"))
        has_items = any(
            bool(payload.get("items"))
            for payload in (output.tasks, output.appointments, output.deals)
            if isinstance(payload, dict)
        )
        if has_task_items:
            return output

        excerpt = " ".join(transcript_text.split())[:240]
        output.tasks["items"] = [
            {
                "title": f"Takip et: {title}",
                "description": excerpt
                or "AI analizi aksiyon üretmedi; görüşmeyi kontrol edip sonraki adımı belirle.",
                "priority": "medium",
                "reason": "Analiz tamamlandı ancak net aksiyon üretilemediği için takip görevi önerildi.",
                "confidence": 0.55 if has_items else 0.5,
            }
        ]
        return output

    def _validate_approved_payload(self, action_type: str, payload: dict) -> None:
        if action_type in {"task", "create_task", "task/create_task"} and not payload.get("title"):
            raise ValidationAppError("Approved task payload must include a title.")
        if action_type in {"appointment", "create_appointment", "appointment/create_appointment"}:
            if not payload.get("title"):
                raise ValidationAppError("Approved appointment payload must include a title.")
            if not payload.get("proposed_datetime"):
                raise ValidationAppError(
                    "Approved appointment payload must include proposed_datetime."
                )
        if action_type in {"deal", "create_deal", "deal/create_deal"} and not payload.get("title"):
            raise ValidationAppError("Approved deal payload must include a title.")

    async def _materialize_approved_action(
        self,
        *,
        tenant_id,
        organization_id,
        user_id,
        approval: AIActionApproval,
    ) -> None:
        if approval.action_type in {"task", "create_task", "task/create_task"}:
            await TaskService(self._db).create_task_from_approval(
                tenant_id=tenant_id,
                organization_id=organization_id,
                user_id=user_id,
                approval_id=approval.id,
            )
            return
        if approval.action_type in {"appointment", "create_appointment", "appointment/create_appointment"}:
            await AppointmentService(self._db).create_appointment_from_approval(
                tenant_id=tenant_id,
                organization_id=organization_id,
                user_id=user_id,
                approval_id=approval.id,
            )
            return
        if approval.action_type in {"deal", "create_deal", "deal/create_deal"}:
            await DealService(self._db).create_deal_from_approval(
                tenant_id=tenant_id,
                organization_id=organization_id,
                owner_user_id=user_id,
                approval_id=approval.id,
            )


def _prepare_approval_payload(item: dict, *, action_type: str) -> dict | None:
    if not isinstance(item, dict):
        return None

    defaults = ACTION_PAYLOAD_DEFAULTS.get(action_type, ACTION_PAYLOAD_DEFAULTS["task"])
    payload = dict(item)
    title = str(payload.get("title") or payload.get("name") or payload.get("subject") or "").strip()
    payload["title"] = title or defaults["title"]

    description = str(payload.get("description") or payload.get("notes") or "").strip()
    payload["description"] = description or defaults["description"]

    reason = str(
        payload.get("reason")
        or payload.get("source_excerpt")
        or payload.get("evidence")
        or payload.get("matched_text")
        or ""
    ).strip()
    payload["reason"] = reason or defaults["reason"]

    if action_type == "task":
        priority = str(payload.get("priority") or "medium").lower()
        payload["priority"] = priority if priority in {"low", "medium", "high"} else "medium"
    if action_type == "deal":
        stage = str(payload.get("stage") or "lead").lower()
        payload["stage"] = stage if stage in {
            "lead",
            "proposal_sent",
            "negotiation",
            "invoiced",
            "won",
            "lost",
        } else "lead"
    if action_type == "appointment":
        _normalize_future_appointment_datetime(payload)

    return payload


def _normalize_future_appointment_datetime(payload: dict) -> None:
    start_at = _parse_datetime_or_none(payload.get("proposed_datetime") or payload.get("start_at"))
    if start_at is None:
        start_at = _infer_turkish_datetime_hint(
            " ".join(
                str(payload.get(key) or "")
                for key in ("time_hint", "source_excerpt", "title", "description")
            )
        )
    if start_at is None:
        return
    if start_at.tzinfo is None:
        start_at = start_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    if start_at <= now - timedelta(minutes=5):
        if start_at.year < now.year:
            start_at = start_at.replace(year=now.year)
        while start_at <= now - timedelta(minutes=5):
            start_at = start_at.replace(year=start_at.year + 1)

    end_at = _parse_datetime_or_none(payload.get("end_datetime"))
    if end_at is None or end_at <= start_at:
        end_at = start_at + timedelta(minutes=30)
    elif end_at.tzinfo is None:
        end_at = end_at.replace(tzinfo=timezone.utc)

    payload["proposed_datetime"] = start_at.isoformat()
    payload["end_datetime"] = end_at.isoformat()


def _infer_turkish_datetime_hint(text: str) -> datetime | None:
    normalized = text.casefold()
    if not normalized.strip():
        return None

    weekdays = {
        "pazartesi": 0,
        "salı": 1,
        "sali": 1,
        "çarşamba": 2,
        "carsamba": 2,
        "perşembe": 3,
        "persembe": 3,
        "cuma": 4,
        "cumartesi": 5,
        "pazar": 6,
    }
    matched_weekday = next((day for name, day in weekdays.items() if name in normalized), None)
    if matched_weekday is None:
        return None

    hour = 9
    minute = 0
    time_match = re.search(r"(?:saat\s*)?(\d{1,2})(?:[:.](\d{2}))?", normalized)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        if 0 <= hour <= 7:
            hour += 12
        if hour > 23 or minute > 59:
            return None

    now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3)))
    days_ahead = (matched_weekday - now.weekday()) % 7
    candidate = (now + timedelta(days=days_ahead)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    if candidate <= now:
        candidate += timedelta(days=7)
    return candidate


def _parse_datetime_or_none(value) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
