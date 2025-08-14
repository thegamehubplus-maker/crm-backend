"""Database models for the CRM application.

This module defines the SQLAlchemy ORM models representing the core
entities of the CRM system. Each model corresponds to a table in
PostgreSQL and includes appropriate indexes to optimise common
queries. The models are intentionally minimal at this stage, focusing
on primary identifiers and a handful of useful attributes. Fields
which can be absent (e.g. optional strings) are marked as nullable.
"""

from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------
class Contact(Base):
    """Represents an end user or lead interacting with the business."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str | None] = mapped_column(String(64), index=True)
    email: Mapped[str | None] = mapped_column(String(256), index=True)
    name: Mapped[str | None] = mapped_column(String(256))
    tags: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


# ---------------------------------------------------------------------------
# Products and Variants
# ---------------------------------------------------------------------------
class Product(Base):
    """Represents a sellable product in the catalogue."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str | None] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class Variant(Base):
    """Represents a specific variation of a product with its own price."""

    __tablename__ = "variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(256))
    price: Mapped[Numeric] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------
class Order(Base):
    """Represents an order placed by a contact for one or more products."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)  # new/waiting/paid/etc
    total: Mapped[Numeric] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


Index(
    "ix_orders_contact_status_created",
    Order.contact_id,
    Order.status,
    Order.created_at.desc(),
)


class OrderItem(Base):
    """Represents an individual line item within an order."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    variant_id: Mapped[int] = mapped_column(ForeignKey("variants.id"))
    qty: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[Numeric] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


# ---------------------------------------------------------------------------
# Interactions
# ---------------------------------------------------------------------------
class Interaction(Base):
    """Represents a conversation, message, call or other interaction with a contact."""

    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), index=True)
    channel: Mapped[str] = mapped_column(String(32))  # e.g., telegram, avito
    direction: Mapped[str] = mapped_column(String(16))  # in/out
    message: Mapped[str | None] = mapped_column(Text)
    external_event_id: Mapped[str | None] = mapped_column(
        String(128), index=True
    )  # deduplication
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


Index(
    "ix_interactions_contact_created",
    Interaction.contact_id,
    Interaction.created_at.desc(),
)


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------
class Payment(Base):
    """Represents a payment associated with an order."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)  # pending/paid/etc
    amount: Mapped[Numeric] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8))
    provider: Mapped[str | None] = mapped_column(String(64))
    tx_id: Mapped[str | None] = mapped_column(String(128), index=True)
    fee: Mapped[Numeric | None] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


Index(
    "ix_payments_status_created",
    Payment.status,
    Payment.created_at.desc(),
)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
class Task(Base):
    """Represents a task or reminder for follow‑up actions with contacts."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("contacts.id"), index=True
    )
    type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), index=True)  # open/done
    due_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


# ---------------------------------------------------------------------------
# Customer statistics
# ---------------------------------------------------------------------------
class CustomerStats(Base):
    """Aggregated metrics about a contact, such as total orders and lifetime value."""

    __tablename__ = "customer_stats"

    contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.id"), primary_key=True
    )
    orders_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    ltv: Mapped[Numeric] = mapped_column(Numeric(14, 2), default=0)
    last_order_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)


# ---------------------------------------------------------------------------
# Event log
# ---------------------------------------------------------------------------
class EventLog(Base):
    """Generic event log for auditing and tracking system events."""

    __tablename__ = "event_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

# ---------------------------------------------------------------------------
# Users and Idempotency Keys
# ---------------------------------------------------------------------------
class User(Base):
    """Represents a user of the CRM system with a role and credentials."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(16), index=True)  # owner/manager/agent
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class IdempotencyKey(Base):
    """Stores request/response pairs to support idempotent write operations."""

    __tablename__ = "idempotency_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(128), index=True)
    method: Mapped[str] = mapped_column(String(8))
    path: Mapped[str] = mapped_column(String(512))
    body_hash: Mapped[str | None] = mapped_column(String(64))  # sha256
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[dict | None] = mapped_column(JSONB)  # save response
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


# speed up lookup by key, method and path
Index(
    "ix_idem_key_method_path",
    IdempotencyKey.key,
    IdempotencyKey.method,
    IdempotencyKey.path,
)
