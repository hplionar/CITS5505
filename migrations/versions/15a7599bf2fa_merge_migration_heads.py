"""Merge migration heads

Revision ID: 15a7599bf2fa
Revises: 1c74515529f4, b7a1d3e9c4f2
Create Date: 2026-05-17 13:27:45.812656

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15a7599bf2fa'
down_revision = ('1c74515529f4', 'b7a1d3e9c4f2')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
