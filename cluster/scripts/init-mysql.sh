#!/bin/bash
set -e

echo "[MySQL] Starting MySQL Server..."
/opt/mysql/bin/mysqld \
    --user=mysql \
    --datadir=/var/lib/mysql \
    --bind-address=0.0.0.0 \
    --port=3306 \
    --default-authentication-plugin=mysql_native_password &

MYSQL_PID=$!

# Wait for MySQL to start
sleep 5

# Create bigdt database and user
echo "[MySQL] Setting up bigdt database and user..."
/opt/mysql/bin/mysql -h127.0.0.1 -P3306 -uroot << EOF
CREATE DATABASE IF NOT EXISTS bigdt DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'bigdt_user'@'%' IDENTIFIED BY 'bigdt_password';
GRANT ALL PRIVILEGES ON bigdt.* TO 'bigdt_user'@'%';
FLUSH PRIVILEGES;
EOF

echo "[MySQL] Setup complete"

# Keep the process in foreground
wait $MYSQL_PID
