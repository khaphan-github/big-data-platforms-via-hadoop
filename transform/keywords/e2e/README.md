# Keywords E2E

This folder provides end-to-end scripts for `transform/keywords`:

1. generate mock input data on HDFS
2. run Spark trending words job
3. clean up HDFS and temp files

## Prerequisites

- Docker + Docker Compose
- Running containers:
  - `hadoop-namenode`, `hadoop-datanode1`, `hadoop-datanode2`
  - `spark-master` (and workers if you want distributed execution)

Example:

```bash
docker compose up -d namenode datanode1 datanode2 spark-master spark-worker1 spark-worker2
```

## Quick start

Run setup + processing:

```bash
bash transform/keywords/e2e/run_e2e.sh all
```

Run each step separately:

```bash
bash transform/keywords/e2e/run_e2e.sh setup
bash transform/keywords/e2e/run_e2e.sh run
bash transform/keywords/e2e/run_e2e.sh cleanup
```

## Configurable env vars

- `NAMENODE_CONTAINER` (default: `hadoop-namenode`)
- `SPARK_CONTAINER` (default: `spark-master`)
- `HDFS_BASE_PATH` for setup/cleanup path mode (default: `/raw_zone`)
- `HDFS_OUTPUT_PATH` for cleanup path mode (default: `/work_zone/table_trending_words`)
- `HDFS_BASE_URI` for Spark read path (default: `hdfs://namenode:9000/raw_zone`)
- `HDFS_OUTPUT_URI` for Spark write path (default: `hdfs://namenode:9000/work_zone/table_trending_words`)
