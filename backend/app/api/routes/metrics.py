from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.api.deps import DbSession, require_admin
from app.models import Category, Deal, DealStatus, Product, Publication, Store
from app.schemas import MetricsSummary
from app.services.deal_pipeline import avg_discount


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/summary", response_model=MetricsSummary)
def summary(db: DbSession):
    deals_by_store = db.execute(
        select(Store.name, func.count(Deal.id))
        .join(Product, Product.store_id == Store.id)
        .join(Deal, Deal.product_id == Product.id)
        .group_by(Store.name)
    ).all()
    deals_by_category = db.execute(
        select(Category.name, func.count(Deal.id))
        .join(Product, Product.category_id == Category.id)
        .join(Deal, Deal.product_id == Product.id)
        .group_by(Category.name)
    ).all()
    return MetricsSummary(
        total_products=db.scalar(select(func.count(Product.id))) or 0,
        total_deals=db.scalar(select(func.count(Deal.id))) or 0,
        total_publications=db.scalar(select(func.count(Publication.id))) or 0,
        published_deals=db.scalar(select(func.count(Deal.id)).where(Deal.status == DealStatus.published)) or 0,
        avg_discount=avg_discount(db),
        deals_by_store=[{"store": name, "count": count} for name, count in deals_by_store],
        deals_by_category=[{"category": name, "count": count} for name, count in deals_by_category],
    )
