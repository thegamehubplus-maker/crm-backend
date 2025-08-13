"""Database session and engine configuration.

This module provides a configured SQLAlchemy engine and a
``SessionLocal`` factory for creating database sessions. The database
URL is read from the ``DATABASE_URL`` environment variable, which
should be in the form accepted by SQLAlchemy, for example:
``postgresql+psycopg://user:password@host:port/dbname``. The engine
is configured with ``pool_pre_ping=True`` to ensure connections are
checked for liveness before each checkout, helping to avoid using
stale connections from the pool.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Retrieve the database URL from the environment. When deploying to
# Render or another platform, ensure this environment variable is set.
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the SQLAlchemy engine. ``pool_pre_ping=True`` makes the
# connection pool test connections before handing them out, which
# mitigates issues with dropped connections in long‑running
# applications.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Configure a session factory. ``autoflush`` and ``autocommit`` are
# disabled to give the developer explicit control over transaction
# boundaries. Use ``SessionLocal()`` to obtain a new session in your
# application code.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
