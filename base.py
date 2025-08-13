"""SQLAlchemy declarative base.

This module defines the base class for SQLAlchemy models. All ORM
models in the application should inherit from ``Base``. Using a
centralized base class makes it straightforward for Alembic to
discover model metadata for automatic migrations.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Subclassing from ``DeclarativeBase`` enables SQLAlchemy's
    declarative system, allowing models to be defined as plain Python
    classes. This class doesn't define any additional behaviour
    itself but serves as the common ancestor for all tables.
    """

    pass
