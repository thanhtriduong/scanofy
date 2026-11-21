from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class OCROutput(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ocr_outputs"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    engine: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    markdown_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    average_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="ocr_outputs")
