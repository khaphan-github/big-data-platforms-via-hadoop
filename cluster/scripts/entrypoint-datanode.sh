#!/bin/bash
set -e

HADOOP_HOME=${HADOOP_HOME:-/opt/hadoop}
NAMENODE_HOST=${NAMENODE_HOST:-namenode}

# Setup directories
mkdir -p /var/log/hadoop-hdfs /var/log/hadoop-yarn /var/log/hadoop
chmod 755 /var/log/hadoop* /var/log/hadoop

# Create DataNode directories
mkdir -p /var/lib/hadoop-hdfs/cache/dfs/data
chown hadoop:hadoop /var/lib/hadoop-hdfs/cache/dfs/data

# Wait for NameNode to be ready (max 60 seconds)
for i in {1..30}; do
    nc -z ${NAMENODE_HOST} 9000 2>/dev/null && break
    sleep 2
done

# Start DataNode daemon
hdfs datanode
