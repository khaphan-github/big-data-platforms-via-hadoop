# BIRT Report Starter Pack

These `.rptdesign` files are starter templates wired for the RSS ingestion MySQL database.

Connection defaults:

- Host: `mysql`
- Port: `3306`
- Database: `rss_ingest`
- User: `root`

The designs currently define the MySQL ODA data source and a query skeleton. Open them in BIRT Designer to add tables, charts, and formatting if you want richer layouts.

Files:

1. `rss_articles_by_category.rptdesign`
2. `rss_articles_by_feed.rptdesign`
3. `rss_articles_by_day.rptdesign`
4. `rss_articles_dashboard.rptdesign`

The queries join `articles` to `categories` and `feed_sources` so the report labels match the app schema.
