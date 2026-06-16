from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, LargeBinary, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    feed_sources = relationship("FeedSource", back_populates="category")
    articles = relationship("Article", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class FeedSource(Base):
    __tablename__ = "feed_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_fetched_at = Column(DateTime, nullable=True)

    # Relationships
    category = relationship("Category", back_populates="feed_sources")
    articles = relationship("Article", back_populates="feed_source")
    logs = relationship("IngestionLog", back_populates="feed_source")

    def __repr__(self):
        return f"<FeedSource(id={self.id}, name='{self.name}')>"


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    slug = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    content_html = Column(Text, nullable=True)
    link = Column(String(500), unique=True, nullable=False)
    guid = Column(String(500), unique=True, nullable=True)
    author = Column(String(255), nullable=True)
    published_date = Column(DateTime, nullable=False)
    fetched_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    feed_source_id = Column(Integer, ForeignKey("feed_sources.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    comment_count = Column(Integer, default=0)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(Integer, ForeignKey("articles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_title_date", "title", "published_date"),
        Index("idx_feed_source", "feed_source_id"),
        Index("idx_category", "category_id"),
        Index("idx_published_date", "published_date"),
    )

    # Relationships
    feed_source = relationship("FeedSource", back_populates="articles")
    category = relationship("Category", back_populates="articles")
    duplicates = relationship("Article", remote_side=[id], backref="duplicate_articles")

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...')>"


class IngestionLog(Base):
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    feed_source_id = Column(Integer, ForeignKey("feed_sources.id"), nullable=True)
    status = Column(String(20), nullable=False)  # success, failed, partial
    articles_fetched = Column(Integer, default=0)
    articles_saved = Column(Integer, default=0)
    duplicates_found = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_feed_source", "feed_source_id"),
        Index("idx_status", "status"),
        Index("idx_started_at", "started_at"),
    )

    # Relationships
    feed_source = relationship("FeedSource", back_populates="logs")

    def __repr__(self):
        return f"<IngestionLog(id={self.id}, status='{self.status}')>"
