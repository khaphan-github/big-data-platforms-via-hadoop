#!/bin/bash
set -e

HADOOP_HOME=${HADOOP_HOME:-/opt/hadoop}

# Setup directories
mkdir -p /var/log/hadoop-hdfs /var/log/hadoop-yarn /var/log/hadoop
chmod 755 /var/log/hadoop* /var/log/hadoop

# Create ResourceManager directories
mkdir -p /var/lib/hadoop-yarn/cache
chown hadoop:hadoop /var/lib/hadoop-yarn/cache

# Start ResourceManager daemon
yarn resourcemanager
