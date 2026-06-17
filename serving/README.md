# ToDO: Draw chart this this data via UI

```sql
CREATE TABLE table_trending_words (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ngay VARCHAR(8) NOT NULL COMMENT 'Date in format yyyyMMdd',
    nguon VARCHAR(100) NOT NULL COMMENT 'Source: ThanhNien, TuoiTre, VNN',
    chu_de VARCHAR(100) NOT NULL COMMENT 'Category: GiaiTri, CongNghe, SucKhoe',
    tu_khoa VARCHAR(255) NOT NULL COMMENT 'Vietnamese keyword',
    so_lan_xuat_hien INT NOT NULL DEFAULT 1 COMMENT 'Occurrence count',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
);

SELECT chu_de, COUNT(\*) as so_luong_tu_khoa
FROM table_trending_words
GROUP BY chu_de;

SELECT tu_khoa, SUM(so_lan_xuat_hien) as tong
FROM table_trending_words
GROUP BY tu_khoa
ORDER BY tong DESC
LIMIT 20;

SELECT chu_de, tu_khoa, SUM(so_lan_xuat_hien) as tong
FROM table_trending_words
GROUP BY chu_de, tu_khoa
ORDER BY chu_de, tong DESC;
```

---

## Huong dan chay serving

Thu muc nay cung cap FastAPI de tao va xem bieu do tu bang `table_trending_words`.

### 1) Cai dat thu vien

Tu thu muc `serving/`:

```bash
python3 -m pip install -r requirements.txt
```

Neu may bao khong co `pip`, dung `python3 -m pip` nhu ben tren.

### 2) Chay API

```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

Neu khong co `uvicorn`, co the chay:

```bash
python3 main.py
```

### 3) Mo trang bieu do

Truy cap:

- http://localhost:5000/charts

### 4) API tao anh bieu do

- `GET /api/charts/pie` - bieu do tron so luong tu khoa theo chu de
- `GET /api/charts/top20` - top 20 tu khoa nhieu nhat
- `GET /api/charts/top10` - top 10 tu khoa theo tung chu de

Sau khi goi API, anh se duoc luu trong `serving/static/`:

- `pie_chart_category.png`
- `top_20_articles.png`
- `top_10_by_category.png`

### 5) Luu y ket noi database

File `db/database.py` dang su dung thong tin MySQL cuc bo. Neu ban chay database khac port, hay cap nhat lai thong so ket noi cho phu hop voi moi truong cua ban.
