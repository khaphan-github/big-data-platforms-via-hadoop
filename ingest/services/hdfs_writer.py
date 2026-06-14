import json
from collections import defaultdict
from datetime import datetime
from typing import Iterable, Any
from urllib.parse import quote
from uuid import uuid4

import httpx

from config.settings import settings
from models.base import Article
from utils.logger import setup_logger

logger = setup_logger(__name__)


class HDFSWriter:
    """Write ingested articles to HDFS through WebHDFS."""

    def __init__(self):
        self.base_url = settings.HDFS_WEBHDFS_URL.rstrip("/")
        self.user = settings.HDFS_USER
        self.root_path = settings.HDFS_ARTICLES_PATH.rstrip("/")
        self.timeout = settings.HDFS_TIMEOUT_SECONDS

    async def write_articles(self, articles: Iterable[Article]) -> list[str]:
        """Persist articles as newline-delimited JSON in a date partition."""
        article_list = list(articles)
        if not article_list:
            return []

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
            written_files = []
            for partition_date, partition_articles in self._group_by_partition(article_list).items():
                payload = "\n".join(
                    json.dumps(self._serialize_article(article), ensure_ascii=False)
                    for article in partition_articles
                )
                payload += "\n"

                hdfs_dir = f"{self.root_path}/dt={partition_date}"
                hdfs_file = f"{hdfs_dir}/articles_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}_{uuid4().hex}.jsonl"

                await self._mkdirs(client, hdfs_dir)
                await self._create_file(client, hdfs_file, payload)
                written_files.append(hdfs_file)

        logger.info(f"Wrote {len(article_list)} articles to HDFS: {', '.join(written_files)}")
        return written_files

    async def _mkdirs(self, client: httpx.AsyncClient, path: str) -> None:
        url = self._webhdfs_url(path, "MKDIRS")
        response = await client.put(url)
        response.raise_for_status()
        result = response.json()
        if not result.get("boolean"):
            raise RuntimeError(f"WebHDFS MKDIRS returned false for {path}")

    async def _create_file(self, client: httpx.AsyncClient, path: str, payload: str) -> None:
        create_url = self._webhdfs_url(path, "CREATE", overwrite="true")
        response = await client.put(create_url)

        if response.status_code not in (307, 201):
            response.raise_for_status()

        upload_url = response.headers.get("Location")
        if upload_url:
            response = await client.put(
                upload_url,
                content=payload.encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
            )

        response.raise_for_status()

    def _webhdfs_url(self, path: str, op: str, **params: Any) -> str:
        encoded_path = quote(path, safe="/")
        query = {"op": op, "user.name": self.user, **params}
        query_string = "&".join(f"{quote(str(key))}={quote(str(value))}" for key, value in query.items())
        return f"{self.base_url}/webhdfs/v1{encoded_path}?{query_string}"

    def _group_by_partition(self, articles: list[Article]) -> dict[str, list[Article]]:
        grouped = defaultdict(list)
        for article in articles:
            partition_date = article.published_date or article.fetched_date or datetime.utcnow()
            grouped[partition_date.strftime("%Y-%m-%d")].append(article)
        return dict(grouped)

    @staticmethod
    def _iso(value: datetime | None) -> str | None:
        return value.isoformat() if value else None

    def _serialize_article(self, article: Article) -> dict[str, Any]:
        return {
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "description": article.description,
            "content_html": article.content_html,
            "link": article.link,
            "guid": article.guid,
            "author": article.author,
            "published_date": self._iso(article.published_date),
            "fetched_date": self._iso(article.fetched_date),
            "feed_source_id": article.feed_source_id,
            "feed_source_name": article.feed_source.name if article.feed_source else None,
            "category_id": article.category_id,
            "category_name": article.category.name if article.category else None,
            "comment_count": article.comment_count,
            "created_at": self._iso(article.created_at),
            "updated_at": self._iso(article.updated_at),
        }
