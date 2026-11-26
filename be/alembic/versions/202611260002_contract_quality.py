"""Add nullable evidence fields for Page/Block contract v1.1."""
from alembic import op
import sqlalchemy as sa

revision = "202611260002"
down_revision = "202611260001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("pages", sa.Column("rotation", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("is_handwritten", sa.Boolean(), nullable=True))
    op.add_column("blocks", sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column("blocks", sa.Column("coordinate_system", sa.String(32), nullable=True))
    op.add_column("blocks", sa.Column("heading_level", sa.Integer(), nullable=True))


def downgrade():
    for name in ("heading_level", "coordinate_system", "quality_score", "is_handwritten"):
        op.drop_column("blocks", name)
    op.drop_column("pages", "rotation")
