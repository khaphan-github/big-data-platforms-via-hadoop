# Huong dan chay end-to-end: thu thap du lieu -> HDFS -> BIRT

Tai lieu nay huong dan cach chay dung luong hien co trong thu muc `ingest/`:

1. Thu RSS feed va luu vao MySQL.
2. Ghi cac ban ghi da commit sang HDFS duoi dang `jsonl`.
3. Dung BIRT de ve report va chart tu MySQL.

## 1. Tong quan luong xu ly

Khi `ingest/main.py` khoi dong, ung dung se:

1. Khoi tao schema MySQL.
2. Seed du lieu nguon RSS neu can.
3. Tu dong bat scheduler ingestion.

Moi chu ky ingestion chay theo `INGEST_INTERVAL_MINUTES` va thuc hien:

1. Fetch RSS feed.
2. Clean va process du lieu.
3. Kiem tra duplicate.
4. Luu article moi vao MySQL.
5. Neu `HDFS_ENABLED=true`, ghi article da commit sang HDFS.

Du lieu tren HDFS duoc ghi theo mau:

```text
/data/rss/articles/dt=YYYY-MM-DD/articles_<timestamp>_<uuid>.jsonl
```

## 2. Kien truc dich vu

Trong `ingest/docker-compose.yml`, cac service chinh la:

1. `mysql`: luu metadata va article trong MySQL.
2. `app`: FastAPI ingestion service, scheduler, HDFS writer.
3. `namenode`: HDFS NameNode, expose WebHDFS o port `9870`.
4. `datanode`: HDFS DataNode.
5. `birt`: dashboard va chart.

## 3. Yeu cau truoc khi chay

Can co:

1. Docker va Docker Compose hoat dong binh thuong.
2. Neu dung macOS Apple Silicon va gap `exec format error`, hay dam bao compose dang ep `linux/amd64` cho cac image Hadoop nhu file hien tai.
3. Kiem tra cac port chua bi trung:
   - `8000` cho API
   - `8088` cho BIRT
   - `9870` cho NameNode / WebHDFS
   - `3308` cho MySQL expose ra host

## 4. Cau hinh moi truong

Lam viec trong thu muc `ingest/`:

```bash
cp .env.example .env
```

## 5. Cac bien can chu y

Tai lieu nay tap trung vao cac bien lien quan den HDFS/BIRT:

```env
HDFS_ENABLED=true
HDFS_WEBHDFS_URL=http://namenode:9870
HDFS_USER=root
HDFS_ARTICLES_PATH=/data/rss/articles
HDFS_TIMEOUT_SECONDS=30

BIRT_REPORTS_DIR=/opt/birt/reports
BIRT_DEFAULT_REPORT=rss_articles_dashboard.rptdesign
BIRT_VIEWER_CONTEXT=/birt
```

Neu muon test nhanh ingestion, co the giam interval xuong `1` phut:

```env
INGEST_INTERVAL_MINUTES=1
```

## 6. Khoi dong he thong

Chay toan bo stack trong thu muc `ingest/`:

```bash
docker-compose up -d --build
```

Neu ban chi muon quay lai sau khi da build image, co the dung:

```bash
docker-compose up -d
```

## 7. Kiem tra service da len

Kiem tra trang thai:

```bash
docker-compose ps
```

Kiem tra API:

```bash
curl http://localhost:8000/api/health
```

Kiem tra scheduler:

```bash
curl http://localhost:8000/api/admin/scheduler/status
```

Neu can bat lai scheduler:

```bash
curl -X POST http://localhost:8000/api/admin/scheduler/start
```

## 8. Giai thich scheduler ingestion

Scheduler da duoc auto-start trong `ingest/main.py`, nen thong thuong ban khong can goi API start thu cong. Tuy nhien, API van co san de:

1. Xac nhan scheduler dang chay.
2. Bat lai scheduler neu no bi dung.
3. Tat scheduler khi can debug.

Neu ban moi start stack va chua thay du lieu ngay, hay doi toi chu ky tiep theo. Neu muon test nhanh, ha `INGEST_INTERVAL_MINUTES` xuong `1` va restart `app`.

## 9. Kiem tra du lieu da vao MySQL

Xem log ingestion:

```bash
docker-compose logs -f app
```

Xem ingestion log gan nhat:

```bash
curl http://localhost:8000/api/admin/logs/latest
```

Xem danh sach feed:

```bash
curl http://localhost:8000/api/admin/feeds
```

Neu ingest thanh cong, ban se thay thong tin:

1. `articles_fetched`
2. `articles_saved`
3. `duplicates_found`

## 10. Ghi du lieu sang HDFS

Khi `HDFS_ENABLED=true`, ung dung se goi `HDFSWriter` de ghi cac article da commit sang WebHDFS.

Co che ghi:

1. Nhom article theo ngay `published_date`.
2. Neu `published_date` null, fallback sang `fetched_date`.
3. Tao partition `dt=YYYY-MM-DD`.
4. Ghi file `.jsonl` vao partition do.

Moi dong trong file la 1 JSON object, phu hop cho luu tru tuan tu va truy van sau nay.

## 11. Kiem tra HDFS

Neu ban chi muon verify file da duoc ghi vao HDFS, xem [CHECK_HDFS_DATA.md](CHECK_HDFS_DATA.md).

Mo NameNode UI:

```text
http://localhost:9870
```

Hoac kiem tra tu CLI trong container:

```bash
docker-compose exec namenode hdfs dfs -ls /data/rss/articles
```

Mot partition mau se co dang:

```text
/data/rss/articles/dt=2026-06-14/
```

Va ben trong co file:

```text
articles_20260614T123456_<uuid>.jsonl
```

## 12. Xac nhan BIRT da san sang doc report

Mo BIRT portal:

```text
http://localhost:8088
```

Container `birt` duoc cau hinh de:

1. Host BIRT viewer tren port `8088`.
2. Mount report designs tu `./birt/reports`.
3. Ket noi MySQL truc tiep trong runtime.

Neu report chua hien, can build lai service:

```bash
docker-compose up -d --build birt
```

## 13. Cach ve report

Sau khi vao BIRT, lam theo cac buoc sau:

1. Mo report design `rss_articles_dashboard.rptdesign`.
2. Kiem tra data source tro den `mysql:3306/rss_ingest`.
3. Chay report hoac preview chart.

### Chart 1: So luong bai theo category

1. Chart type: `Bar Chart`.
2. Metric: `COUNT(*)`.
3. Group by: `category_name`.
4. Sort: theo metric giam dan.

Muc dich: biet category nao dang co nhieu bai nhat.

### Chart 2: So luong bai theo feed

1. Chart type: `Pie Chart` hoac `Bar Chart`.
2. Metric: `COUNT(*)`.
3. Group by: `feed_source_name`.

Muc dich: do nhieu luong cua tung nguon RSS.

### Chart 3: Trend theo ngay

1. Chart type: `Line Chart` hoac `Time-series Bar Chart`.
2. Time column: `dt`.
3. Metric: `COUNT(*)`.

Muc dich: xem xu huong bai viet theo ngay ingest.

### Chart 4: Bai moi nhat theo thoi gian

Neu muon chart theo ngay pub:

1. Group by `published_date` neu du lieu co format on dinh.
2. Neu khong, uu tien `fetched_date`.

## 14. Goiy report

Nen tao report gom 3 widget:

1. `Articles by category`
2. `Articles by feed`
3. `Articles per day`

Neu muon them 1 widget chi tiet:

1. `Top articles` theo `title` hoac `feed_source_name`
2. `Latest articles` theo `published_date`

## 15. Vi du query trong MySQL

Neu ban muon kiem tra truc tiep du lieu trong MySQL:

```sql
SELECT dt, COUNT(*) AS article_count
FROM rss_articles
GROUP BY dt
ORDER BY dt;
```

```sql
SELECT category_name, COUNT(*) AS article_count
FROM rss_articles
GROUP BY category_name
ORDER BY article_count DESC;
```

```sql
SELECT feed_source_name, COUNT(*) AS article_count
FROM rss_articles
GROUP BY feed_source_name
ORDER BY article_count DESC;
```

## 16. Luot chay de test nhanh

Neu ban muon test tu dau den cuoi trong lan dau tien, thu tu hop ly la:

1. `cp .env.example .env`
2. `docker-compose up -d --build`
3. `docker-compose ps`
4. `curl http://localhost:8000/api/health`
5. `curl http://localhost:8000/api/admin/scheduler/status`
6. `docker-compose logs -f app`
7. Cho ingestion cycle chay xong
8. Mo `http://localhost:9870` de kiem tra HDFS
9. Mo `http://localhost:8088` de xem report

## 18. Troubleshooting

### `exec format error`

Nguyen nhan thuong gap:

1. Image chay sai kien truc CPU.
2. Thieu `platform: linux/amd64` tren service Hadoop.

### `Connection refused` toi HDFS hoac BIRT

Nguyen nhan thuong gap:

1. Service chua healthy.
2. BIRT chay truoc khi MySQL san sang.
3. Sai `MYSQL_HOST`, `MYSQL_PORT`, hoac `HDFS_WEBHDFS_URL`.

### Khong co du lieu trong BIRT

Kiem tra:

1. `app` da ingest thanh cong.
2. Da co file trong `/data/rss/articles/dt=...`.
3. BIRT runtime va report design da duoc mount dung vi tri.
4. Data source trong report tro den MySQL ingestion database.

### Ingestion co du lieu MySQL nhung HDFS rong

Kiem tra:

1. `HDFS_ENABLED=true`
2. `HDFS_WEBHDFS_URL=http://namenode:9870`
3. `namenode` dang chay va WebHDFS truy cap duoc
4. BIRT report design chua tro dung du lieu nguon.

## 19. Khoi dung va dua ve trang thai sach

Dung toan bo stack:

```bash
docker-compose down
```

Neu muon xoa luon volume du lieu:

```bash
docker-compose down -v
```

## 20. Tom tat ngan gon

1. Chay `docker-compose up -d --build` trong `ingest/`.
2. Doi `app` auto-start scheduler va ingest feed.
3. Kiem tra HDFS tai `http://localhost:9870`.
4. Kiem tra BIRT tai `http://localhost:8088`.
5. Mo report `rss_articles_dashboard.rptdesign`.
