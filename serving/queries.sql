-- Task 1: So luong tu khoa theo chu de
SELECT chu_de, COUNT(DISTINCT tu_khoa) AS so_luong_tu_khoa
FROM table_trending_words
GROUP BY chu_de;

-- Task 2: Top 20 tu khoa tat ca chu de
SELECT tu_khoa, SUM(so_lan_xuat_hien) AS tong_so_lan
FROM table_trending_words
GROUP BY tu_khoa
ORDER BY tong_so_lan DESC
LIMIT 20;

-- Task 3: Top 10 tu khoa moi chu de (du lieu nguon)
SELECT chu_de, tu_khoa, SUM(so_lan_xuat_hien) AS tong_so_lan
FROM table_trending_words
GROUP BY chu_de, tu_khoa
ORDER BY chu_de, tong_so_lan DESC;
