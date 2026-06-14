from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Any

from pyhive import hive

from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class HiveManager:
    """Create and refresh the Hive external table used by Superset."""

    def __init__(self):
        self.host = settings.HIVE_HOST
        self.port = settings.HIVE_PORT
        self.database = settings.HIVE_DATABASE
        self.table = settings.HIVE_ARTICLES_TABLE
        self.auth = settings.HIVE_AUTH_MODE
        self.root_path = settings.HDFS_ARTICLES_PATH.rstrip("/")

    def ensure_table(self) -> None:
        """Create the Hive database and external table if they do not exist."""
        with self._cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.execute(f"USE {self.database}")
            cursor.execute(self._create_table_sql())
        logger.info("Hive table ensured: %s.%s", self.database, self.table)

    def repair_partitions(self) -> None:
        """Refresh Hive partition metadata after new HDFS partitions are written."""
        with self._cursor() as cursor:
            cursor.execute(f"USE {self.database}")
            cursor.execute(f"MSCK REPAIR TABLE {self.table}")
        logger.info("Hive partitions refreshed for %s.%s", self.database, self.table)

    def sync(self) -> None:
        """Ensure schema exists and refresh partition metadata."""
        self.ensure_table()
        self.repair_partitions()

    @contextmanager
    def _cursor(self) -> Iterator[Any]:
        connection = None
        cursor = None
        try:
            connection = hive.Connection(
                host=self.host,
                port=self.port,
                username=settings.HDFS_USER,
                database=self.database,
                auth=self.auth,
            )
            cursor = connection.cursor()
            yield cursor
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass
            try:
                if connection is not None:
                    connection.close()
            except Exception:
                pass

    def _create_table_sql(self) -> str:
        return f"""
CREATE EXTERNAL TABLE IF NOT EXISTS {self.table} (
  id BIGINT,
  title STRING,
  slug STRING,
  description STRING,
  content_html STRING,
  link STRING,
  guid STRING,
  author STRING,
  published_date STRING,
  fetched_date STRING,
  feed_source_id INT,
  feed_source_name STRING,
  category_id INT,
  category_name STRING,
  comment_count INT,
  created_at STRING,
  updated_at STRING
)
PARTITIONED BY (dt STRING)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION 'hdfs://{self.root_path}';
""".strip()
