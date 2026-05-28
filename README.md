# Vietnamese News Analytics - Big Data Platform

Analyze trending keywords from Vietnamese news using Hadoop, Spark, and FastAPI.

## Quick Start

1. **Download files**

   ```bash
   cd cluster/download &&  ./download.sh
   ```

2. **Start cluster** (wait ~3 minutes for services to be ready)

   ```bash
   docker-compose up -d
   ```

3. **Ingest service**

   Ingest đã được gộp trong `docker-compose.yml` tổng, chạy cùng lúc với bước 2.

4. **Run Spark job**

   ```bash
   cd transform && ./run_scheduler.sh
   ```

5. **Start API**
   ```bash
   cd serving && python main.py
   ```

## 🔗 Check Services

| Service              | URL                        |
| -------------------- | -------------------------- |
| HDFS NameNode        | http://localhost:50070     |
| YARN ResourceManager | http://localhost:8088      |
| Spark Master         | http://localhost:8080      |
| Apache NiFi          | http://localhost:8161/nifi |
| Ingest API           | http://localhost:8000      |
| Ingest Docs          | http://localhost:8000/docs |
| Serving API          | http://localhost:5000      |
| Cluster MySQL        | localhost:3306             |
| Ingest MySQL         | localhost:3308             |

## 📂 Folders

- `cluster/` - Hadoop HDFS + YARN
- `ingest/` - RSS fetcher + MySQL storage
- `transform/` - Spark trending words job
- `serving/` - Results API
