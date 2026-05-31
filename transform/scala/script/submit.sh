#!/usr/bin/env bash
sbt clean assembly
docker cp target/scala-assembly.jar spark-master:/tmp/scala-assembly.jar
docker cp libs/vntokenizer4.1/models spark-master:/tmp/vnlp-models
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --class Main \
  --executor-memory 2g \
  --executor-cores 2 \
  --driver-memory 1g \
  /tmp/scala-assembly.jar \
  hdfs://namenode:9000/raw_zone \
  /tmp/vnlp-models \
  hdfs://namenode:9000/work_zone/table_trending_words_csv
