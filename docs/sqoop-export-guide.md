# Hướng dẫn chạy Flow 2: HDFS → Spark → Sqoop → MySQL (Serving DB)

Tài liệu này hướng dẫn chi tiết cách cấu hình, chuẩn bị hạ tầng, và thực thi luồng chuyển dịch dữ liệu kết quả phân tích từ **HDFS** qua **Spark** và **Sqoop** vào **MySQL Serving DB** (`mysql-db`).

---

## 1. Tổng quan Kiến trúc dữ liệu của dự án

Hệ thống sử dụng **2 database MySQL hoàn toàn độc lập** để đảm bảo tách biệt giữa dữ liệu thô và dữ liệu phục vụ:

| Tên Service (Compose) | Tên Container | Cổng Host | Vai trò |
| :--- | :--- | :--- | :--- |
| `ingest-mysql` | `mysql` | `3308` | **Ingestion DB**: Lưu trữ dữ liệu thô từ RSS feeds (Flow 1). |
| `mysql` | `mysql-db` | `3306` | **Serving DB**: Lưu trữ kết quả thống kê `trending_words` (Flow 2). |

**Lưu ý quan trọng:** Không sử dụng hostname `mysql` trong cấu hình Sqoop vì DNS Docker sẽ bị tranh chấp (round-robin) giữa container mang tên `mysql` và service mang tên `mysql`. Luôn chỉ định rõ **`mysql-db`** để kết nối Serving DB.

---

## 2. Chuẩn bị trước khi chạy lần đầu tiên

Thực hiện lần lượt các bước chuẩn bị hạ tầng dưới đây từ máy host của bạn:

### Bước 2.1: Khởi động các container liên quan
Đảm bảo Spark, HDFS, Serving DB và Sqoop đang chạy:
```bash
docker-compose up -d spark-master spark-worker1 spark-worker2 namenode datanode1 datanode2 mysql sqoop
```

### Bước 2.2: Vá lỗi Classpath Dependency của Sqoop
Mặc định, container Sqoop bị thiếu thư viện xử lý chuỗi của Hadoop Yarn dẫn đến lỗi `ClassNotFoundException: org.apache.commons.lang.StringUtils`. Bạn cần copy file `.jar` từ Hadoop sang thư viện của Sqoop:
```bash
docker exec -u 0 sqoop cp /opt/hadoop-3.2.1/share/hadoop/yarn/timelineservice/lib/commons-lang-2.6.jar /opt/sqoop/lib/
```
*(Cần thực hiện lại bước này nếu bạn dùng lệnh `docker-compose down -v` hoặc huỷ/recreate container Sqoop).*

---

## 3. Các bước thực thi End-to-End (Flow 2)

Sau khi hạ tầng sẵn sàng, quy trình chạy luồng phân tích và export gồm 2 bước:

### Bước 3.1: Chạy Spark Job để phân tích Trending Words
Spark Job sẽ đọc dữ liệu bài viết thô từ `/raw_zone` trên HDFS, tách từ khóa tiếng Việt (Tokenization), đếm số lần xuất hiện, nhóm theo nguồn/chủ đề và xuất ra định dạng Parquet cùng CSV (có kèm header) trên HDFS tại `/work_zone/table_trending_words_csv`.

Chạy lệnh dưới đây từ máy host:
```bash
bash transform/keywords/e2e/02_run_job.sh
```
*Thời gian chạy dự kiến: **50 - 80 giây**.*

### Bước 3.2: Chạy Sqoop Export sang MySQL Serving DB
Chạy script tự động hóa để dọn dẹp dữ liệu cũ, xử lý định dạng HDFS và nạp dữ liệu vào MySQL:
```bash
docker exec sqoop /opt/sqoop-scripts/export_trending_words.sh
```
*Thời gian chạy dự kiến: **10 - 15 giây**.*

---

## 4. Cơ chế hoạt động của Script Tự động hóa Sqoop

Script `/opt/sqoop-scripts/export_trending_words.sh` đã được thiết kế lại hoàn chỉnh và chạy an toàn (idempotent) với các tác vụ tự động sau:

1. **Khởi tạo bảng (Auto-DDL):** Sử dụng `sqoop eval` để tạo bảng `trending_words` trên Serving DB (`mysql-db`) nếu bảng chưa tồn tại (không cần tạo thủ công).
2. **Dọn dẹp bảng (Truncate):** Sử dụng `sqoop eval` để xóa dữ liệu cũ trước khi nạp dữ liệu mới.
3. **Xử lý CSV Header (Idempotent):**
   * Do Spark xuất CSV kèm header (`ngay,nguon...`), Sqoop sẽ bị lỗi parse dữ liệu nếu đọc trúng dòng này.
   * Script tự động kiểm tra: Nếu thấy file `part-*.csv` mới từ Spark, nó sẽ dùng lệnh `tail -n +2` để loại bỏ dòng header đầu tiên, lưu thành một file sạch duy nhất `data.csv`.
   * Nếu chạy lại export mà không chạy Spark, script sẽ giữ nguyên `data.csv` đã xử lý trước đó mà không làm trống file.
4. **Biên dịch cấu trúc cột đúng thứ tự (Query-based Codegen):**
   * Sqoop mặc định biên dịch Java ORM class (`trending_words`) theo thứ tự bảng chữ cái của các cột trong DB. Điều này gây lệch cột nghiêm trọng so với cấu trúc file CSV.
   * Script sử dụng `sqoop codegen` kèm tham số `--query` chọn đúng 5 cột đích theo thứ tự chính xác của CSV để sinh ra file ORM riêng biệt (`trending_words_query.jar`).
5. **MapReduce Export:** Chạy Sqoop export song song dùng 1 mapper đẩy dữ liệu cực nhanh vào MySQL Serving DB.

---

## 5. Xác minh dữ liệu đã vào Serving DB

Sau khi chạy xong Sqoop Export, bạn có thể kiểm tra dữ liệu bằng các lệnh sau:

**1. Đếm tổng số bản ghi đã nạp:**
```bash
docker exec -i mysql-db mysql -u root -prss_password rss_ingest -e "SELECT COUNT(*) FROM trending_words;"
```

**2. Xem thử 5 bản ghi đầu tiên để xác thực ánh xạ cột:**
```bash
docker exec -i mysql-db mysql -u root -prss_password rss_ingest -e "SELECT * FROM trending_words LIMIT 5;"
```
*Kết quả mẫu chính xác:*
```text
id   ngay       nguon                  chu_de    tu_khoa   so_lan_xuat_hien   created_at
1    20260615   Vietnamnet - Sức Khỏe  SucKhoe   người     51                 2026-06-20 12:13:38
2    20260619   Vietnamnet - Sức Khỏe  SucKhoe   người     34                 2026-06-20 12:13:38
```
Dữ liệu cột `id` tự tăng và `created_at` tự động sinh thời gian chèn vào database thành công!
