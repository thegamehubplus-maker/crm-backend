from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.models import User
from app.auth import hash_password, verify_password, create_token
from app.deps import get_db, require_role

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    role: str  # owner/manager/agent


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(
    body: RegisterIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("owner")),
):
    """Register a new user. Only users with the 'owner' role can create users."""
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    """Authenticate user and return a JWT token."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user.id, user.email, user.role)
    return {"access_token": token, "token_type": "bearer"}