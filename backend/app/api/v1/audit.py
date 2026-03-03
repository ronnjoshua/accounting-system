from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.core.dependencies import require_accountant, require_viewer
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse, AuditLogCreate

router = APIRouter()


def create_audit_log(
    db: Session,
    user_id: Optional[int],
    user_email: Optional[str],
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    description: Optional[str] = None
):
    """Helper function to create audit log entries"""
    audit_log = AuditLog(
        user_id=user_id,
        user_email=user_email,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
        description=description
    )
    db.add(audit_log)
    return audit_log


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    query = select(AuditLog)

    if action:
        query = query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if start_date:
        query = query.where(AuditLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.where(AuditLog.timestamp <= datetime.combine(end_date, datetime.max.time()))

    query = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
    result = db.execute(query)
    return result.scalars().all()


@router.get("/summary")
def get_audit_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    """Get summary of audit activities"""
    base_query = select(AuditLog)

    if start_date:
        base_query = base_query.where(AuditLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        base_query = base_query.where(AuditLog.timestamp <= datetime.combine(end_date, datetime.max.time()))

    # Count by action
    action_counts = {}
    for action in ["create", "update", "delete", "login", "logout", "post", "void"]:
        count_query = select(func.count(AuditLog.id)).where(AuditLog.action == action)
        if start_date:
            count_query = count_query.where(AuditLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            count_query = count_query.where(AuditLog.timestamp <= datetime.combine(end_date, datetime.max.time()))
        result = db.execute(count_query)
        count = result.scalar() or 0
        if count > 0:
            action_counts[action] = count

    # Count by entity type
    entity_counts = {}
    entity_types = ["invoice", "bill", "journal_entry", "customer", "vendor", "product", "account", "user"]
    for entity_type in entity_types:
        count_query = select(func.count(AuditLog.id)).where(AuditLog.entity_type == entity_type)
        if start_date:
            count_query = count_query.where(AuditLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            count_query = count_query.where(AuditLog.timestamp <= datetime.combine(end_date, datetime.max.time()))
        result = db.execute(count_query)
        count = result.scalar() or 0
        if count > 0:
            entity_counts[entity_type] = count

    # Total count
    total_query = select(func.count(AuditLog.id))
    if start_date:
        total_query = total_query.where(AuditLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        total_query = total_query.where(AuditLog.timestamp <= datetime.combine(end_date, datetime.max.time()))
    total = db.execute(total_query).scalar() or 0

    # Recent activity
    recent_query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10)
    recent = db.execute(recent_query).scalars().all()

    return {
        "total_entries": total,
        "by_action": action_counts,
        "by_entity": entity_counts,
        "recent_activity": [
            {
                "timestamp": log.timestamp.isoformat(),
                "user_email": log.user_email,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "description": log.description
            }
            for log in recent
        ]
    }


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
def get_entity_history(
    entity_type: str,
    entity_id: int,
    current_user: User = Depends(require_viewer),
    db: Session = Depends(get_db)
):
    """Get audit history for a specific entity"""
    query = select(AuditLog).where(
        and_(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id
        )
    ).order_by(AuditLog.timestamp.desc())

    result = db.execute(query)
    return result.scalars().all()


@router.get("/{audit_id}", response_model=AuditLogResponse)
def get_audit_log(
    audit_id: int,
    current_user: User = Depends(require_accountant),
    db: Session = Depends(get_db)
):
    result = db.execute(select(AuditLog).where(AuditLog.id == audit_id))
    audit_log = result.scalar_one_or_none()
    if not audit_log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return audit_log
