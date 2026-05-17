"""Merge migration heads

Revision ID: 424b560a49cb
Revises: 1c74515529f4, b7a1d3e9c4f2
Create Date: 2026-05-17 12:55:02.423022

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '424b560a49cb'
down_revision = ('1c74515529f4', 'b7a1d3e9c4f2')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
