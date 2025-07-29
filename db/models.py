from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Date, DateTime, Text, Index, UniqueConstraint

class Base(DeclarativeBase):
    pass

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    category: Mapped[str | None] = mapped_column(String(64))
    serial_no: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(Text)

    page_url: Mapped[str | None] = mapped_column(Text)
    doc_url: Mapped[str | None] = mapped_column(Text)
    download_url: Mapped[str | None] = mapped_column(Text)

    file_type: Mapped[str | None] = mapped_column(String(16))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)

    published_date: Mapped[datetime | None] = mapped_column(Date)
    updated_date: Mapped[datetime | None] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    content_hash: Mapped[str | None] = mapped_column(String(64))

    __table_args__ = (
        UniqueConstraint("title", "doc_url", name="uq_title_docurl"),
        Index("ix_category_date", "category", "published_date"),
    )