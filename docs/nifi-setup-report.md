# Báo cáo Cấu hình hệ thống Ingestion qua Apache NiFi

Tài liệu này tổng hợp toàn bộ các bước và cấu hình đã thực hiện để thiết lập thành công luồng đồng bộ dữ liệu tự động từ MySQL (`rss_ingest`) lên HDFS (`/raw_zone`) thông qua Apache NiFi.

---

## 1. Sơ đồ luồng dữ liệu (Data Pipeline)

```
[MySQL: rss_ingest] 
       │
       ▼ (Tạo 3 View lọc theo chủ đề & chuẩn hóa cột)
[MySQL Views: v_articles_...]
       │
       ▼ (NiFi QueryDatabaseTable - Tần suất 10s, dùng ID tăng dần)
[NiFi: Query_...] 
       │
       ▼ (ConvertAvroToJSON - Định dạng JSON Lines)
[NiFi: ConvertAvroToJSON_...] 
       │
       ▼ (PutHDFS - Đọc cấu hình từ core-site.xml & hdfs-site.xml)
[NiFi: PutHDFS_...] 
       │
       ▼ (Ghi dữ liệu thô với quyền 777)
[HDFS: /raw_zone/<chu_de>]
```

---

## 2. Bước 1: Tạo các View chuẩn hóa trong MySQL

Để giải quyết sự lệch pha về tên cột và định dạng thư mục HDFS mà Spark Job yêu cầu, các View sau đã được tạo trực tiếp trong MySQL (`rss_ingest`):

```sql
USE rss_ingest;

-- View Giải Trí (giai-tri -> giai_tri)
CREATE OR REPLACE VIEW v_articles_giai_tri AS
SELECT 
    a.id,
    a.published_date AS publish_date,
    f.name AS source,
    a.title AS title,
    a.description AS content
FROM articles a
JOIN feed_sources f ON a.feed_source_id = f.id
JOIN categories c ON a.category_id = c.id
WHERE c.slug = 'giai-tri';

-- View Công Nghệ (cong-nghe -> cong_nghe)
CREATE OR REPLACE VIEW v_articles_cong_nghe AS
SELECT 
    a.id,
    a.published_date AS publish_date,
    f.name AS source,
    a.title AS title,
    a.description AS content
FROM articles a
JOIN feed_sources f ON a.feed_source_id = f.id
JOIN categories c ON a.category_id = c.id
WHERE c.slug = 'cong-nghe';

-- View Sức Khỏe (suc-khoe -> suc_khoe)
CREATE OR REPLACE VIEW v_articles_suc_khoe AS
SELECT 
    a.id,
    a.published_date AS publish_date,
    f.name AS source,
    a.title AS title,
    a.description AS content
FROM articles a
JOIN feed_sources f ON a.feed_source_id = f.id
JOIN categories c ON a.category_id = c.id
WHERE c.slug = 'suc-khoe';
```

---

## 3. Bước 2: Đồng bộ tệp cấu hình Hadoop vào NiFi

Để processor `PutHDFS` nhận diện được NameNode (`hdfs://namenode:9000`), các tệp cấu hình Hadoop đã được sao chép trực tiếp từ Host vào thư mục cấu hình của container NiFi:

```bash
docker cp cluster/config/core-site.xml nifi:/opt/nifi-1.25.0/conf/core-site.xml
docker cp cluster/config/hdfs-site.xml nifi:/opt/nifi-1.25.0/conf/hdfs-site.xml
```

---

## 4. Bước 3: Tự động hóa thiết lập NiFi qua API

Một kịch bản Python [setup_nifi_flow.py](file:///Users/mew/Developer/big-data-platforms-via-hadoop/cluster/tests/setup_nifi_flow.py) đã được xây dựng và thực thi để tự động cấu hình NiFi thông qua REST API (`http://localhost:8161/nifi-api`):

1. **Khởi tạo DBCPConnectionPool:** 
   - URL: `jdbc:mysql://ingest-mysql:3306/rss_ingest`
   - Driver Class: `com.mysql.cj.jdbc.Driver`
   - User: `root` / Pass: `rss_password`
2. **Khởi tạo 3 luồng xử lý riêng biệt cho 3 chủ đề:**
   - **QueryDatabaseTable:** Thiết lập các thuộc tính kết nối động, chỉ truy vấn dữ liệu mới tăng dần dựa trên khóa chính `id`.
   - **ConvertAvroToJSON:** Cấu hình `"JSON container options"` thành `"none"` (tương đương với định dạng `JSON Lines` - mỗi dòng một JSON object).
   - **PutHDFS:** Cấu hình đường dẫn Hadoop XML resources tại `/opt/nifi-1.25.0/conf/...` và ghi đè thư mục đích tương ứng (`/raw_zone/giai_tri`, `/raw_zone/cong_nghe`, `/raw_zone/suc_khoe`).
3. **Liên kết & Khởi chạy:** Tự động kết nối các processor với nhau qua quan hệ `success` và chuyển đổi tất cả sang trạng thái `RUNNING`.

---

## 5. Bước 4: Khởi tạo và Cấp quyền thư mục HDFS

Để tránh lỗi phân quyền ghi (`AccessControlException` vì NiFi mặc định chạy với user `nifi` trong container), các thư mục đích trên HDFS đã được khởi tạo trước và cấp quyền truy cập rộng rãi (`777`):

```bash
# Tạo thư mục phân vùng dữ liệu thô
docker exec -e HADOOP_CONF_DIR=/tmp/hadoop-conf hadoop-namenode hdfs dfs -mkdir -p /raw_zone/giai_tri /raw_zone/cong_nghe /raw_zone/suc_khoe

# Cấp quyền ghi cho mọi user
docker exec -e HADOOP_CONF_DIR=/tmp/hadoop-conf hadoop-namenode hdfs dfs -chmod -R 777 /raw_zone
```

---

## 6. Bước 5: Kích hoạt đồng bộ dữ liệu lịch sử

Để đảm bảo toàn bộ **2186 bài viết** đã lưu trong MySQL trước đó được NiFi thu thập ngay lập tức, một kịch bản [reset_nifi_state.py](file:///Users/mew/Developer/big-data-platforms-via-hadoop/cluster/tests/reset_nifi_state.py) đã được khởi chạy để dừng các processor `QueryDatabaseTable`, xóa toàn bộ cache trạng thái (`state`) và khởi động lại. 

NiFi đã ngay lập tức fetch toàn bộ dữ liệu lịch sử và ghi lên HDFS thành công.

---

## 7. Kết quả kiểm tra lưu trữ trên HDFS

Kiểm tra bằng WebHDFS API cho thấy dữ liệu đã được ghi hoàn tất với kích thước chuẩn xác:

* Thư mục `/raw_zone/giai_tri` chứa tệp tin JSON Lines kích thước **443.8 KB** (1,050 bài viết).
* Thư mục `/raw_zone/cong_nghe` chứa tệp tin JSON Lines kích thước **36.5 KB**.
* Thư mục `/raw_zone/suc_khoe` chứa tệp tin JSON Lines kích thước **458.4 KB**.

Hạ tầng hiện tại đã sẵn sàng phục vụ các tác vụ phân tích từ khóa bằng Spark Job.
