from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class Span(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "spans"
    __table_args__ = (UniqueConstraint("block_id", "reading_order", name="uq_span_block_order"),)

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    block_id: Mapped[str] = mapped_column(ForeignKey("blocks.id", ondelete="CASCADE"), index=True)
    parse_run_id: Mapped[str | None] = mapped_column(ForeignKey("ocr_outputs.id", ondelete="CASCADE"), nullable=True)
    page_number: Mapped[int] = mapped_column(Integer)
    reading_order: Mapped[int] = mapped_column(Integer)
    span_type: Mapped[str] = mapped_column(String(64))
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    bbox: Mapped[list | None] = mapped_column(JSON, nullable=True)
    coordinate_system: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    block = relationship("Block", back_populates="spans")
