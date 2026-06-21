#!/usr/bin/env bash
set -e
cd "$(cd "$(dirname "$0")" && pwd)"
JAR_NAME="transform-keyword-version-10-56-21-06-2026"
sbt clean assembly
docker cp "$JAR_NAME.jar" spark-master:/tmp/scala-assembly.jar
docker cp libs/vntokenizer4.1/models spark-master:/tmp/vnlp-models
