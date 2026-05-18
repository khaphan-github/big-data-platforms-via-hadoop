# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Local Python (Recommended for Development)

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Create environment file
cp .env.example .env

# 3. Start the application (without database)
python main.py

# 4. Visit the API
# Open browser: http://localhost:8000/docs
```

### Option 2: Docker Compose (Recommended for Production)

```bash
# 1. Create environment file
cp .env.example .env

# 2. Start all services (seeds database automatically on startup)
docker-compose up -d

# 3. Wait for services and auto-seeding to complete (~15 seconds)
sleep 15

# 4. Verify database is seeded
docker-compose exec app mysql -u root -prss_password rss_ingest -e "SELECT COUNT(*) as feed_sources FROM feed_sources;"

# 5. Monitor logs
docker-compose logs -f app
```

**Note:** Database seeding runs automatically when the application starts. To manually reseed:

```bash
# Reseed without losing data
docker-compose exec app python seed.py

# Reseed with full reset (destructive)
docker-compose exec app python seed.py --reset
```

---

## 📋 Common Commands

### Seed Database

```bash
# Automatic (runs on app startup)
python main.py

# Manual seeding - add missing data
python seed.py

# Manual seeding - reset and reseed everything (destructive)
python seed.py --reset

# Docker: Reseed without data loss
docker-compose exec app python seed.py

# Docker: Full reset (destructive)
docker-compose exec app python seed.py --reset
```

### Start Application

```bash
source .venv/bin/activate
python main.py
```

### Check Health

```bash
curl http://localhost:8000/api/health
```

### View API Docs

```
Browser: http://localhost:8000/docs
```

### Start RSS Ingestion

```bash
curl -X POST http://localhost:8000/api/admin/scheduler/start
```

### Get Scheduler Status

```bash
curl http://localhost:8000/api/admin/scheduler/status
```

### View Recent Logs

```bash
curl http://localhost:8000/api/admin/logs?limit=10
```

### Stop Ingestion

```bash
curl -X POST http://localhost:8000/api/admin/scheduler/stop
```

### View Application Logs

```bash
tail -f logs/ingest.log
```

### Docker: View Logs

```bash
docker-compose logs -f app
```

### Docker: Stop Services

```bash
docker-compose down
```

---

## 🔧 Configuration

Edit `.env` file to customize:

```env
# Database (required for ingestion)
MYSQL_HOST=mysql          # or localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=rss_ingest

# API Server
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Scheduler
INGEST_INTERVAL_MINUTES=30
MAX_RETRIES=4
REQUEST_TIMEOUT_SECONDS=10
```

---

## 📊 First Ingestion Cycle

After starting the scheduler, the system will:

1. Fetch 9 Vietnamese RSS feeds
2. Parse 150-200 articles
3. Check for duplicates
4. Save to database
5. Log all activities

This happens automatically every 30 minutes.

---

## 🐛 Troubleshooting

### "Connection refused" error

- **Cause**: MySQL not running
- **Solution**: Start MySQL or Docker container

### "Port already in use" error

- **Cause**: Port 8000 already in use
- **Solution**: Change `API_PORT` in .env or kill existing process

### Empty logs in database

- **Cause**: No ingestion cycle completed yet
- **Solution**: Wait 30+ minutes or manually trigger ingestion

### Database errors

- **Cause**: MySQL not initialized
- **Solution**: Run `python db/init_db.py`

---

## 📚 Documentation

- **Full API Docs**: http://localhost:8000/docs
- **Architecture**: [INGESTION_PLAN.md](INGESTION_PLAN.md)
- **Test Report**: [TEST_REPORT.md](TEST_REPORT.md)
- **Implementation**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

## ✨ Features

- ✅ 9 Vietnamese news RSS feeds
- ✅ Automatic ingestion every 30 minutes
- ✅ Duplicate detection
- ✅ Retry with exponential backoff
- ✅ Comprehensive logging
- ✅ Docker ready
- ✅ API documentation with Swagger UI

---

## 🎯 Next Steps

1. Start the application
2. Visit http://localhost:8000/docs to explore APIs
3. Check the logs to see ingestion in action
4. Set up database with Docker for production

**Enjoy!** 🚀
