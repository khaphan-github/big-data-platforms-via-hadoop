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
