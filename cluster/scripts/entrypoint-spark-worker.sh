#!/bin/bash
set -e

SPARK_HOME=${SPARK_HOME:-/opt/spark}
SPARK_MASTER_HOST=${SPARK_MASTER_HOST:-spark-master}
SPARK_MASTER_PORT=${SPARK_MASTER_PORT:-7077}

# Setup directories
mkdir -p /var/log/spark /var/lib/spark/work
chmod 755 /var/log/spark /var/lib/spark/work

# Set permissions
chown spark:spark /var/lib/spark/work /var/log/spark

# Wait for Spark Master to be ready (max 60 seconds)
for i in {1..30}; do
    nc -z ${SPARK_MASTER_HOST} ${SPARK_MASTER_PORT} 2>/dev/null && break
    sleep 2
done

# Start Spark Worker daemon
/opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker spark://${SPARK_MASTER_HOST}:${SPARK_MASTER_PORT}
