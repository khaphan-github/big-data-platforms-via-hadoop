#!/bin/sh
set -eu

/opt/hive/bin/schematool -dbType postgres -initSchema || true
