#!/bin/bash
set -e

NAMENODE_DIR="/var/lib/hadoop-hdfs/cache/dfs/name"
CLUSTER_ID="bigdt-anal-cluster-001"

mkdir -p /var/log/hadoop-hdfs /var/log/hadoop-yarn /var/log/hadoop
chmod 755 /var/log/hadoop* /var/log/hadoop
mkdir -p "${NAMENODE_DIR}"

if [ ! -f "${NAMENODE_DIR}/current/fsimage" ]; then
  echo "[NameNode] First startup: formatting NameNode"
  hdfs namenode -format -force -clusterId "${CLUSTER_ID}" >/dev/null 2>&1
fi

exec hdfs namenode
