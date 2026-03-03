from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import AuditMixin


class Document(Base, AuditMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    # Cloudinary fields
    cloudinary_public_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    cloudinary_url: Mapped[str] = mapped_column(String(500), nullable=False)
    cloudinary_secure_url: Mapped[str] = mapped_column(String(500), nullable=False)

    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class DocumentLink(Base, AuditMixin):
    __tablename__ = "document_links"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    # Polymorphic link to any entity
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # invoice, bill, journal_entry, etc.
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
