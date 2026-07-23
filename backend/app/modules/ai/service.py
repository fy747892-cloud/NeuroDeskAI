import time
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationAppError
from app.modules.ai.models import AIActionApproval, AIAnalysisJob
from app.modules.ai.provider import get_ai_provider
from app.modules.ai.repository import AIRepository
from app.modules.analytics.repository import AICostLogRepository
from app.modules.appointments.service import AppointmentService
from app.modules.billing.service import AI_ANALYSIS_REQUESTS_QUOTA_TYPE, BillingService
from app.modules.conversations.models import Call
from app.modules.conversations.repository import ConversationRepository
from app.modules.deals.service import DealService
from app.modules.tasks.service import TaskService


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
        has_items = any(
            bool(payload.get("items"))
            for payload in (output.tasks, output.appointments, output.deals)
            if isinstance(payload, dict)
        )
        if has_items:
            return output

        excerpt = " ".join(transcript_text.split())[:240]
        output.tasks["items"] = [
            {
                "title": f"Takip et: {title}",
                "description": excerpt
                or "AI analizi aksiyon üretmedi; görüşmeyi kontrol edip sonraki adımı belirle.",
                "priority": "medium",
                "reason": "Analiz tamamlandı ancak net aksiyon üretilemediği için takip görevi önerildi.",
                "confidence": 0.5,
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
