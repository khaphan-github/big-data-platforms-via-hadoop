#!/usr/bin/env bash
set -euo pipefail

NAMENODE_CONTAINER="${NAMENODE_CONTAINER:-hadoop-namenode}"
SPARK_CONTAINER="${SPARK_CONTAINER:-spark-master}"
HDFS_BASE_PATH="${HDFS_BASE_PATH:-/raw_zone}"
HDFS_OUTPUT_PATH="${HDFS_OUTPUT_PATH:-/work_zone/table_trending_words}"
REMOTE_WORKDIR="${REMOTE_WORKDIR:-/tmp/keywords_e2e}"

if docker ps --format '{{.Names}}' | grep -qx "$NAMENODE_CONTAINER"; then
  echo "[INFO] Removing HDFS mock input/output"
  docker exec "$NAMENODE_CONTAINER" hdfs dfs -rm -r -f -skipTrash "$HDFS_BASE_PATH" || true
  docker exec "$NAMENODE_CONTAINER" hdfs dfs -rm -r -f -skipTrash "$HDFS_OUTPUT_PATH" || true
  docker exec "$NAMENODE_CONTAINER" hdfs dfs -rm -r -f -skipTrash "${HDFS_OUTPUT_PATH}_csv" || true
else
  echo "[WARN] Namenode container '$NAMENODE_CONTAINER' not running. Skipping HDFS cleanup."
fi

if docker ps --format '{{.Names}}' | grep -qx "$SPARK_CONTAINER"; then
  echo "[INFO] Removing temporary Spark workdir"
  docker exec "$SPARK_CONTAINER" rm -rf "$REMOTE_WORKDIR" || true
else
  echo "[WARN] Spark container '$SPARK_CONTAINER' not running. Skipping Spark temp cleanup."
fi

echo "[DONE] Cleanup finished"
