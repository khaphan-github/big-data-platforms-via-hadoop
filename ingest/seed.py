#!/usr/bin/env python
"""
Database seeding entry point.
Can be run directly to seed the database without starting the app.

Usage:
    python seed.py              # Seed with default settings
    python seed.py --reset      # Reset and reseed the database
"""

import sys
import logging
from argparse import ArgumentParser

from db.database import SessionLocal, engine
from db.init_db import init_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def seed_database(reset: bool = False):
    """
    Seed the database with initial data.
    
    Args:
        reset: If True, drops all tables before seeding (destructive)
    """
    try:
        if reset:
            logger.warning("Resetting database - dropping all tables...")
            from db.database import Base
            Base.metadata.drop_all(bind=engine)
            logger.info("All tables dropped")
        
        logger.info("Starting database initialization and seeding...")
        init_db()
        logger.info("✓ Database seeding completed successfully!")
        return True
    except Exception as e:
        logger.error(f"✗ Error seeding database: {e}", exc_info=True)
        return False


def main():
    parser = ArgumentParser(description="Database seeding utility")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (drops all tables) before seeding"
    )
    
    args = parser.parse_args()
    
    if args.reset:
        response = input(
            "⚠️  WARNING: This will drop all existing data. Continue? (yes/no): "
        )
        if response.lower() != "yes":
            logger.info("Seeding cancelled")
            sys.exit(0)
    
    success = seed_database(reset=args.reset)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
