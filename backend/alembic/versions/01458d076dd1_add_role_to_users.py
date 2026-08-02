"""add role to users

Revision ID: 01458d076dd1
Revises: 6cdcceae8480
Create Date: 2026-08-02 07:36:47.025510

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '01458d076dd1'
down_revision: Union[str, None] = '6cdcceae8480'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default is required here for the same reason as the
    # tech_stack migration before it (see that file's comment): this
    # ALTER TABLE runs against a users table that may already have
    # real rows, and Postgres needs a value to backfill them with to
    # satisfy NOT NULL. Every existing user becomes USER, never ADMIN
    # -- promoting an account to ADMIN is always a separate, deliberate
    # action (see README), never an accidental side effect of a schema
    # migration.
    op.add_column(
        'users',
        sa.Column('role', sa.String(length=20), nullable=False, server_default='USER'),
    )


def downgrade() -> None:
    op.drop_column('users', 'role')