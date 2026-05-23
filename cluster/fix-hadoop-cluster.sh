#!/bin/bash
set -e

docker compose down > /dev/null 2>&1
docker volume rm $(docker volume ls -q | grep hadoop) 2>/dev/null || true
docker compose up namenode -d > /dev/null 2>&1
sleep 5
docker compose exec -T namenode /opt/hadoop/bin/hdfs namenode -format -force > /dev/null 2>&1
docker compose up -d > /dev/null 2>&1
sleep 30
