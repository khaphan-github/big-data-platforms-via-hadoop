import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import settings
from db.database import SessionLocal, engine
from models.base import FeedSource, Article, IngestionLog
from services.rss_fetcher import RSSFetcher
from services.content_crawler import ContentCrawler
from services.deduplicator import Deduplicator
from services.data_processor import DataProcessor
from utils.logger import setup_logger

logger = setup_logger(__name__)


class IngestionScheduler:
    """Handle scheduled RSS ingestion"""

    def __init__(self):
        self.fetcher = None
        self.crawler = None
        self.is_running = False
        self.scheduler = None

    async def ingest_all_feeds(self):
        """Main ingestion job - fetch and process all feeds"""
        logger.info("=" * 50)
        logger.info("Starting RSS ingestion cycle")
        logger.info("=" * 50)

        start_time = datetime.utcnow()
        db = SessionLocal()

        try:
            # Initialize fetcher and crawler
            self.fetcher = RSSFetcher()
            self.crawler = ContentCrawler()

            # Get all active feed sources
            feed_sources = db.query(FeedSource).filter(FeedSource.is_active == True).all()
            logger.info(f"Found {len(feed_sources)} active feed sources")

            total_fetched = 0
            total_saved = 0
            total_duplicates = 0

            # Fetch each feed
            for i, feed_source in enumerate(feed_sources, 1):
                feed_start = datetime.utcnow()
                logger.info(f"\n[{i}/{len(feed_sources)}] Processing: {feed_source.name}")

                # Fetch feed
                result = await self.fetcher.fetch_feed(feed_source.url)

                if result["status"] == "success" and result["items"]:
                    # Process items
                    processed_items = DataProcessor.batch_process_items(
                        result["items"],
                        feed_source.id,
                        feed_source.category_id,
                    )

                    saved = 0
                    duplicates = 0

                    # Save articles to DB
                    for item in processed_items:
                        # Check for duplicate
                        is_dup, dup_id = Deduplicator.check_duplicate(
                            db,
                            item["title"],
                            item["published_date"],
                            feed_source.id,
                        )

                        if is_dup:
                            duplicates += 1
                            logger.debug(f"  Skipping duplicate: {item['title'][:50]}")
                        else:
                            try:
                                # Crawl full article content
                                full_content = await self.crawler.crawl_content(item["link"])
                                if full_content:
                                    item["content_html"] = full_content
                                    logger.debug(f"  Content crawled: {len(full_content)} chars")

                                article = Article(**item)
                                db.add(article)
                                saved += 1
                            except Exception as e:
                                logger.error(f"Error saving article: {e}")
                                db.rollback()

                    # Commit batch
                    try:
                        db.commit()
                        feed_source.last_fetched_at = datetime.utcnow()
                        db.commit()
                    except Exception as e:
                        logger.error(f"Error committing batch: {e}")
                        db.rollback()

                    # Log ingestion result
                    execution_time = (datetime.utcnow() - feed_start).total_seconds() * 1000
                    self._log_ingestion(
                        db,
                        feed_source.id,
                        "success",
                        len(result["items"]),
                        saved,
                        duplicates,
                        None,
                        int(execution_time),
                    )

                    total_fetched += len(result["items"])
                    total_saved += saved
                    total_duplicates += duplicates

                    logger.info(f"  ✓ Fetched: {len(result['items'])}, Saved: {saved}, Duplicates: {duplicates}")
                else:
                    # Log failed ingestion
                    self._log_ingestion(
                        db,
                        feed_source.id,
                        "failed",
                        0,
                        0,
                        0,
                        "Failed to fetch feed",
                        0,
                    )
                    logger.error(f"  ✗ Failed to fetch feed")

            # Final summary
            total_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info("\n" + "=" * 50)
            logger.info(f"Ingestion cycle completed in {total_time:.2f}s")
            logger.info(f"Total Fetched: {total_fetched}")
            logger.info(f"Total Saved: {total_saved}")
            logger.info(f"Total Duplicates: {total_duplicates}")
            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"Error in ingestion cycle: {e}")
        finally:
            if self.fetcher:
                await self.fetcher.close()
            if self.crawler:
                await self.crawler.close()
            db.close()

    def _log_ingestion(
        self,
        db: Session,
        feed_source_id: int,
        status: str,
        fetched: int,
        saved: int,
        duplicates: int,
        error: str,
        execution_time_ms: int,
    ):
        """Log ingestion results"""
        try:
            log = IngestionLog(
                feed_source_id=feed_source_id,
                status=status,
                articles_fetched=fetched,
                articles_saved=saved,
                duplicates_found=duplicates,
                error_message=error,
                execution_time_ms=execution_time_ms,
                completed_at=datetime.utcnow(),
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging ingestion: {e}")
            db.rollback()

    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return False

        try:
            # Create a fresh scheduler instance
            self.scheduler = BackgroundScheduler()
            
            # Add ingestion job
            self.scheduler.add_job(
                self._run_ingestion,
                trigger=IntervalTrigger(minutes=settings.INGEST_INTERVAL_MINUTES),
                id="rss_ingest_job",
                name="RSS Feed Ingestion",
                max_instances=1,
                misfire_grace_time=300,
            )

            self.scheduler.start()
            self.is_running = True
            logger.info(f"Scheduler started - ingestion every {settings.INGEST_INTERVAL_MINUTES} minutes")
            return True
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            return False

    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return False

        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown()
            self.scheduler = None
            self.is_running = False
            logger.info("Scheduler stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            return False

    def _run_ingestion(self):
        """Wrapper to run async ingestion in sync context"""
        asyncio.run(self.ingest_all_feeds())

    def get_status(self) -> dict:
        """Get scheduler status"""
        if self.scheduler:
            job = self.scheduler.get_job("rss_ingest_job")
            if job:
                return {
                    "is_running": self.is_running,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                }
        return {
            "is_running": self.is_running,
            "next_run_time": None,
        }


# Global ingestion scheduler instance
ingestion_scheduler = IngestionScheduler()
