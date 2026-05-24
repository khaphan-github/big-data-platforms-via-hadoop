#!/bin/bash
# Download MySQL (only if not exists)
if [ ! -f "mysql-8.0.39-linux-glibc2.28-x86_64.tar.xz" ] && [ ! -d "mysql-8.0.39-linux-glibc2.28-x86_64" ]; then
    echo "[MySQL] Downloading mysql-8.0.39..."
    curl -fSL "https://dev.mysql.com/get/Downloads/MySQL-8.0/mysql-8.0.39-linux-glibc2.28-x86_64.tar.xz" -o "mysql-8.0.39-linux-glibc2.28-x86_64.tar.xz"
    echo "[MySQL] Downloaded successfully"
else
    echo "[MySQL] Already exists, skipping download"
fi

# Download Spark (only if not exists)
if [ ! -f "spark-3.5.0-bin-hadoop3.tgz" ] && [ ! -d "spark-3.5.0-bin-hadoop3" ]; then
    echo "[Spark] Downloading spark-3.5.0..."
    curl -fSL "https://archive.apache.org/dist/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3.tgz" -o "spark-3.5.0-bin-hadoop3.tgz"
    echo "[Spark] Downloaded successfully"
else
    echo "[Spark] Already exists, skipping download"
fi

# Download Hadoop (only if not exists)
if [ ! -f "hadoop-3.3.6.tar.gz" ] && [ ! -d "hadoop-3.3.6" ]; then
    echo "[Hadoop] Downloading hadoop-3.3.6..."
    curl -fSL "https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz" -o "hadoop-3.3.6.tar.gz"
    echo "[Hadoop] Downloaded successfully"
else
    echo "[Hadoop] Already exists, skipping download"
fi

# Download NiFi (only if not exists)
if [ ! -f "nifi-1.25.0-bin.zip" ] && [ ! -d "nifi-1.25.0" ]; then
    echo "[NiFi] Downloading nifi-1.25.0..."
    curl -fSL "https://archive.apache.org/dist/nifi/1.25.0/nifi-1.25.0-bin.zip" -o "nifi-1.25.0-bin.zip"
    echo "[NiFi] Downloaded successfully"
else
    echo "[NiFi] Already exists, skipping download"
fi


