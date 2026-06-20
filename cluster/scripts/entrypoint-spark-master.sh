#!/bin/bash
set -e

SPARK_HOME=${SPARK_HOME:-/opt/spark}

# Setup directories
mkdir -p /var/log/spark /var/lib/spark/work
chmod 755 /var/log/spark /var/lib/spark/work

# Set permissions
chown spark:spark /var/lib/spark/work /var/log/spark

# Start Spark Master daemon
/opt/spark/bin/spark-class org.apache.spark.deploy.master.Master
