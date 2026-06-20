#!/bin/bash
# =============================================================================
# Flow 2: HDFS → Sqoop → MySQL
# Export kết quả trending words từ HDFS (work_zone) sang MySQL
# Usage: docker exec sqoop /opt/sqoop-scripts/export_trending_words.sh
# =============================================================================

set -e

# ---- Cấu hình ----
MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-rss_password}"
MYSQL_DATABASE="${MYSQL_DATABASE:-rss_ingest}"
TARGET_TABLE="${TARGET_TABLE:-trending_words}"
HDFS_URL="${HDFS_URL:-hdfs://namenode:9000}"
WORK_ZONE_PATH="${WORK_ZONE_PATH:-/work_zone/table_trending_words_csv}"

echo "============================================================"
echo "  Flow 2: HDFS → Sqoop → MySQL"
echo "  Source: ${HDFS_URL}${WORK_ZONE_PATH}"
echo "  Target: ${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}.${TARGET_TABLE}"
echo "============================================================"

# ---- Tạo bảng MySQL nếu chưa có ----
echo "[1/4] Chuẩn bị bảng MySQL: ${TARGET_TABLE}..."
mysql -h "${MYSQL_HOST}" -P "${MYSQL_PORT}" -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" \
    "${MYSQL_DATABASE}" <<EOF
CREATE TABLE IF NOT EXISTS ${TARGET_TABLE} (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    ngay         VARCHAR(8)   NOT NULL COMMENT 'Ngày thống kê (yyyyMMdd)',
    nguon        VARCHAR(100) COMMENT 'Nguồn tin',
    chu_de       VARCHAR(50)  COMMENT 'Chủ đề',
    tu_khoa      VARCHAR(255) NOT NULL COMMENT 'Từ khóa',
    so_lan_xuat_hien BIGINT  DEFAULT 0 COMMENT 'Số lần xuất hiện',
    created_at   TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ngay (ngay),
    INDEX idx_chu_de (chu_de),
    INDEX idx_tu_khoa (tu_khoa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Trending keywords from Spark job';
EOF
echo "  ✓ Bảng sẵn sàng."

# ---- Truncate bảng trước khi import (overwrite mode) ----
echo "[2/4] Xóa dữ liệu cũ trong bảng ${TARGET_TABLE}..."
mysql -h "${MYSQL_HOST}" -P "${MYSQL_PORT}" -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" \
    "${MYSQL_DATABASE}" -e "TRUNCATE TABLE ${TARGET_TABLE};"
echo "  ✓ Đã xóa dữ liệu cũ."

# ---- Kiểm tra dữ liệu tồn tại trên HDFS ----
echo "[3/4] Kiểm tra dữ liệu trên HDFS: ${WORK_ZONE_PATH}..."
if ! hdfs dfs -test -d "${WORK_ZONE_PATH}" 2>/dev/null; then
    echo "  ✗ Đường dẫn HDFS không tồn tại: ${WORK_ZONE_PATH}"
    echo "  Vui lòng chạy Spark job trước."
    exit 1
fi
echo "  ✓ Đường dẫn HDFS tồn tại."

# ---- Chạy Sqoop export ----
echo "[4/4] Chạy Sqoop export: HDFS → MySQL..."
sqoop export \
    --connect "jdbc:mysql://${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}?useSSL=false&allowPublicKeyRetrieval=true" \
    --username "${MYSQL_USER}" \
    --password "${MYSQL_PASSWORD}" \
    --table "${TARGET_TABLE}" \
    --export-dir "${WORK_ZONE_PATH}" \
    --input-fields-terminated-by ',' \
    --input-lines-terminated-by '\n' \
    --input-optionally-enclosed-by '"' \
    --columns "ngay,nguon,chu_de,tu_khoa,so_lan_xuat_hien" \
    --skip-dist-cache \
    --num-mappers 1 \
    2>&1

echo "============================================================"
echo "  ✓ Sqoop export hoàn tất!"
echo "  Kiểm tra: mysql -h ${MYSQL_HOST} -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}"
echo "            SELECT COUNT(*) FROM ${TARGET_TABLE};"
echo "============================================================"
