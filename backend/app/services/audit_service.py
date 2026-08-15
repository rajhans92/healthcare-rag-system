"""
Audit log service for healthcare RAG operations.

This keeps the application aligned with healthcare production requirements by
recording important user actions, retrieval requests, and access decisions.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog, AuditStatus


class AuditService:
    """
    Record high-value operations for traceability and compliance.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_event(
        self,
        *,
        user_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: UUID | None,
        status: str,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """
        Write an audit record for an important app event.
        """

        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=AuditStatus.SUCCESS if status == "SUCCESS" else AuditStatus.FAILED,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )

        self.session.add(log_entry)
        await self.session.flush()
        return log_entry
