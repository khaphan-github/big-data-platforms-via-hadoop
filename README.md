# Vietnamese News Analytics - Big Data Platform

Analyze trending keywords from Vietnamese news using Hadoop, Spark, NiFi, Sqoop, and FastAPI.

## Architecture

```
Flow 1 (Ingestion):
  RSS Feeds → FastAPI (ingest app) → MySQL (rss_ingest)
                                          ↓
                                       NiFi (QueryDatabaseTable → PutHDFS)
                                          ↓
                                       HDFS /raw_zone/

Flow 2 (Processing → Serving):
  HDFS /raw_zone/ → Spark (trending words) → HDFS /work_zone/
                                                    ↓
                                              Sqoop export
                                                    ↓
                                           MySQL (trending_words table)
                                                    ↓
                                              Dashboard (serving app)
```

## Quick Start

### 1. Start infrastructure

```bash
cd ingest && docker-compose up -d --build
```

Wait ~3 minutes for all services to be healthy.

### 2. Configure NiFi (Flow 1)

Open NiFi at **http://localhost:8161/nifi** and create the flow:

```
[QueryDatabaseTable]  →  [ConvertAvroToJSON]  →  [PutHDFS]
  MySQL: ingest DB           (format conv)       /raw_zone/
```

See `docs/nifi-flow-setup.md` for step-by-step NiFi configuration.

### 3. Run Spark job (Flow 2, Step 1)

```bash
# From spark-master container
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --py-files /path/to/tokenizer_handler.py \
  trending_words_job.py \
  hdfs://namenode:9000/raw_zone \
  hdfs://namenode:9000/work_zone/table_trending_words
```

### 4. Run Sqoop export (Flow 2, Step 2)

```bash
docker exec sqoop /opt/sqoop-scripts/export_trending_words.sh
```

### 5. View Dashboard

```bash
cd serving && python main.py
# Open http://localhost:3030/charts
```

## 🔗 Services

| Service              | URL                        | Mô tả |
| -------------------- | -------------------------- | ------ |
| HDFS NameNode        | http://localhost:9870      | HDFS Web UI |
| Apache NiFi          | http://localhost:8161/nifi | Cấu hình Flow 1 |
| Ingest API           | http://localhost:8000/docs | RSS ingestion API |
| Ingest MySQL         | localhost:3308             | Source DB (rss_ingest) |
| Apache Superset      | http://localhost:8088      | Analytics dashboard |
| Serving API          | http://localhost:3030      | Charts dashboard |

## 📂 Folders

- `cluster/` - Hadoop HDFS images & config
- `ingest/` - RSS fetcher + MySQL + NiFi + Sqoop
- `transform/` - Spark trending words job
- `serving/` - Results dashboard API

## Pipeline Steps Detail

| Step | Tool | Input | Output |
|------|------|-------|--------|
| 1 | FastAPI + APScheduler | RSS XML | MySQL `articles` table |
| 2 | **NiFi** (Flow 1) | MySQL `articles` | HDFS `/raw_zone/` JSON |
| 3 | Spark PySpark/Scala | HDFS `/raw_zone/` | HDFS `/work_zone/` CSV+Parquet |
| 4 | **Sqoop** (Flow 2) | HDFS `/work_zone/` CSV | MySQL `trending_words` table |
| 5 | Serving App | MySQL `trending_words` | Chart images via API |
