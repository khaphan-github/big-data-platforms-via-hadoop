#!/bin/bash
set -e

HADOOP_HOME=${HADOOP_HOME:-/opt/hadoop}

# Setup directories
mkdir -p /var/log/hadoop-hdfs /var/log/hadoop-yarn /var/log/hadoop
chmod 755 /var/log/hadoop* /var/log/hadoop

# Format HDFS namespace (only runs once due to volume persistence)
mkdir -p "/var/lib/hadoop-hdfs/cache/dfs/name"
hdfs namenode -format -force >/dev/null 2>&1

# Set permissions
chown hadoop:hadoop /var/lib/hadoop-hdfs/cache/dfs/name

# Start NameNode daemon
hdfs namenode
