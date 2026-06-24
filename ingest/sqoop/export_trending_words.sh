#!/bin/bash
# =============================================================================
# Flow 2: HDFS → Sqoop → MySQL
# Export kết quả trending words từ HDFS (work_zone) sang MySQL
# Usage: docker exec sqoop /opt/sqoop-scripts/export_trending_words.sh
# =============================================================================

set -e

# ---- Cấu hình ----
MYSQL_HOST="${MYSQL_HOST:-mysql-db}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-rss_password}"
MYSQL_DATABASE="${MYSQL_DATABASE:-rss_ingest}"
TARGET_TABLE="${TARGET_TABLE:-trending_words}"
HDFS_URL="${HDFS_URL:-hdfs://namenode:9000}"
WORK_ZONE_PATH="${WORK_ZONE_PATH:-/work_zone/table_trending_words_csv}"

echo "============================================================"
echo "  Flow 2: HDFS → Sqoop → MySQL (Serving DB)"
echo "  Source: ${HDFS_URL}${WORK_ZONE_PATH}"
echo "  Target: ${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}.${TARGET_TABLE}"
echo "============================================================"

# Ensure JAVA_HOME is configured for ARM64 if running on Apple Silicon inside the cluster
export JAVA_HOME="/usr/lib/jvm/java-8-openjdk-arm64"
export HADOOP_USER_NAME="hadoop"

# ---- Tạo bảng MySQL nếu chưa có ----
echo "[1/5] Chuẩn bị bảng MySQL: ${TARGET_TABLE}..."
sqoop eval \
    --connect "jdbc:mysql://${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}?useSSL=false&allowPublicKeyRetrieval=true" \
    --username "${MYSQL_USER}" \
    --password "${MYSQL_PASSWORD}" \
    --query "CREATE TABLE IF NOT EXISTS ${TARGET_TABLE} (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        ngay         VARCHAR(8)   NOT NULL,
        nguon        VARCHAR(100),
        chu_de       VARCHAR(50),
        tu_khoa      VARCHAR(255) NOT NULL,
        so_lan_xuat_hien BIGINT  DEFAULT 0,
        created_at   TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_ngay (ngay),
        INDEX idx_chu_de (chu_de),
        INDEX idx_tu_khoa (tu_khoa)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
echo "  ✓ Bảng sẵn sàng."

# ---- Truncate bảng trước khi import (overwrite mode) ----
echo "[2/5] Xóa dữ liệu cũ trong bảng ${TARGET_TABLE}..."
sqoop eval \
    --connect "jdbc:mysql://${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}?useSSL=false&allowPublicKeyRetrieval=true" \
    --username "${MYSQL_USER}" \
    --password "${MYSQL_PASSWORD}" \
    --query "TRUNCATE TABLE ${TARGET_TABLE};"
echo "  ✓ Đã xóa dữ liệu cũ."

# ---- Kiểm tra dữ liệu tồn tại trên HDFS ----
echo "[3/5] Kiểm tra dữ liệu trên HDFS: ${WORK_ZONE_PATH}..."
if ! hdfs dfs -test -d "${WORK_ZONE_PATH}" 2>/dev/null; then
    echo "  ✗ Đường dẫn HDFS không tồn tại: ${WORK_ZONE_PATH}"
    echo "  Vui lòng chạy Spark job trước."
    exit 1
fi
echo "  ✓ Đường dẫn HDFS tồn tại."

# ---- Xử lý strip header CSV trên HDFS ----
echo "[4/5] Loại bỏ header của CSV trên HDFS..."
# Spark ghi CSV kèm header=true, Sqoop không hỗ trợ tự động bỏ qua header lúc export
# Nếu có file part-*.csv mới từ Spark, ta tiến hành strip header.
# Nếu không có nhưng có data.csv đã strip trước đó, ta tái sử dụng trực tiếp.
if hdfs dfs -ls "${WORK_ZONE_PATH}/part-*.csv" >/dev/null 2>&1; then
    TEMP_NO_HEADER="/work_zone/table_trending_words_no_header.csv"
    hdfs dfs -cat "${WORK_ZONE_PATH}/part-*.csv" | tail -n +2 | hdfs dfs -put -f - "${TEMP_NO_HEADER}"
    hdfs dfs -rm -r -f "${WORK_ZONE_PATH}"
    hdfs dfs -mkdir -p "${WORK_ZONE_PATH}"
    hdfs dfs -mv "${TEMP_NO_HEADER}" "${WORK_ZONE_PATH}/data.csv"
    echo "  ✓ Bỏ header thành công."
elif hdfs dfs -ls "${WORK_ZONE_PATH}/data.csv" >/dev/null 2>&1; then
    echo "  ✓ data.csv đã sẵn sàng (đã được bỏ header từ trước)."
else
    echo "  ✗ Không tìm thấy dữ liệu CSV để export!"
    exit 1
fi


# ---- Chạy Sqoop export ----
echo "[5/5] Bắt đầu chạy Sqoop export: HDFS → MySQL..."
sqoop export \
    --connect "jdbc:mysql://${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}?useSSL=false&allowPublicKeyRetrieval=true" \
    --username "${MYSQL_USER}" \
    --password "${MYSQL_PASSWORD}" \
    --table "${TARGET_TABLE}" \
    --export-dir "${WORK_ZONE_PATH}" \
    --bindir /opt/sqoop/lib \
    --input-fields-terminated-by '\t' \
    --input-lines-terminated-by '\n' \
    --columns "ngay,nguon,chu_de,tu_khoa,so_lan_xuat_hien" \
    --map-column-java ngay=String,nguon=String,chu_de=String,tu_khoa=String,so_lan_xuat_hien=Long \
    --input-null-string '' \
    --input-null-non-string '' \
    --num-mappers 1

echo "============================================================"
echo "  ✓ Sqoop export hoàn tất!"
echo "============================================================"
