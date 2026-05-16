"""Merge migration heads

Revision ID: 1c74515529f4
Revises: 42f01ca82d08, 9c0f3d2b8a1e
Create Date: 2026-05-16 22:42:20.111973

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c74515529f4'
down_revision = ('42f01ca82d08', '9c0f3d2b8a1e')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
