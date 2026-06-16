#!/usr/bin/env bash

# Minimal env for Spark Standalone + HDFS
export SPARK_MASTER_HOST=spark-master
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export HADOOP_HOME=/opt/hadoop
export LD_LIBRARY_PATH=$HADOOP_HOME/lib/native:$LD_LIBRARY_PATH
export HADOOP_USER_NAME=hadoop

export SPARK_MASTER_PORT=7077
export SPARK_MASTER_WEBUI_PORT=8080
export SPARK_WORKER_WEBUI_PORT=8081
