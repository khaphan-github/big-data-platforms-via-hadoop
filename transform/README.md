# Trending Words Extraction - Spark Job with Scheduler

Production-ready Spark job for extracting and counting trending Vietnamese keywords from article data with periodic execution scheduler.

## Quick Start

### Local Setup

```bash
pip install -r requirements.txt
chmod +x run_spark_job.sh run_scheduler.sh

# Run job once
./run_spark_job.sh hdfs://namenode:9000/raw_zone hdfs://namenode:9000/work_zone/table_trending_words

# Run scheduler with hourly intervals
./run_scheduler.sh hdfs://namenode:9000/raw_zone hdfs://namenode:9000/work_zone/table_trending_words 3600
```

### Docker Compose (Spark + Scheduler)

```bash
# Start Spark services and scheduler
docker-compose up -d

# View scheduler logs
docker-compose logs -f scheduler

# View Spark job logs
docker-compose logs -f trending-words-job

# Stop all services
docker-compose down
```

### Docker Build & Run

```bash
# Build Spark job image
docker build -t trending-words:latest -f Dockerfile .

# Build scheduler image
docker build -t trending-words-scheduler:latest -f Dockerfile.scheduler .

# Run job manually
docker run -e HDFS_INPUT=hdfs://namenode:9000/raw_zone \
           -e HDFS_OUTPUT=hdfs://namenode:9000/work_zone/table_trending_words \
           -e SPARK_MASTER=spark://spark-master:7077 \
           trending-words:latest

# Run scheduler with 1-hour interval
docker run -e HDFS_INPUT=hdfs://namenode:9000/raw_zone \
           -e HDFS_OUTPUT=hdfs://namenode:9000/work_zone/table_trending_words \
           -e SPARK_MASTER=spark://spark-master:7077 \
           -e SCHEDULE_INTERVAL=3600 \
           trending-words-scheduler:latest
```

### Run Tests

```bash
python test_tokenizer.py
```

## Docker Services

When running `docker-compose up`, the following services start:

| Service            | Port       | Purpose                                  |
| ------------------ | ---------- | ---------------------------------------- |
| spark-master       | 8080, 7077 | Spark Master (web UI, cluster)           |
| spark-worker       | 8081       | Spark Worker                             |
| trending-words-job | -          | Transformation job (runs when needed)    |
| scheduler          | -          | Periodic job scheduler (default: hourly) |

**Access Web UIs**:

- Spark: http://localhost:8080

## Scheduler Configuration

The scheduler runs the trending words extraction job at regular intervals with automatic output replacement.

### Environment Variables

- `SCHEDULE_INTERVAL` - Interval in seconds (default: 3600 = 1 hour)
- `HDFS_INPUT` - Input data path (default: hdfs://namenode:9000/raw_zone)
- `HDFS_OUTPUT` - Output path (default: hdfs://namenode:9000/work_zone/table_trending_words)
- `SPARK_MASTER` - Spark master URL (default: spark://spark-master:7077)
- `EXECUTOR_MEMORY` - Executor memory (default: 2G)
- `EXECUTOR_CORES` - Executor cores (default: 2)

### Examples

```bash
# Run scheduler every 30 minutes
SCHEDULE_INTERVAL=1800 python scheduler.py

# Run scheduler every 2 hours
SCHEDULE_INTERVAL=7200 python scheduler.py

# Custom paths
HDFS_INPUT=/data/articles HDFS_OUTPUT=/results python scheduler.py
```

## Input Data

Data organized by category in HDFS:

```
hdfs://namenode:9000/raw_zone/
  ├── giai_tri/      → Entertainment
  ├── cong_nghe/     → Technology
  └── suc_khoe/      → Health
```

Each file contains:

```json
{
  "publish_date": "2024-01-15T10:30:00",
  "source": "ThanhNien",
  "title": "Phim mới nhất...",
  "content": "Nội dung bài viết..."
}
```

**Sources**: ThanhNien, TuoiTre, VNN

## Output Data

**Location**: `/work_zone/table_trending_words` (Parquet + CSV)

Output files are **automatically overwritten** on each scheduler execution.

**Fields**:
| Column | Format | Example |
|--------|--------|---------|
| ngay | yyyyMMdd | 20240115 |
| nguon | String | ThanhNien |
| chu_de | String | GiaiTri |
| tu_khoa | String | phim |
| so_lan_xuat_hien | Integer | 45 |

**Example Output**:

```
ngay,nguon,chu_de,tu_khoa,so_lan_xuat_hien
20240115,ThanhNien,GiaiTri,phim,45
20240115,ThanhNien,GiaiTri,hành_động,32
20240116,TuoiTre,CongNghe,công_nghệ,68
20240117,VNN,SucKhoe,sức_khỏe,61
```

## Processing Pipeline

1. Read articles from category folders
2. Parse date, source, category
3. Clean text (remove special chars)
4. Tokenize using VnTokenizer4.1
5. Remove stopwords + short words (< 2 chars)
6. Count keyword occurrences
7. Write to HDFS (Parquet + CSV) with overwrite mode

## Components

### trending_words_job.py

Main Spark job that:

- Reads from HDFS by category
- Tokenizes Vietnamese text
- Extracts and counts keywords
- Outputs results with overwrite mode (write.mode("overwrite"))

### scheduler.py

Scheduler that:

- Runs at configurable intervals
- Executes trending_words_job with replacement logic
- Logs all execution details
- Handles errors gracefully

### tokenizer_handler.py

Vietnamese text processing:

- Word segmentation using vntokenizer4.1
- Stopword filtering (~300+ Vietnamese words)
- Text cleaning

## Troubleshooting

| Issue                 | Solution                                         |
| --------------------- | ------------------------------------------------ |
| Scheduler not running | Check logs: `docker-compose logs scheduler`      |
| HDFS connection fails | Verify HDFS paths and connectivity               |
| Data not found        | Check folder paths exist in HDFS                 |
| Tokenizer error       | Install: `pip install vntokenizer==4.1`          |
| Out of memory         | Increase `EXECUTOR_MEMORY` in docker-compose.yml |
| Job stuck/hanging     | Check Spark Web UI at http://localhost:8080      |

## Architecture

```
docker-compose
├── spark-master (coordinator)
├── spark-worker (executor)
├── trending-words-job (on-demand)
└── scheduler (periodic trigger)
    └── Executes trending-words-job every N seconds
        └── Writes results with overwrite mode
```

## Performance Notes

- Default: 1-hour execution interval (3600 seconds)
- Memory: 2GB per executor (configurable)
- Cores: 2 per executor (configurable)
- Output: Automatic replacement (no manual cleanup needed)
