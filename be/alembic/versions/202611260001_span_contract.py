"""Add normalized spans without changing existing document data."""
from alembic import op
import sqlalchemy as sa

revision = "202611260001"
down_revision = "202606270001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "spans",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("document_id", sa.String(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("block_id", sa.String(), sa.ForeignKey("blocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parse_run_id", sa.String(), sa.ForeignKey("ocr_outputs.id", ondelete="CASCADE")),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("reading_order", sa.Integer(), nullable=False),
        sa.Column("span_type", sa.String(64), nullable=False),
        sa.Column("text", sa.Text()),
        sa.Column("bbox", sa.JSON()),
        sa.Column("coordinate_system", sa.String(32)),
        sa.Column("confidence", sa.Float()),
        sa.Column("raw_json", sa.JSON()),
        sa.UniqueConstraint("block_id", "reading_order", name="uq_span_block_order"),
    )
    op.create_index("ix_spans_document_id", "spans", ["document_id"])
    op.create_index("ix_spans_block_id", "spans", ["block_id"])
    op.create_index("ix_spans_id", "spans", ["id"])


def downgrade():
    op.drop_table("spans")
