FROM python:3.9-slim

# Install system dependencies + Java
RUN apt-get update && apt-get install -y \
    default-jdk \
    procps \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH=$JAVA_HOME/bin:$PATH

# Install Spark
RUN wget https://archive.apache.org/dist/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3.tgz && \
    tar -xzf spark-3.5.0-bin-hadoop3.tgz && \
    mv spark-3.5.0-bin-hadoop3 /opt/spark && \
    rm spark-3.5.0-bin-hadoop3.tgz

ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH

# Working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install schedule requests pyvi

# Copy application files
COPY tokenizer_handler.py .
COPY trending_words_job.py .
COPY scheduler.py .
COPY stopwords_vi.txt .

# Environment variables
ENV HDFS_INPUT=hdfs://namenode:9000/raw_zone
ENV HDFS_OUTPUT=hdfs://namenode:9000/work_zone/table_trending_words
ENV SPARK_MASTER=spark://spark-master:7077
ENV EXECUTOR_MEMORY=2G
ENV EXECUTOR_CORES=2
ENV SCHEDULE_INTERVAL=3600

# Start app
ENTRYPOINT ["python", "scheduler.py"]