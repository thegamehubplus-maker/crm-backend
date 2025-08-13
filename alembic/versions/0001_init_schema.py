"""Initial CRM schema.

Revision ID: 0001
Revises: 
Create Date: 2025-08-13

This revision creates the foundational tables for the CRM application,
including contacts, products, variants, orders, order items,
interactions, payments, tasks, aggregated customer statistics and a
general event log. It also introduces composite indexes to optimise
common query patterns involving contact identifiers, statuses and
timestamps.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the CRM schema."""
    # ### Create contacts table ###
    op.create_table(
        'contacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phone', sa.String(length=64), nullable=True),
        sa.Column('email', sa.String(length=256), nullable=True),
        sa.Column('name', sa.String(length=256), nullable=True),
        sa.Column('tags', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_contacts_phone', 'contacts', ['phone'], unique=False)
    op.create_index('ix_contacts_email', 'contacts', ['email'], unique=False)
    op.create_index('ix_contacts_created_at', 'contacts', ['created_at'], unique=False)

    # ### Create products table ###
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(length=64), nullable=True),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_products_sku', 'products', ['sku'], unique=False)
    op.create_index('ix_products_title', 'products', ['title'], unique=False)
    op.create_index('ix_products_created_at', 'products', ['created_at'], unique=False)

    # ### Create variants table ###
    op.create_table(
        'variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('price', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_variants_product_id', 'variants', ['product_id'], unique=False)
    op.create_index('ix_variants_created_at', 'variants', ['created_at'], unique=False)

    # ### Create orders table ###
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('total', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_orders_contact_id', 'orders', ['contact_id'], unique=False)
    op.create_index('ix_orders_status', 'orders', ['status'], unique=False)
    op.create_index('ix_orders_created_at', 'orders', ['created_at'], unique=False)
    # Composite index for contact_id, status, created_at
    op.create_index(
        'ix_orders_contact_status_created',
        'orders',
        ['contact_id', 'status', 'created_at'],
        unique=False,
    )

    # ### Create order_items table ###
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('variant_id', sa.Integer(), nullable=False),
        sa.Column('qty', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('price', sa.Numeric(12, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'], unique=False)
    op.create_index('ix_order_items_created_at', 'order_items', ['created_at'], unique=False)

    # ### Create interactions table ###
    op.create_table(
        'interactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.String(length=32), nullable=False),
        sa.Column('direction', sa.String(length=16), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('external_event_id', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_interactions_contact_id', 'interactions', ['contact_id'], unique=False)
    op.create_index('ix_interactions_external_event_id', 'interactions', ['external_event_id'], unique=False)
    op.create_index('ix_interactions_created_at', 'interactions', ['created_at'], unique=False)
    # Composite index for contact_id and created_at
    op.create_index(
        'ix_interactions_contact_created',
        'interactions',
        ['contact_id', 'created_at'],
        unique=False,
    )

    # ### Create payments table ###
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('provider', sa.String(length=64), nullable=True),
        sa.Column('tx_id', sa.String(length=128), nullable=True),
        sa.Column('fee', sa.Numeric(12, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_payments_order_id', 'payments', ['order_id'], unique=False)
    op.create_index('ix_payments_status', 'payments', ['status'], unique=False)
    op.create_index('ix_payments_tx_id', 'payments', ['tx_id'], unique=False)
    op.create_index('ix_payments_created_at', 'payments', ['created_at'], unique=False)
    # Composite index for status and created_at
    op.create_index(
        'ix_payments_status_created',
        'payments',
        ['status', 'created_at'],
        unique=False,
    )

    # ### Create tasks table ###
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('due_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tasks_contact_id', 'tasks', ['contact_id'], unique=False)
    op.create_index('ix_tasks_status', 'tasks', ['status'], unique=False)
    op.create_index('ix_tasks_due_at', 'tasks', ['due_at'], unique=False)
    op.create_index('ix_tasks_created_at', 'tasks', ['created_at'], unique=False)

    # ### Create customer_stats table ###
    op.create_table(
        'customer_stats',
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('orders_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ltv', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('last_order_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id']),
        sa.PrimaryKeyConstraint('contact_id'),
    )
    op.create_index('ix_customer_stats_orders_count', 'customer_stats', ['orders_count'], unique=False)
    op.create_index('ix_customer_stats_last_order_at', 'customer_stats', ['last_order_at'], unique=False)

    # ### Create event_log table ###
    op.create_table(
        'event_log',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_event_log_event_type', 'event_log', ['event_type'], unique=False)
    op.create_index('ix_event_log_created_at', 'event_log', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop all CRM tables and indexes."""
    # Drop tables in reverse dependency order
    op.drop_table('event_log')
    op.drop_table('customer_stats')
    op.drop_table('tasks')
    op.drop_table('payments')
    op.drop_table('interactions')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('variants')
    op.drop_table('products')
    op.drop_table('contacts')
