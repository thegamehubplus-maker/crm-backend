from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, conint
from typing import List, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from app.db.session import SessionLocal
from app.db.models import Order, OrderItem
from app.deps import get_db, require_role

router = APIRouter(prefix="/orders", tags=["orders"])

class OrderItemIn(BaseModel):
    product_id: int
    variant_id: int
    qty: conint(ge=1) = 1
    price: Decimal
    currency: str

class OrderCreateIn(BaseModel):
    contact_id: int
    currency: str
    items: List[OrderItemIn]

class OrderUpdateIn(BaseModel):
    status: Optional[str] = None
    total: Optional[Decimal] = None
    currency: Optional[str] = None

def calc_total(items: List[OrderItemIn]) -> Decimal:
    return sum((i.price * i.qty for i in items), Decimal("0.00"))

@router.post("", dependencies=[Depends(require_role("owner","manager","agent"))])
def create_order(body: OrderCreateIn, db: Session = Depends(get_db)):
    total = calc_total(body.items)
    order = Order(
        contact_id=body.contact_id,
        status="new",
        total=total,
        currency=body.currency,
    )
    db.add(order)
    db.flush()  # получим order.id до commit

    for it in body.items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=it.product_id,
            variant_id=it.variant_id,
            qty=it.qty,
            price=it.price,
        ))

    db.commit()
    db.refresh(order)
    return {"id": order.id, "status": order.status, "total": str(order.total), "currency": order.currency}

@router.get("", dependencies=[Depends(require_role("owner","manager","agent"))])
def list_orders(
    db: Session = Depends(get_db),
    contact_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0
):
    q = db.query(Order)
    if contact_id: q = q.filter(Order.contact_id == contact_id)
    if status: q = q.filter(Order.status == status)
    res = q.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {"id": o.id, "contact_id": o.contact_id, "status": o.status, "total": str(o.total), "currency": o.currency, "created_at": o.created_at}
        for o in res
    ]

@router.get("/{order_id}", dependencies=[Depends(require_role("owner","manager","agent"))])
def get_order(order_id: int, db: Session = Depends(get_db)):
    o = db.query(Order).get(order_id)
    if not o: raise HTTPException(404, "Order not found")
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    return {
        "id": o.id, "contact_id": o.contact_id, "status": o.status,
        "total": str(o.total), "currency": o.currency, "created_at": o.created_at,
        "items": [{"id": it.id, "product_id": it.product_id, "variant_id": it.variant_id, "qty": it.qty, "price": str(it.price)} for it in items]
    }

@router.put("/{order_id}", dependencies=[Depends(require_role("owner","manager"))])
def update_order(order_id: int, body: OrderUpdateIn, db: Session = Depends(get_db)):
    o = db.query(Order).get(order_id)
    if not o: raise HTTPException(404, "Order not found")
    changed = False
    if body.status: o.status = body.status; changed = True
    if body.total is not None: o.total = body.total; changed = True
    if body.currency: o.currency = body.currency; changed = True
    if changed:
        db.commit()
        db.refresh(o)
    return {"id": o.id, "status": o.status, "total": str(o.total), "currency": o.currency}
