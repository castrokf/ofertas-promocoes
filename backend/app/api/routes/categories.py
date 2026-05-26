from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, require_admin
from app.models import Category
from app.schemas import CategoryCreate, CategoryRead


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[CategoryRead])
def list_categories(db: DbSession):
    return db.scalars(select(Category).order_by(Category.name)).all()


@router.post("", response_model=CategoryRead)
def create_category(payload: CategoryCreate, db: DbSession):
    if db.scalar(select(Category).where(Category.slug == payload.slug)):
        raise HTTPException(status_code=409, detail="Category already exists")
    category = Category(
        name=payload.name,
        slug=payload.slug,
        min_discount_percent=payload.min_discount_percent,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
