# How to check whether data is saved in HDFS

This guide explains how to verify that ingested articles were written to HDFS in this project.

The pipeline writes committed articles through WebHDFS into a date-partitioned layout:

```text
/data/rss/articles/dt=YYYY-MM-DD/articles_<timestamp>_<uuid>.jsonl
```

Each file is newline-delimited JSON. One line equals one article record.

## 1. Prerequisites

Make sure the ingestion stack is running from `ingest/`:

```bash
docker-compose up -d
```

At minimum, these services must be up:

1. `app`
2. `namenode`
3. `datanode`

Also confirm HDFS is enabled in `.env`:

```env
HDFS_ENABLED=true
HDFS_WEBHDFS_URL=http://namenode:9870
HDFS_ARTICLES_PATH=/data/rss/articles
```

## 2. Confirm that ingestion actually ran

Before checking HDFS, confirm the app completed at least one ingestion cycle.

### Check app logs

```bash
docker-compose logs -f app
```

Look for messages like:

1. `Starting RSS ingestion cycle`
2. `HDFS write complete`
3. `Wrote X articles to HDFS`

### Check ingestion API

```bash
curl http://localhost:8000/api/admin/logs/latest
```

If ingestion succeeded, the latest log should show:

1. `status: success`
2. non-zero `articles_fetched`
3. non-zero `articles_saved`

If `articles_saved` is `0`, nothing will be written to HDFS.

## 3. Check HDFS from the NameNode UI

Open the NameNode web UI:

```text
http://localhost:9870
```

Then browse the file system and inspect:

```text
/data/rss/articles
```

What you should see:

1. One or more `dt=YYYY-MM-DD` folders.
2. Inside each folder, one or more `.jsonl` files.

If the path is empty, the app likely did not write any committed articles yet.

## 4. Check HDFS from the command line

You can inspect HDFS directly from the `namenode` container.

### List the article root path

```bash
docker-compose exec namenode hdfs dfs -ls /data/rss/articles
```

Expected result:

```text
Found N items
drwxr-xr-x   - root supergroup          0 2026-06-14  /data/rss/articles/dt=2026-06-14
```

### List files inside one partition

```bash
docker-compose exec namenode hdfs dfs -ls /data/rss/articles/dt=2026-06-14
```

Expected result:

```text
-rw-r--r--   1 root supergroup       12345 2026-06-14  articles_20260614T120102_abcd1234.jsonl
```

### Preview file content

```bash
docker-compose exec namenode hdfs dfs -cat /data/rss/articles/dt=2026-06-14/articles_20260614T120102_abcd1234.jsonl | head
```

Each line should be valid JSON, for example:

```json
{"id":1,"title":"...","published_date":"2026-06-14T10:15:00","category_name":"Tech"}
```

If the file exists but is empty, the ingestion wrote a file but no article payload was available. That is rare and should be investigated.

## 5. Check with WebHDFS

The app writes through WebHDFS, so you can also query the same API manually.

### List the root directory

```bash
curl "http://localhost:9870/webhdfs/v1/data/rss/articles?op=LISTSTATUS&user.name=root"
```

### Inspect a partition folder

```bash
curl "http://localhost:9870/webhdfs/v1/data/rss/articles/dt=2026-06-14?op=LISTSTATUS&user.name=root"
```

This returns JSON with file metadata. Look for:

1. `pathSuffix`
2. `type`
3. `length`

If WebHDFS returns an error:

1. Check that NameNode is healthy.
2. Verify port `9870` is exposed.
3. Confirm `HDFS_WEBHDFS_URL=http://namenode:9870`.

## 6. Check from BIRT

BIRT should read the same MySQL data as the ingestion app.

Open:

```text
http://localhost:8088
```

Then:

1. Open the report viewer landing page.
2. Preview the mounted `.rptdesign` file.
3. Confirm the report loads data from MySQL without errors.

If you need a quick data check, use a report section or table grouped by `published_date`:

1. Chart type: `Bar Chart`
2. Metric: `COUNT(*)`
3. Group by: `published_date`

If the report is empty:

1. Confirm the HDFS files exist.
2. Restart the BIRT container if the report design or data source changed.

## 8. Common failure cases

### Case 1: MySQL has data but HDFS is empty

Most likely causes:

1. `HDFS_ENABLED` is `false`.
2. The app did not complete a successful ingestion cycle.
3. `HDFS_WEBHDFS_URL` points to the wrong host or port.
4. `namenode` is not healthy.

### Case 2: HDFS folder exists but there are no files

Most likely causes:

1. The batch contained only duplicates.
2. Saving to MySQL failed before HDFS write.
3. The app logged an HDFS error after commit.

### Case 3: HDFS files exist but BIRT is empty

Most likely causes:

1. The report data source points to the wrong MySQL database.
2. The report design was not mounted correctly.
3. The BIRT container could not reach MySQL.

## 9. What to check in the code

The HDFS write path is implemented in:

1. `ingest/services/hdfs_writer.py`
2. `ingest/services/scheduler.py`

The file layout is controlled by:

1. `HDFS_ARTICLES_PATH`
2. article `published_date`
3. `dt=YYYY-MM-DD` partition naming

## 10. Quick checklist

Use this checklist when debugging:

1. `docker-compose ps`
2. `docker-compose logs -f app`
3. `curl http://localhost:8000/api/admin/logs/latest`
4. `docker-compose exec namenode hdfs dfs -ls /data/rss/articles`
5. `docker-compose exec namenode hdfs dfs -ls /data/rss/articles/dt=YYYY-MM-DD`
6. Open `http://localhost:8088` and test a report
