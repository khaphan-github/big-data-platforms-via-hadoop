#!/bin/bash
set -e

HADOOP_HOME=${HADOOP_HOME:-/opt/hadoop}
DATANODE_DIR="/var/lib/hadoop-hdfs/cache/dfs/data"

# Setup directories
mkdir -p /var/log/hadoop-hdfs /var/log/hadoop-yarn /var/log/hadoop
chmod 755 /var/log/hadoop* /var/log/hadoop

# Create DataNode directories
mkdir -p "${DATANODE_DIR}"
chown hadoop:hadoop "${DATANODE_DIR}"
hdfs datanode
