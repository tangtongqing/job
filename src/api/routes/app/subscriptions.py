"""岗位订阅规则 CRUD。"""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.api.responses import NotFoundError, make_paginated
from src.db.models import Subscription
from src.db.session import get_db
from src.schemas.models import SubscriptionOut, SubscriptionPayload

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("")
def list_subscriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count(Subscription.id))) or 0
    subscriptions = db.scalars(
        select(Subscription)
        .order_by(Subscription.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return make_paginated(
        [SubscriptionOut.model_validate(item).model_dump() for item in subscriptions],
        page,
        page_size,
        total,
    )


@router.post("", status_code=201)
def create_subscription(payload: SubscriptionPayload, db: Session = Depends(get_db)):
    subscription = Subscription(**payload.model_dump())
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return {"data": SubscriptionOut.model_validate(subscription).model_dump()}


@router.put("/{subscription_id}")
def update_subscription(
    subscription_id: int,
    payload: SubscriptionPayload,
    db: Session = Depends(get_db),
):
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError(f"Subscription {subscription_id} not found")
    for key, value in payload.model_dump().items():
        setattr(subscription, key, value)
    db.commit()
    db.refresh(subscription)
    return {"data": SubscriptionOut.model_validate(subscription).model_dump()}


@router.delete("/{subscription_id}", status_code=204)
def delete_subscription(subscription_id: int, db: Session = Depends(get_db)):
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise NotFoundError(f"Subscription {subscription_id} not found")
    db.delete(subscription)
    db.commit()
    return Response(status_code=204)
