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