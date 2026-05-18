#!/bin/bash
# Run Trending Words Scheduler
# Usage: ./run_scheduler.sh [hdfs_input] [hdfs_output] [interval_seconds]

set -e

# Default values
HDFS_INPUT="${1:-hdfs://namenode:9000/raw_zone}"
HDFS_OUTPUT="${2:-hdfs://namenode:9000/work_zone/table_trending_words}"
SCHEDULE_INTERVAL="${3:-3600}"

export HDFS_INPUT=$HDFS_INPUT
export HDFS_OUTPUT=$HDFS_OUTPUT
export SCHEDULE_INTERVAL=$SCHEDULE_INTERVAL

echo "=========================================="
echo "Starting Trending Words Scheduler"
echo "=========================================="
echo "HDFS Input:      $HDFS_INPUT"
echo "HDFS Output:     $HDFS_OUTPUT"
echo "Schedule Interval: $SCHEDULE_INTERVAL seconds"
echo "=========================================="

python scheduler.py "$HDFS_INPUT" "$HDFS_OUTPUT" "$SCHEDULE_INTERVAL"
