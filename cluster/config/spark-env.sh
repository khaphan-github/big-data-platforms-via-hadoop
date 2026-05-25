#!/usr/bin/env bash

# Set SPARK_MASTER_HOST
export SPARK_MASTER_HOST=spark-master

# Set SPARK_LOCAL_IP for binding to all interfaces
export SPARK_LOCAL_IP=0.0.0.0

# Set Java home
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# Hadoop configuration
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export HADOOP_HOME=/opt/hadoop
export LD_LIBRARY_PATH=$HADOOP_HOME/lib/native:$LD_LIBRARY_PATH

# Spark ports
export SPARK_MASTER_PORT=7077
export SPARK_MASTER_WEBUI_PORT=8080
export SPARK_WORKER_WEBUI_PORT=8081

# Executor and Driver settings (can be overridden in spark-submit)
export SPARK_EXECUTOR_MEMORY=1g
export SPARK_EXECUTOR_CORES=2
export SPARK_DRIVER_MEMORY=1g

# Enable SSH
export SPARK_SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
