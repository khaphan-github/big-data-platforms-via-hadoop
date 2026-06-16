#!/usr/bin/env bash
set -euo pipefail

NAMENODE_CONTAINER="${NAMENODE_CONTAINER:-hadoop-namenode}"
HDFS_BASE_PATH="${HDFS_BASE_PATH:-/raw_zone}"

if ! docker ps --format '{{.Names}}' | grep -qx "$NAMENODE_CONTAINER"; then
  echo "[ERROR] Container '$NAMENODE_CONTAINER' is not running."
  echo "Start it first, e.g. docker compose up -d namenode datanode1 datanode2"
  exit 1
fi

echo "[INFO] Creating HDFS input folders under ${HDFS_BASE_PATH}"
docker exec "$NAMENODE_CONTAINER" hdfs dfs -mkdir -p \
  "${HDFS_BASE_PATH}/giai_tri" \
  "${HDFS_BASE_PATH}/cong_nghe" \
  "${HDFS_BASE_PATH}/suc_khoe"

echo "[INFO] Uploading mock data to HDFS"
cat <<'JSON' | docker exec -i "$NAMENODE_CONTAINER" hdfs dfs -put -f - "${HDFS_BASE_PATH}/giai_tri/mock_1.json"
{"publish_date":"2026-05-26","source":"vnexpress","title":"Sao viet ra mat phim moi","content":"Bo phim moi cua sao viet thu hut khan gia va tao xu huong"}
{"publish_date":"2026-05-26","source":"tuoitre","title":"Le hoi am nhac ngoai troi","content":"Dem nhac dong nguoi tham du va nhieu tiet muc an tuong"}
JSON

cat <<'JSON' | docker exec -i "$NAMENODE_CONTAINER" hdfs dfs -put -f - "${HDFS_BASE_PATH}/cong_nghe/mock_1.json"
{"publish_date":"2026-05-26","source":"vnexpress","title":"AI tao dot pha moi","content":"Cong nghe AI ho tro tu dong hoa va nang suat cho doanh nghiep"}
{"publish_date":"2026-05-27","source":"dantri","title":"Dien thoai gap the he moi","content":"Thiet bi moi co camera tot va hieu nang cao"}
JSON

cat <<'JSON' | docker exec -i "$NAMENODE_CONTAINER" hdfs dfs -put -f - "${HDFS_BASE_PATH}/suc_khoe/mock_1.json"
{"publish_date":"2026-05-26","source":"thanhnien","title":"Loi ich cua tap the duc","content":"Tap luyen deu dan giup cai thien suc khoe tim mach"}
{"publish_date":"2026-05-27","source":"tuoitre","title":"Che do an lanh manh","content":"An nhieu rau xanh va ngu coc nguyen hat giup co the khoe manh"}
JSON

echo "[INFO] Verifying uploaded files"
docker exec "$NAMENODE_CONTAINER" hdfs dfs -ls -R "$HDFS_BASE_PATH"

echo "[DONE] Mock data generated on HDFS"
