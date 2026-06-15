from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import ChatMessage, ExportArtifact, WizardSession


async def cleanup_expired_sessions(db: AsyncSession) -> int:
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.session_retention_days)
    result = await db.execute(
        select(WizardSession.id).where(WizardSession.updated_at < cutoff)
    )
    session_ids = [row[0] for row in result.all()]
    if not session_ids:
        return 0

    await db.execute(delete(ChatMessage).where(ChatMessage.session_id.in_(session_ids)))
    await db.execute(delete(ExportArtifact).where(ExportArtifact.session_id.in_(session_ids)))
    await db.execute(delete(WizardSession).where(WizardSession.id.in_(session_ids)))
    await db.commit()
    return len(session_ids)
