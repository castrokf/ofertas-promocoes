from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import DbSession, require_admin
from app.models import AlertRule
from app.schemas import AlertRuleCreate, AlertRuleRead


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[AlertRuleRead])
def list_rules(db: DbSession):
    return db.scalars(select(AlertRule).order_by(AlertRule.created_at.desc())).all()


@router.post("", response_model=AlertRuleRead)
def create_rule(payload: AlertRuleCreate, db: DbSession):
    rule = AlertRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
