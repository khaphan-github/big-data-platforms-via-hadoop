CREATE DATABASE IF NOT EXISTS rss_analytics;

USE rss_analytics;

CREATE EXTERNAL TABLE IF NOT EXISTS rss_articles (
  id BIGINT,
  title STRING,
  slug STRING,
  description STRING,
  content_html STRING,
  link STRING,
  guid STRING,
  author STRING,
  published_date STRING,
  fetched_date STRING,
  feed_source_id INT,
  feed_source_name STRING,
  category_id INT,
  category_name STRING,
  comment_count INT,
  created_at STRING,
  updated_at STRING
)
PARTITIONED BY (dt STRING)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION 'hdfs:///data/rss/articles';

MSCK REPAIR TABLE rss_articles;
