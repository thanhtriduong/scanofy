from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class Block(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "blocks"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_id: Mapped[str | None] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), nullable=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    block_type: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    bbox: Mapped[list | None] = mapped_column(JSON, nullable=True)
    reading_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    correction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_engine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="blocks")
    spans = relationship("Span", back_populates="block", cascade="all, delete-orphan")
    page = relationship("Page", back_populates="blocks")
