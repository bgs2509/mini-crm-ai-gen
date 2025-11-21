"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2025-11-20 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('default_currency', sa.String(length=3), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_created_at'), 'organizations', ['created_at'], unique=False)

    # Create organization_members table
    op.create_table(
        'organization_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_organization_member')
    )
    op.create_index(op.f('ix_organization_members_created_at'), 'organization_members', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_members_organization_id'), 'organization_members', ['organization_id'], unique=False)
    op.create_index(op.f('ix_organization_members_user_id'), 'organization_members', ['user_id'], unique=False)

    # Create contacts table
    op.create_table(
        'contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contacts_created_at'), 'contacts', ['created_at'], unique=False)
    op.create_index(op.f('ix_contacts_email'), 'contacts', ['email'], unique=False)
    op.create_index(op.f('ix_contacts_name'), 'contacts', ['name'], unique=False)
    op.create_index(op.f('ix_contacts_organization_id'), 'contacts', ['organization_id'], unique=False)
    op.create_index(op.f('ix_contacts_owner_id'), 'contacts', ['owner_id'], unique=False)

    # Create deals table
    op.create_table(
        'deals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('stage', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deals_amount'), 'deals', ['amount'], unique=False)
    op.create_index(op.f('ix_deals_contact_id'), 'deals', ['contact_id'], unique=False)
    op.create_index(op.f('ix_deals_created_at'), 'deals', ['created_at'], unique=False)
    op.create_index(op.f('ix_deals_organization_id'), 'deals', ['organization_id'], unique=False)
    op.create_index(op.f('ix_deals_owner_id'), 'deals', ['owner_id'], unique=False)
    op.create_index(op.f('ix_deals_stage'), 'deals', ['stage'], unique=False)
    op.create_index(op.f('ix_deals_status'), 'deals', ['status'], unique=False)
    op.create_index(op.f('ix_deals_title'), 'deals', ['title'], unique=False)

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('is_done', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_created_at'), 'tasks', ['created_at'], unique=False)
    op.create_index(op.f('ix_tasks_deal_id'), 'tasks', ['deal_id'], unique=False)
    op.create_index(op.f('ix_tasks_due_date'), 'tasks', ['due_date'], unique=False)
    op.create_index(op.f('ix_tasks_is_done'), 'tasks', ['is_done'], unique=False)

    # Create activities table
    op.create_table(
        'activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activities_author_id'), 'activities', ['author_id'], unique=False)
    op.create_index(op.f('ix_activities_created_at'), 'activities', ['created_at'], unique=False)
    op.create_index(op.f('ix_activities_deal_id'), 'activities', ['deal_id'], unique=False)
    op.create_index(op.f('ix_activities_type'), 'activities', ['type'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_activities_type'), table_name='activities')
    op.drop_index(op.f('ix_activities_deal_id'), table_name='activities')
    op.drop_index(op.f('ix_activities_created_at'), table_name='activities')
    op.drop_index(op.f('ix_activities_author_id'), table_name='activities')
    op.drop_table('activities')

    op.drop_index(op.f('ix_tasks_is_done'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_due_date'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_deal_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_created_at'), table_name='tasks')
    op.drop_table('tasks')

    op.drop_index(op.f('ix_deals_title'), table_name='deals')
    op.drop_index(op.f('ix_deals_status'), table_name='deals')
    op.drop_index(op.f('ix_deals_stage'), table_name='deals')
    op.drop_index(op.f('ix_deals_owner_id'), table_name='deals')
    op.drop_index(op.f('ix_deals_organization_id'), table_name='deals')
    op.drop_index(op.f('ix_deals_created_at'), table_name='deals')
    op.drop_index(op.f('ix_deals_contact_id'), table_name='deals')
    op.drop_index(op.f('ix_deals_amount'), table_name='deals')
    op.drop_table('deals')

    op.drop_index(op.f('ix_contacts_owner_id'), table_name='contacts')
    op.drop_index(op.f('ix_contacts_organization_id'), table_name='contacts')
    op.drop_index(op.f('ix_contacts_name'), table_name='contacts')
    op.drop_index(op.f('ix_contacts_email'), table_name='contacts')
    op.drop_index(op.f('ix_contacts_created_at'), table_name='contacts')
    op.drop_table('contacts')

    op.drop_index(op.f('ix_organization_members_user_id'), table_name='organization_members')
    op.drop_index(op.f('ix_organization_members_organization_id'), table_name='organization_members')
    op.drop_index(op.f('ix_organization_members_created_at'), table_name='organization_members')
    op.drop_table('organization_members')

    op.drop_index(op.f('ix_organizations_created_at'), table_name='organizations')
    op.drop_table('organizations')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_created_at'), table_name='users')
    op.drop_table('users')
