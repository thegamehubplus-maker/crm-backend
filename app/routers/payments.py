from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Payment, Order
from app.deps import get_db, require_role

router = APIRouter(prefix="/payments", tags=["payments"])

class PaymentCreateIn(BaseModel):
    order_id: int
    amount: Decimal
    currency: str
    provider: Optional[str] = None
    status: str = "paid"  # для тестов

class PaymentUpdateIn(BaseModel):
    status: Optional[str] = None
    tx_id: Optional[str] = None
    fee: Optional[Decimal] = None

@router.post("", dependencies=[Depends(require_role("owner","manager","agent"))])
def create_payment(body: PaymentCreateIn, db: Session = Depends(get_db)):
    o = db.query(Order).get(body.order_id)
    if not o: raise HTTPException(404, "Order not found")

    p = Payment(
        order_id=body.order_id,
        amount=body.amount,
        currency=body.currency,
        provider=body.provider,
        status=body.status,
    )
    db.add(p)
    # если платёж успешен — переведём заказ в paid (для MVP)
    if body.status == "paid":
        o.status = "paid"
    db.commit(); db.refresh(p); db.refresh(o)

    return {
        "id": p.id, "order_id": p.order_id, "status": p.status, "amount": str(p.amount),
        "currency": p.currency, "provider": p.provider, "tx_id": p.tx_id, "fee": str(p.fee) if p.fee is not None else None
    }

@router.get("", dependencies=[Depends(require_role("owner","manager","agent"))])
def list_payments(
    db: Session = Depends(get_db),
    order_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0
):
    q = db.query(Payment)
    if order_id: q = q.filter(Payment.order_id == order_id)
    if status: q = q.filter(Payment.status == status)
    res = q.order_by(Payment.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {"id": p.id, "order_id": p.order_id, "status": p.status, "amount": str(p.amount), "currency": p.currency, "provider": p.provider, "created_at": p.created_at}
        for p in res
    ]

@router.put("/{payment_id}", dependencies=[Depends(require_role("owner","manager"))])
def update_payment(payment_id: int, body: PaymentUpdateIn, db: Session = Depends(get_db)):
    p = db.query(Payment).get(payment_id)
    if not p: raise HTTPException(404, "Payment not found")
    if body.status: p.status = body.status
    if body.tx_id: p.tx_id = body.tx_id
    if body.fee is not None: p.fee = body.fee
    db.commit(); db.refresh(p)
    return {"id": p.id, "status": p.status, "tx_id": p.tx_id, "fee": str(p.fee) if p.fee is not None else None}
