from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class Page(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("document_id", "page_number", name="uq_pages_document_page"),)

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[float | None] = mapped_column(Float, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    rotation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="pages")
    blocks = relationship("Block", back_populates="page", cascade="all, delete-orphan")
