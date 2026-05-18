"""
Scheduler for Trending Words Spark Job
Periodically executes the trending words extraction with output replacement logic
"""
import os
import sys
import time
import schedule
import logging
from datetime import datetime
from trending_words_job import TrendingWordsSparkJob


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [Scheduler] - %(message)s',
    handlers=[
        logging.FileHandler('/app/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TrendingWordsScheduler:
    """Scheduler for periodic execution of trending words extraction job"""
    
    def __init__(self, hdfs_input, hdfs_output, interval_seconds=3600):
        """
        Initialize scheduler
        
        Args:
            hdfs_input: HDFS input path
            hdfs_output: HDFS output path
            interval_seconds: Interval in seconds between job executions (default: 1 hour)
        """
        self.hdfs_input = hdfs_input
        self.hdfs_output = hdfs_output
        self.interval_seconds = interval_seconds
        self.job = TrendingWordsSparkJob(hdfs_input, hdfs_output)
        
    def run_job(self):
        """Execute the trending words job"""
        try:
            logger.info(f"Starting scheduled job execution...")
            logger.info(f"Input: {self.hdfs_input}")
            logger.info(f"Output: {self.hdfs_output}")
            
            # Run the job with overwrite mode (replacement logic)
            self.job.run()
            
            logger.info(f"Job completed successfully at {datetime.now()}")
            
        except Exception as e:
            logger.error(f"Job execution failed: {str(e)}", exc_info=True)
    
    def schedule_job(self):
        """Schedule the job to run at specified intervals"""
        interval_minutes = self.interval_seconds / 60
        
        # Schedule the job
        schedule.every(self.interval_seconds).seconds.do(self.run_job)
        
        logger.info(f"Job scheduled to run every {interval_minutes:.1f} minutes")
        logger.info(f"Scheduler started at {datetime.now()}")
        
        # Keep scheduler running
        while True:
            schedule.run_pending()
            time.sleep(1)


def main():
    """Main entry point for scheduler"""
    # Get configuration from environment variables
    hdfs_input = os.getenv("HDFS_INPUT", "hdfs://namenode:9000/raw_zone")
    hdfs_output = os.getenv("HDFS_OUTPUT", "hdfs://namenode:9000/work_zone/table_trending_words")
    interval_seconds = int(os.getenv("SCHEDULE_INTERVAL", "3600"))
    
    # Allow override via command line arguments
    if len(sys.argv) > 1:
        hdfs_input = sys.argv[1]
    if len(sys.argv) > 2:
        hdfs_output = sys.argv[2]
    if len(sys.argv) > 3:
        interval_seconds = int(sys.argv[3])
    
    logger.info("="*60)
    logger.info("Trending Words Scheduler Started")
    logger.info("="*60)
    logger.info(f"HDFS Input: {hdfs_input}")
    logger.info(f"HDFS Output: {hdfs_output}")
    logger.info(f"Schedule Interval: {interval_seconds} seconds ({interval_seconds/60:.1f} minutes)")
    logger.info("="*60)
    
    # Create and start scheduler
    scheduler = TrendingWordsScheduler(hdfs_input, hdfs_output, interval_seconds)
    scheduler.schedule_job()


if __name__ == "__main__":
    main()
