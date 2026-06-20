#!/usr/bin/env bash
set -euo pipefail

SPARK_CONTAINER="${SPARK_CONTAINER:-spark-master}"
HDFS_BASE_URI="${HDFS_BASE_URI:-hdfs://namenode:9000/raw_zone}"
HDFS_OUTPUT_URI="${HDFS_OUTPUT_URI:-hdfs://namenode:9000/work_zone/table_trending_words}"
REMOTE_WORKDIR="${REMOTE_WORKDIR:-/tmp/keywords_e2e}"
REMOTE_PROJECT_DIR="${REMOTE_WORKDIR}/transform"
REMOTE_PYFILES="${REMOTE_WORKDIR}/transform_pyfiles.zip"

if ! docker ps --format '{{.Names}}' | grep -qx "$SPARK_CONTAINER"; then
  echo "[ERROR] Container '$SPARK_CONTAINER' is not running."
  echo "Start Spark first, e.g. docker compose up -d spark-master spark-worker1 spark-worker2"
  exit 1
fi

echo "[INFO] Syncing transform code into ${SPARK_CONTAINER}:${REMOTE_WORKDIR}"
docker exec -u 0 "$SPARK_CONTAINER" rm -rf "$REMOTE_WORKDIR"
docker exec -u 0 "$SPARK_CONTAINER" mkdir -p "$REMOTE_PROJECT_DIR"
docker cp transform/. "$SPARK_CONTAINER":"$REMOTE_PROJECT_DIR/"
docker exec -u 0 "$SPARK_CONTAINER" chown -R spark:spark "$REMOTE_WORKDIR"
docker exec "$SPARK_CONTAINER" python3 -m zipfile -c "$REMOTE_PYFILES" "$REMOTE_PROJECT_DIR"

echo "[INFO] Running Spark job"
docker exec -e HDFS_BASE_PATH="$HDFS_BASE_URI" -e HDFS_OUTPUT_PATH="$HDFS_OUTPUT_URI" -e PYTHONPATH="$REMOTE_WORKDIR" "$SPARK_CONTAINER" \
  spark-submit \
    --master spark://spark-master:7077 \
    --deploy-mode client \
    --py-files "$REMOTE_PYFILES" \
    "$REMOTE_PROJECT_DIR/keywords/trending_words_job.py" \
    "$HDFS_BASE_URI" \
    "$HDFS_OUTPUT_URI"

echo "[DONE] Job completed"
