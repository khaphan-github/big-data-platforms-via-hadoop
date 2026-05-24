# Vietnamese News Analytics - Big Data Platform

Analyze trending keywords from Vietnamese news using Hadoop, Spark, and FastAPI.

## Quick Start

1. **Start Cluster**

   ```bash
   cd cluster && docker-compose up -d
   ```

2. **Start Ingest**

   ```bash
   cd ingest && docker-compose up -d
   ```

3. **Run Spark Job**

   ```bash
   cd transform && ./run_scheduler.sh
   ```

4. **Start API**
   ```bash
   cd serving && python main.py
   ```

## 🔗 Check Services

| Service              | URL                        |
| -------------------- | -------------------------- |
| HDFS NameNode        | http://localhost:50070      |
| YARN ResourceManager | http://localhost:8088      |
| Spark Master         | http://localhost:8080      |
| Apache NiFi          | http://localhost:8161/nifi |
| Ingest API           | http://localhost:8000      |
| Ingest Docs          | http://localhost:8000/docs |
| Serving API          | http://localhost:5000      |
| MySQL                | localhost:3306             |

## 📂 Folders

- `cluster/` - Hadoop HDFS + YARN
- `ingest/` - RSS fetcher + MySQL storage
- `transform/` - Spark trending words job
- `serving/` - Results API
