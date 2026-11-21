from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    user_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    storage_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded", index=True)
    profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    router_decision: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    jobs = relationship("DocumentJob", back_populates="document", cascade="all, delete-orphan")
    ocr_outputs = relationship("OCROutput", back_populates="document", cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    blocks = relationship("Block", back_populates="document", cascade="all, delete-orphan")
    tree_nodes = relationship("DocumentTreeNode", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    generated_features = relationship(
        "GeneratedFeature",
        back_populates="document",
        cascade="all, delete-orphan",
    )
