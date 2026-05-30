#!/usr/bin/env bash
set -euo pipefail

docker exec -u 0 spark-master rm -rf /tmp/keywords_wheel /tmp/keywords_extract 2>/dev/null || true
docker exec -u 0 spark-master mkdir -p /tmp/keywords_wheel /tmp/keywords_extract

docker cp ./dist/bigdt_transform_keywords-0.1.0-py3-none-any.whl spark-master:/tmp/keywords_wheel/
docker exec -u 0 spark-master chown -R spark:spark /tmp/keywords_wheel

# Extract wheel to get entry point
docker exec spark-master python -m zipfile -e /tmp/keywords_wheel/bigdt_transform_keywords-0.1.0-py3-none-any.whl /tmp/keywords_extract/

docker exec \
  -e HDFS_BASE_PATH="hdfs://namenode:9000/raw_zone" \
  -e HDFS_OUTPUT_PATH="hdfs://namenode:9000/work_zone/table_trending_words" \
  spark-master \
  spark-submit \
    --master spark://spark-master:7077 \
    --deploy-mode client \
    --py-files /tmp/keywords_wheel/bigdt_transform_keywords-0.1.0-py3-none-any.whl \
    /tmp/keywords_extract/bigdt_transform_keywords/trending_words_job.py \
    hdfs://namenode:9000/raw_zone \
    hdfs://namenode:9000/work_zone/table_trending_words

docker exec -u 0 spark-master rm -rf /tmp/keywords_wheel /tmp/keywords_extract
