# RSS Feed Data Ingestion System

A complete RSS feed ingestion system built with FastAPI, SQLAlchemy, and APScheduler. Automatically fetches and processes articles from 9 Vietnamese news RSS feeds every 30 minutes with deduplication and comprehensive logging.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python db/init_db.py

# Run application
python main.py
```

### Docker Deployment

```bash
# Create environment file
cp .env.example .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f app
```

## Features

- 🔄 **Scheduled Ingestion**: Every 30 minutes (configurable)
- 🔗 **Multi-Source**: 9 Vietnamese news feeds across 3 categories
- ✅ **Smart Deduplication**: By title + publication date
- 🗂️ **HDFS Data Lake**: Writes committed articles as JSONL partitions
- 📈 **BIRT Ready**: Docker service for reporting dashboards over MySQL
- 🔁 **Resilience**: Exponential backoff retry (up to 4 retries)
- 📊 **Full Logging**: Complete ingestion statistics and audit trail
- 🐳 **Docker Ready**: Containerized with MySQL
- 📋 **Admin API**: Start/stop scheduler, view logs
- 🏗️ **Clean Code**: Layered architecture with separation of concerns

## API Endpoints

### Health & Status

```
GET /api/health              # Health check
GET /api/admin/scheduler/status  # Scheduler status
```

### Scheduler Control

```
POST /api/admin/scheduler/start   # Start ingestion
POST /api/admin/scheduler/stop    # Stop ingestion
```

### Logs & Monitoring

```
GET /api/admin/logs              # Paginated logs
  - ?limit=50&offset=0 (pagination)
  - ?feed_source_id=1 (filter by feed)
  - ?status=success (filter by status)

GET /api/admin/logs/latest       # Latest ingestion
GET /api/admin/feeds             # List all feeds
```

## Feed Sources

| Category      | Sources                          |
| ------------- | -------------------------------- |
| **Giải Trí**  | Vietnamnet, Thanh Niên, Tuổi Trẻ |
| **Công Nghệ** | Vietnamnet, Thanh Niên, Tuổi Trẻ |
| **Sức Khỏe**  | Vietnamnet, Thanh Niên, Tuổi Trẻ |

## Configuration

Edit `.env` file:

```
# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=rss_ingest

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Scheduler
INGEST_INTERVAL_MINUTES=30
MAX_RETRIES=4
REQUEST_TIMEOUT_SECONDS=10

# HDFS / BIRT
HDFS_ENABLED=true
HDFS_WEBHDFS_URL=http://localhost:9870
HDFS_USER=root
HDFS_ARTICLES_PATH=/data/rss/articles
BIRT_REPORTS_DIR=/opt/birt/reports
BIRT_DEFAULT_REPORT=rss_articles_dashboard.rptdesign
BIRT_VIEWER_CONTEXT=/birt
```

## BIRT Reports

Open the BIRT portal at http://localhost:8088.

The BIRT container starts a report viewer on port `8088` and reads MySQL directly from the ingestion database. Mount report designs under `ingest/birt/reports`.

Build reports such as article count by `category_name`, count by `feed_source_name`, or trend by `published_date`.

## Database Schema

### Articles Table

- `id`: Primary key
- `title`: Article title
- `slug`: URL-friendly identifier
- `link`: Article URL (unique)
- `description`: Article text (cleaned HTML)
- `published_date`: Publication date
- `feed_source_id`: Reference to feed
- `is_duplicate`: Duplicate flag
- `duplicate_of_id`: Original article reference

### Feed Sources Table

- `id`: Primary key
- `name`: Feed name
- `url`: RSS URL
- `category_id`: Category reference
- `is_active`: Active status
- `last_fetched_at`: Last update time

### Ingestion Logs Table

- Track each ingestion cycle
- articles_fetched, articles_saved, duplicates_found
- Execution time and error messages

## Architecture

```
┌─────────────────────────────────────┐
│    FastAPI Application              │
├─────────────────────────────────────┤
│ Admin API Routes                    │
│ - Start/Stop Scheduler              │
│ - View Logs & Status                │
└──────────────┬──────────────────────┘
               │
        ┌──────▼──────┐
        │ APScheduler │ (30 min trigger)
        └──────┬──────┘
               │
        ┌──────▼──────────────────┐
        │ Ingestion Pipeline      │
        ├─────────────────────────┤
        │ 1. RSS Fetcher          │
        │ 2. Data Processor       │
        │ 3. Deduplicator        │
        │ 4. Database Persister  │
        │ 5. HDFS JSONL Writer   │
        │ 6. Report Data Refresh │
        └──────┬──────────────────┘
               │
        ┌──────▼──────────┐       ┌──────────────┐       ┌────────┐
        │  MySQL Database │       │ HDFS Storage │       │ BIRT   │
        └─────────────────┘       └──────────────┘       └────────┘
```

## Implementation Details

### Deduplication Strategy

- Normalizes titles (lowercase, whitespace trim)
- Matches against same-day publications from same feed
- Preserves original articles without deletion

### Error Handling

- Retry with exponential backoff: 2s → 4s → 8s → 16s
- Logs all failures for debugging
- Graceful degradation on network issues

### Data Cleaning

- Strips HTML from descriptions
- Creates URL-friendly slugs
- Truncates long text fields
- Normalizes whitespace

### HDFS Layout

Committed articles are written as newline-delimited JSON:

```text
/data/rss/articles/dt=YYYY-MM-DD/articles_<timestamp>_<uuid>.jsonl
```

BIRT reads the same data directly from MySQL. HDFS keeps the committed article storage partitioned by `dt=` for downstream processing or audit.

## Example Usage

```bash
# Start scheduler
curl -X POST http://localhost:8000/api/admin/scheduler/start

# Check status
curl http://localhost:8000/api/admin/scheduler/status

# Get recent logs
curl "http://localhost:8000/api/admin/logs?limit=10"

# Get specific feed logs
curl "http://localhost:8000/api/admin/logs?feed_source_id=1&status=success"

# Stop scheduler
curl -X POST http://localhost:8000/api/admin/scheduler/stop
```

## Monitoring

View application logs:

```bash
# Local
tail -f logs/ingest.log

# Docker
docker-compose logs -f app
```

Logs include:

- Ingestion start/end times
- Articles fetched per feed
- Deduplication counts
- Error messages and retry attempts
- Database operations timing

## Technology Stack

| Component     | Package     | Version |
| ------------- | ----------- | ------- |
| Web Framework | FastAPI     | 0.104+  |
| Server        | Uvicorn     | 0.24+   |
| Scheduler     | APScheduler | 3.10+   |
| ORM           | SQLAlchemy  | 2.0+    |
| Database      | MySQL       | 8.0+    |
| HTTP Client   | httpx       | 0.25+   |
| XML Parser    | lxml        | 4.9+    |
| Validation    | Pydantic    | 2.0+    |
