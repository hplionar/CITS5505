"""Add user profile settings columns

Revision ID: 9c0f3d2b8a1e
Revises: 68df065c47eb
Create Date: 2026-05-15 11:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9c0f3d2b8a1e"
down_revision = "68df065c47eb"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("bio", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "notify_study_messages",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "notify_session_reminders",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "notify_announcements",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("preferred_study_mode", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("preferred_location", sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column("interested_units", sa.String(length=255), nullable=True))
        batch_op.add_column(
            sa.Column(
                "show_full_name",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "show_joined_sessions",
                sa.Boolean(),
                server_default=sa.false(),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "show_saved_sessions",
                sa.Boolean(),
                server_default=sa.false(),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "allow_profile_discovery",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
            )
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("allow_profile_discovery")
        batch_op.drop_column("show_saved_sessions")
        batch_op.drop_column("show_joined_sessions")
        batch_op.drop_column("show_full_name")
        batch_op.drop_column("interested_units")
        batch_op.drop_column("preferred_location")
        batch_op.drop_column("preferred_study_mode")
        batch_op.drop_column("notify_announcements")
        batch_op.drop_column("notify_session_reminders")
        batch_op.drop_column("notify_study_messages")
        batch_op.drop_column("bio")
