from db.database import SessionLocal, engine
from models.base import Base, Category, FeedSource
import logging

logger = logging.getLogger(__name__)

# Feed sources data from the plan
CATEGORIES = [
    {"name": "Giải Trí", "slug": "giai-tri"},
    {"name": "Công Nghệ", "slug": "cong-nghe"},
    {"name": "Sức Khỏe", "slug": "suc-khoe"},
]

FEED_SOURCES = [
    # Entertainment
    {"name": "Vietnamnet - Giải Trí", "url": "https://vietnamnet.vn/rss/giai-tri.rss", "category_slug": "giai-tri"},
    {"name": "Thanh Niên - Giải Trí", "url": "https://thanhnien.vn/rss/giai-tri.rss", "category_slug": "giai-tri"},
    {"name": "Tuổi Trẻ - Giải Trí", "url": "https://tuoitre.vn/rss/giai-tri.rss", "category_slug": "giai-tri"},
    # Technology
    {"name": "Vietnamnet - Công Nghệ", "url": "https://vietnamnet.vn/rss/cong-nghe.rss", "category_slug": "cong-nghe"},
    {"name": "Thanh Niên - Công Nghệ", "url": "https://thanhnien.vn/rss/cong-nghe.rss", "category_slug": "cong-nghe"},
    {"name": "Tuổi Trẻ - Nhịp Sống Số", "url": "https://tuoitre.vn/rss/nhip-song-so.rss", "category_slug": "cong-nghe"},
    # Health
    {"name": "Vietnamnet - Sức Khỏe", "url": "https://vietnamnet.vn/rss/suc-khoe.rss", "category_slug": "suc-khoe"},
    {"name": "Thanh Niên - Sức Khỏe", "url": "https://thanhnien.vn/rss/suc-khoe.rss", "category_slug": "suc-khoe"},
    {"name": "Tuổi Trẻ - Sức Khỏe", "url": "https://tuoitre.vn/rss/suc-khoe.rss", "category_slug": "suc-khoe"},
]


def init_db():
    """Initialize database - create tables and seed data"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Seed data
    db = SessionLocal()
    try:
        # Check if data already exists
        existing_categories = db.query(Category).count()
        if existing_categories == 0:
            # Add categories
            for cat_data in CATEGORIES:
                category = Category(**cat_data)
                db.add(category)
            db.commit()
            logger.info("Categories seeded")

            # Add feed sources
            for feed_data in FEED_SOURCES:
                category_slug = feed_data.pop("category_slug")
                category = db.query(Category).filter(Category.slug == category_slug).first()
                if category:
                    feed_source = FeedSource(**feed_data, category_id=category.id)
                    db.add(feed_source)
            db.commit()
            logger.info("Feed sources seeded")
        else:
            logger.info("Database already initialized with data")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    print("Database initialized successfully!")
