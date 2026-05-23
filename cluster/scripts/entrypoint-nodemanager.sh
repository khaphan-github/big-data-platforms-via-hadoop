#!/bin/bash
set -e

HADOOP_HOME=${HADOOP_HOME:-/opt/hadoop}
RESOURCEMANAGER_HOST=${RESOURCEMANAGER_HOST:-resourcemanager}

# Setup directories
mkdir -p /var/log/hadoop-hdfs /var/log/hadoop-yarn /var/log/hadoop
chmod 755 /var/log/hadoop* /var/log/hadoop

# Create NodeManager directories
mkdir -p /var/lib/hadoop-yarn/cache
chown hadoop:hadoop /var/lib/hadoop-yarn/cache

# Wait for ResourceManager to be ready (max 60 seconds)
for i in {1..30}; do
    nc -z ${RESOURCEMANAGER_HOST} 8032 2>/dev/null && break
    sleep 2
done

# Start NodeManager daemon
yarn nodemanager
