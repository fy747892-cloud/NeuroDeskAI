"""split ai chat and analysis quotas

Revision ID: 3fd8b9a7c2e1
Revises: 58e98d22e7ce
Create Date: 2026-07-21 20:35:00.000000
"""

from alembic import op


revision = "3fd8b9a7c2e1"
down_revision = "58e98d22e7ce"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        insert into usage_quotas (id, tenant_id, quota_type, limit_value, period, created_at, updated_at)
        select gen_random_uuid(), t.id, quota_type, 15, 'daily', now(), now()
        from tenants t
        cross join (values ('ai_chat_requests'), ('ai_analysis_requests')) as q(quota_type)
        on conflict (tenant_id, quota_type) do update
        set limit_value = greatest(usage_quotas.limit_value, 15),
            updated_at = now()
        """
    )
    op.execute(
        """
        update usage_quotas
        set limit_value = greatest(limit_value, 15),
            updated_at = now()
        where quota_type = 'ai_requests'
        """
    )


def downgrade() -> None:
    op.execute("delete from usage_quotas where quota_type in ('ai_chat_requests', 'ai_analysis_requests')")
