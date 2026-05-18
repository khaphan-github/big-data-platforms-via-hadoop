-- Initialize feed data for RSS ingestion system

INSERT INTO categories (name, slug) VALUES
    ('Giải Trí', 'giai-tri'),
    ('Công Nghệ', 'cong-nghe'),
    ('Sức Khỏe', 'suc-khoe');

INSERT INTO feed_sources (name, url, category_id, is_active) VALUES
    ('Vietnamnet - Giải Trí', 'https://vietnamnet.vn/rss/giai-tri.rss', 1, TRUE),
    ('Thanh Niên - Giải Trí', 'https://thanhnien.vn/rss/giai-tri.rss', 1, TRUE),
    ('Tuổi Trẻ - Giải Trí', 'https://tuoitre.vn/rss/giai-tri.rss', 1, TRUE),
    ('Vietnamnet - Công Nghệ', 'https://vietnamnet.vn/rss/cong-nghe.rss', 2, TRUE),
    ('Thanh Niên - Công Nghệ', 'https://thanhnien.vn/rss/cong-nghe.rss', 2, TRUE),
    ('Tuổi Trẻ - Nhịp Sống Số', 'https://tuoitre.vn/rss/nhip-song-so.rss', 2, TRUE),
    ('Vietnamnet - Sức Khỏe', 'https://vietnamnet.vn/rss/suc-khoe.rss', 3, TRUE),
    ('Thanh Niên - Sức Khỏe', 'https://thanhnien.vn/rss/suc-khoe.rss', 3, TRUE),
    ('Tuổi Trẻ - Sức Khỏe', 'https://tuoitre.vn/rss/suc-khoe.rss', 3, TRUE);
