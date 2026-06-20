# BIRT Visualization

This directory is the mount point for BIRT report assets.

Recommended layout:

```text
ingest/birt/
  reports/
    *.rptdesign
```

The Docker service in `docker-compose.yml` mounts `./birt/reports` to
`/opt/birt/reports` inside the container.

If you create BIRT reports for this project, point them at:

```text
MySQL host: mysql
MySQL port: 3306
Database: rss_ingest
Tables: articles, feed_sources, ingestion_logs
```

For article-level dashboards, use fields such as
`category_name`, `feed_source_name`, `published_date`, and `fetched_date`.
