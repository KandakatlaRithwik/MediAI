"""add security question + hashed answer columns to users

Revision ID: a1b2c3d4e5f6
Revises: 981f2931f062
Create Date: 2026-06-25 09:00:00.000000

Adds two nullable columns on `users`:
  - security_question       (VARCHAR 255) - one of the predefined questions
  - security_answer_hash    (VARCHAR 255) - bcrypt hash of the answer

Kept nullable so this migration can be applied on top of an existing
database without breaking older rows; new registrations require both
fields at the API layer (enforced by Pydantic).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "981f2931f062"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("security_question", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("security_answer_hash", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "security_answer_hash")
    op.drop_column("users", "security_question")