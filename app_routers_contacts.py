from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models import Contact
from app.deps import get_db, require_role

router = APIRouter(prefix="/contacts", tags=["contacts"])


class ContactIn(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    tags: Optional[str] = None


class ContactOut(BaseModel):
    id: int
    name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    tags: Optional[str]

    class Config:
        from_attributes = True


@router.post(
    "",
    response_model=ContactOut,
    dependencies=[Depends(require_role("owner", "manager", "agent"))],
)
def create_contact(body: ContactIn, db: Session = Depends(get_db)) -> Contact:
    """Create a new contact."""
    obj = Contact(
        name=body.name, email=body.email, phone=body.phone, tags=body.tags
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get(
    "",
    response_model=List[ContactOut],
    dependencies=[Depends(require_role("owner", "manager", "agent"))],
)
def list_contacts(
    db: Session = Depends(get_db),
    q: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
) -> List[Contact]:
    """List contacts with optional search and pagination."""
    qs = db.query(Contact)
    if q:
        q_like = f"%{q}%"
        qs = qs.filter(
            (Contact.name.ilike(q_like))
            | (Contact.email.ilike(q_like))
            | (Contact.phone.ilike(q_like))
        )
    return (
        qs.order_by(Contact.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get(
    "/{contact_id}",
    response_model=ContactOut,
    dependencies=[Depends(require_role("owner", "manager", "agent"))],
)
def get_contact(contact_id: int, db: Session = Depends(get_db)) -> Contact:
    """Retrieve a contact by ID."""
    obj = db.query(Contact).get(contact_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return obj


@router.put(
    "/{contact_id}",
    response_model=ContactOut,
    dependencies=[Depends(require_role("owner", "manager"))],
)
def update_contact(
    contact_id: int, body: ContactIn, db: Session = Depends(get_db)
) -> Contact:
    """Update an existing contact."""
    obj = db.query(Contact).get(contact_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in body.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/{contact_id}",
    dependencies=[Depends(require_role("owner", "manager"))],
)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """Delete a contact."""
    obj = db.query(Contact).get(contact_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(obj)
    db.commit()
    return {"ok": True}