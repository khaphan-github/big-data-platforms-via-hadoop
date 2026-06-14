# Hướng dẫn cài đặt hạ tầng xử lý dữ liệu lớn

## 1. Giới thiệu

Tài liệu này hướng dẫn quy trình cài đặt và cấu hình hạ tầng phục vụ nghiên cứu và thử nghiệm các giải pháp xử lý dữ liệu lớn (Big Data). Hạ tầng được triển khai dựa trên nền tảng container hóa Docker, sử dụng Docker Compose để quản lý và điều phối các dịch vụ. Toàn bộ mã nguồn và tệp cấu hình được đặt tại thư mục `cluster/` và được định nghĩa trong tệp `docker-compose.yml`.

## 2. Yêu cầu hệ thống

Trước khi tiến hành cài đặt, máy chủ hoặc máy trạm cần đáp ứng các yêu cầu sau:

- Hệ điều hành: Linux (khuyến nghị Ubuntu 22.04+) hoặc Windows/macOS với WSL2
- **Git** phiên bản 2.30 trở lên
- **Docker Engine** phiên bản 24.0 trở lên
- **Docker Compose Plugin** phiên bản 2.20 trở lên
- Tối thiểu **16 GB RAM** (khuyến nghị 32 GB)
- Tối thiểu **50 GB dung lượng đĩa cứng**

## 3. Kiến trúc hạ tầng

Hạ tầng thử nghiệm bao gồm các thành phần chính sau đây:

### 3.1. HDFS Cluster

HDFS (Hadoop Distributed File System) cung cấp hệ thống lưu trữ phân tán cho dữ liệu lớn, bao gồm:

| Thành phần | Tên container | Cổng | Vai trò |
|---|---|---|---|
| NameNode | `hadoop-namenode` | 9870 (Web UI), 9000 | Quản lý siêu dữ liệu và điều phối truy cập tệp |
| DataNode 1 | `hadoop-datanode1` | 9864 | Lưu trữ dữ liệu vật lý |
| DataNode 2 | `hadoop-datanode2` | 9865 | Lưu trữ dữ liệu vật lý |

### 3.2. Spark Cluster

Apache Spark đảm nhận vai trò xử lý tính toán phân tán trên nền tảng HDFS, bao gồm:

| Thành phần | Tên container | Cổng | Vai trò |
|---|---|---|---|
| Spark Master | `spark-master` | 8080 (Web UI), 7077 (giao tiếp), 4040 | Điều phối tác vụ tính toán |
| Spark Worker 1 | `spark-worker1` | 8081 | Thực thi tác vụ (8 GB, 8 CPU) |
| Spark Worker 2 | `spark-worker2` | 8082 | Thực thi tác vụ |

### 3.3. Apache NiFi

Apache NiFi (cổng 8161) là công cụ thu thập, luân chuyển và xử lý luồng dữ liệu giữa các hệ thống. Container có tên `nifi`, hỗ trợ kết nối với MySQL thông qua driver JDBC đã được tích hợp sẵn.

### 3.4. Cơ sở dữ liệu MySQL

Thành phần MySQL bao gồm hai cơ sở dữ liệu riêng biệt:

- **mysql-db** (cổng 3306): Cơ sở dữ liệu chính phục vụ hạ tầng Hadoop/Spark
- **rss_mysql** (cổng 3308): Cơ sở dữ liệu phục vụ ứng dụng thu thập dữ liệu RSS

### 3.5. Ứng dụng thu thập dữ liệu (Ingest)

Container `rss_app` (cổng 8000) là ứng dụng thu thập dữ liệu từ các nguồn RSS. Ứng dụng được cấu hình linh hoạt thông qua các biến môi trường bao gồm tần suất thu thập, số lần thử lại và thời gian chờ.

### 3.6. Sơ đồ kết nối

```
Internet
    │
    ▼
┌──────────────────────┐
│   Ingest App (:8000) │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    RSS MySQL (:3308)  │
└──────────────────────┘

┌──────────────────────┐
│   Apache NiFi (:8161) │
└──┬───────┬───────┬───┘
   │       │       │
   ▼       ▼       ▼
┌─────────────────────────────────┐
│    HDFS Cluster                 │
│  ┌──────────┐  ┌────────────┐  │
│  │ NameNode │  │ DataNode 1 │  │
│  │ (:9870)  │  │ (:9864)    │  │
│  └──────────┘  └────────────┘  │
│                 ┌────────────┐  │
│                 │ DataNode 2 │  │
│                 │ (:9865)    │  │
│                 └────────────┘  │
└─────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│   Spark Cluster                 │
│  ┌──────────┐  ┌────────────┐  │
│  │  Master  │  │ Worker 1   │  │
│  │ (:8080)  │  │ (:8081)    │  │
│  └──────────┘  └────────────┘  │
│                 ┌────────────┐  │
│                 │ Worker 2   │  │
│                 │ (:8082)    │  │
│                 └────────────┘  │
└─────────────────────────────────┘

┌──────────────────────┐
│  MySQL DB (:3306)    │
└──────────────────────┘
```

## 4. Quy trình cài đặt

Quy trình cài đặt được thực hiện tuần tự theo các bước dưới đây.

### Bước 1: Cài đặt các gói phụ thuộc

#### 1.1. Cài đặt Git

Git là công cụ quản lý phiên bản, được sử dụng để tải mã nguồn của dự án từ kho lưu trữ.

**Trên Ubuntu/Debian:**

```bash
sudo apt update && sudo apt install -y git
```

**Trên CentOS/RHEL/Fedora:**

```bash
sudo yum install -y git
```

Kiểm tra phiên bản Git sau khi cài đặt:

```bash
git --version
```

#### 1.2. Cài đặt Docker Engine

**Trên Ubuntu/Debian:**

```bash
# Cài đặt các gói phụ thuộc
sudo apt update && sudo apt install -y ca-certificates curl

# Thêm kho lưu trữ Docker chính thức
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Cài đặt Docker
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**Trên CentOS/RHEL/Fedora:**

```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl start docker && sudo systemctl enable docker
```

#### 1.3. Phân quyền người dùng cho Docker

Để tránh phải sử dụng `sudo` khi chạy các lệnh Docker, thêm người dùng hiện tại vào nhóm `docker`:

```bash
sudo usermod -aG docker $USER
```

**Lưu ý:** Sau khi thực hiện lệnh trên, nghiên cứu viên cần đăng xuất và đăng nhập lại (hoặc khởi động lại phiên làm việc) để thay đổi có hiệu lực.

#### 1.4. Kiểm tra Docker và Docker Compose

Xác nhận Docker Engine và Docker Compose đã được cài đặt thành công:

```bash
docker --version
docker compose version
```

Kết quả mong đợi:

```
Docker version 24.0.7, build afdd53b
Docker Compose version v2.24.1
```

### Bước 2: Tải mã nguồn từ kho lưu trữ

Sao chép (clone) mã nguồn dự án từ kho lưu trữ Git về máy:

```bash
git clone <địa_chỉ_kho_lưu_trữ>
```

Chuyển vào thư mục dự án:

```bash
cd bigdt-anal
```

Kiểm tra cấu trúc thư mục:

```bash
ls -la
```

Thư mục dự án bao gồm các thành phần chính:

```
bigdt-anal/
├── cluster/              # Dockerfiles và cấu hình Hadoop, Spark, NiFi, MySQL
├── docs/                 # Tài liệu hướng dẫn
├── ingest/               # Mã nguồn ứng dụng thu thập dữ liệu RSS
├── orchestration/        # Mã nguồn điều phối luồng xử lý
├── serving/              # Mã nguồn phục vụ dữ liệu
├── transform/            # Mã nguồn biến đổi dữ liệu
├── docker-compose.yml    # Định nghĩa toàn bộ hạ tầng container
└── .env                  # Cấu hình biến môi trường
```

### Bước 3: Cấu hình biến môi trường (tùy chọn)

Tạo tệp `.env` từ tệp mẫu (nếu có) hoặc tạo mới:

```bash
# Tạo tệp .env với cấu hình mặc định
cat > .env << EOF
MYSQL_PASSWORD=rss_password
MYSQL_DATABASE=rss_ingest
INGEST_INTERVAL_MINUTES=5
DEBUG=false
LOG_LEVEL=INFO
EOF
```

Các biến môi trường này sẽ được Docker Compose tự động nạp khi khởi động.

### Bước 4: Xây dựng các image Docker

Do hạ tầng sử dụng các image Docker được xây dựng tùy chỉnh, nghiên cứu viên cần xây dựng các image cơ sở trước tiên:

```bash
docker compose --profile build-only build hadoop-base spark-base
```

Lệnh trên sẽ xây dựng hai image nền tảng:
- `cluster-hadoop-3.3.6:base`: Image cơ sở chứa Hadoop 3.3.6
- `cluster-spark-3.5.0:base`: Image cơ sở chứa Spark 3.5.0

Sau khi đã có image cơ sở, tiến hành xây dựng các image cho từng dịch vụ:

```bash
docker compose build namenode datanode1 datanode2 spark-master spark-worker1 spark-worker2 nifi mysql ingest-app
```

**Thời gian thực hiện:** Quá trình xây dựng image có thể kéo dài từ 10 đến 30 phút tùy thuộc vào cấu hình máy và tốc độ kết nối mạng, do quá trình tải xuống các gói phụ thuộc (Hadoop, Spark, NiFi, MySQL) và biên dịch.

### Bước 5: Khởi động toàn bộ hạ tầng

Khởi động tất cả các dịch vụ:

```bash
docker compose up -d
```

Tham số `-d` cho phép các container chạy ở chế độ nền (detached mode). Quá trình khởi động có thể mất từ 2 đến 5 phút do các dịch vụ cần thời gian khởi tạo và chờ kiểm tra sức khỏe (healthcheck) theo thứ tự phụ thuộc.

Để theo dõi quá trình khởi động trong thời gian thực:

```bash
docker compose logs -f
```

### Bước 6: Kiểm tra trạng thái các dịch vụ

#### 6.1. Kiểm tra bằng dòng lệnh

Liệt kê trạng thái của tất cả các container:

```bash
docker compose ps
```

Kết quả mong đợi: tất cả các dịch vụ đều ở trạng thái `Up` (hoặc `Healthy`).

Kiểm tra chi tiết từng container:

```bash
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

#### 6.2. Kiểm tra sức khỏe HDFS

```bash
docker exec hadoop-namenode hdfs dfsadmin -report
```

Kết quả mong đợi: hiển thị thông tin về dung lượng, số lượng DataNode đang hoạt động và trạng thái khối dữ liệu.

#### 6.3. Kiểm tra Spark

```bash
docker exec spark-master spark-submit --version
```

#### 6.4. Kiểm tra cơ sở dữ liệu MySQL

```bash
docker exec mysql-db mysqladmin ping -h 127.0.0.1 -u root
```

#### 6.5. Kiểm tra qua giao diện web

Nghiên cứu viên có thể truy cập giao diện web của từng dịch vụ để xác nhận hoạt động:

| Dịch vụ | URL | Chỉ dẫn kiểm tra |
|---|---|---|
| HDFS NameNode | `http://localhost:9870` | Vào mục "Datanodes" để xem danh sách DataNode |
| Spark Master | `http://localhost:8080` | Kiểm tra trạng thái Workers và số lượng CPU/RAM khả dụng |
| Apache NiFi | `http://localhost:8161/nifi` | Truy cập thành công hiển thị giao diện kéo-thả luồng dữ liệu |
| Ingest API | `http://localhost:8000/docs` | Giao diện Swagger hiển thị danh sách API endpoint |

#### 6.6. Kiểm tra khả năng ghi dữ liệu lên HDFS

```bash
# Tạo thư mục trên HDFS
docker exec hadoop-namenode hdfs dfs -mkdir -p /user/bigdata

# Ghi tệp thử nghiệm
echo "Hello Big Data" | docker exec -i hadoop-namenode hdfs dfs -put - /user/bigdata/test.txt

# Đọc lại tệp
docker exec hadoop-namenode hdfs dfs -cat /user/bigdata/test.txt

# Xóa tệp thử nghiệm
docker exec hadoop-namenode hdfs dfs -rm /user/bigdata/test.txt
```

## 5. Cấu hình tùy chỉnh

### 5.1. Biến môi trường

Ứng dụng thu thập dữ liệu RSS hỗ trợ các biến môi trường sau (có thể đặt trong tệp `.env` tại thư mục gốc):

| Biến | Giá trị mặc định | Mô tả |
|---|---|---|
| `MYSQL_USER` | `root` | Tên người dùng MySQL |
| `MYSQL_PASSWORD` | `rss_password` | Mật khẩu MySQL |
| `MYSQL_DATABASE` | `rss_ingest` | Tên cơ sở dữ liệu |
| `INGEST_INTERVAL_MINUTES` | `1` | Tần suất thu thập (phút) |
| `MAX_RETRIES` | `4` | Số lần thử lại tối đa |
| `REQUEST_TIMEOUT_SECONDS` | `10` | Thời gian chờ yêu cầu (giây) |
| `DEBUG` | `false` | Chế độ gỡ lỗi |
| `LOG_LEVEL` | `INFO` | Mức độ ghi log |

Ví dụ tệp `.env`:

```bash
MYSQL_PASSWORD=rss_password
MYSQL_DATABASE=rss_ingest
INGEST_INTERVAL_MINUTES=5
DEBUG=false
LOG_LEVEL=INFO
```

### 5.2. Tài nguyên Spark Worker

Tài nguyên của Spark Worker 1 được cấu hình mặc định với 8 GB RAM và 8 CPU. Nghiên cứu viên có thể điều chỉnh các giá trị này trong tệp `docker-compose.yml` tại phần `spark-worker1`:

```yaml
spark-worker1:
  environment:
    - SPARK_WORKER_MEMORY=8g
    - SPARK_WORKER_CORES=8
  deploy:
    resources:
      limits:
        memory: 8g
        cpus: "8"
```

## 6. Lưu ý khi triển khai

### 6.1. Thứ tự khởi động

Docker Compose đã được cấu hình thứ tự khởi động thông qua mệnh đề `depends_on` kết hợp với `condition: service_healthy`. Cụ thể:

- DataNode chỉ khởi động sau khi NameNode đã sẵn sàng
- Spark Master chỉ khởi động sau khi NameNode đã sẵn sàng
- Spark Worker chỉ khởi động sau khi Spark Master đã sẵn sàng

### 6.2. Dữ liệu bền vững

Dữ liệu của các dịch vụ được lưu trữ trong các Docker volume riêng biệt, đảm bảo dữ liệu không bị mất khi container khởi động lại. Danh sách các volume bao gồm:

```
datanode1-data      datanode2-data
spark-master-work   spark-master-logs
spark-worker1-work  spark-worker1-logs
spark-worker2-work  spark-worker2-logs
nifi-data           nifi-conf         nifi-logs
mysql-data          mysql-logs
ingest-mysql-data
```

### 6.3. Dừng và dọn dẹp

Để dừng toàn bộ hạ tầng mà vẫn giữ dữ liệu:

```bash
docker compose down
```

Để dừng và xóa toàn bộ dữ liệu (bao gồm volume):

```bash
docker compose down -v
```

**Cảnh báo**: Lệnh `docker compose down -v` sẽ xóa vĩnh viễn toàn bộ dữ liệu lưu trữ trong các volume. Chỉ sử dụng lệnh này khi nghiên cứu viên chắc chắn muốn khởi tạo lại toàn bộ trạng thái ban đầu.

## 7. Xử lý sự cố thường gặp

### 7.1. Container không khởi động được

Kiểm tra log của container:

```bash
docker compose logs <tên_dịch_vụ>
```

Ví dụ:

```bash
docker compose logs namenode
```

### 7.2. Xung đột cổng (port)

Nếu một số cổng đã được sử dụng bởi ứng dụng khác trên máy chủ, nghiên cứu viên có thể thay đổi cổng ánh xạ trong tệp `docker-compose.yml`. Ví dụ, thay đổi cổng 8080 thành 8088:

```yaml
spark-master:
  ports:
    - "8088:8080"
```

### 7.3. HDFS ở chế độ Safe Mode sau khởi động

Trong một số trường hợp, HDFS có thể khởi động ở chế độ Safe Mode. Để thoát khỏi chế độ này:

```bash
docker exec hadoop-namenode hdfs dfsadmin -safemode leave
```

## 8. Tài liệu tham khảo

- Docker Compose: https://docs.docker.com/compose/
- Apache Hadoop: https://hadoop.apache.org/
- Apache Spark: https://spark.apache.org/
- Apache NiFi: https://nifi.apache.org/
