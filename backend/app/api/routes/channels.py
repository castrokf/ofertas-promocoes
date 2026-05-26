from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, require_admin
from app.models import ChannelType, PublishChannel
from app.schemas import PublishChannelCreate, PublishChannelRead


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[PublishChannelRead])
def list_channels(db: DbSession):
    return db.scalars(select(PublishChannel).order_by(PublishChannel.name)).all()


@router.post("", response_model=PublishChannelRead)
def create_channel(payload: PublishChannelCreate, db: DbSession):
    if db.scalar(select(PublishChannel).where(PublishChannel.name == payload.name)):
        raise HTTPException(status_code=409, detail="Channel already exists")
    channel = PublishChannel(
        name=payload.name,
        channel_type=ChannelType(payload.channel_type),
        config=payload.config,
        is_active=payload.is_active,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel
