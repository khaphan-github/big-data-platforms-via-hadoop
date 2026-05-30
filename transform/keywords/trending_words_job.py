"""BigDT Transform - Trending Keywords Extraction"""
import os, sys
from functools import reduce
from pyvi import ViTokenizer
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, explode, regexp_replace, desc, date_format, udf, concat_ws, lit
from pyspark.sql.types import ArrayType, StringType

REGEX_TEXT = r"[^a-zA-Z0-9_àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ\s]"
def _load_stopwords():
    stopwords = set()
    path = os.path.join(os.path.dirname(__file__), "stopwords_vi.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            stopwords.update(line.strip() for line in f if line.strip())
    except:
        pass
    return stopwords

def tokenize(text):
    if not text or not isinstance(text, str):
        return []
    try:
        return ViTokenizer.tokenize(text).split() if ViTokenizer else text.split()
    except:
        return text.split()

def extract_keywords(text, min_length=2):
    stopwords = _load_stopwords()
    tokens = tokenize(text.lower().strip())
    return [t for t in tokens if t not in stopwords and len(t) > 1 and not t.startswith("http") and len(t) >= min_length]

'''
- Main job function to run the Spark job for trending keywords extraction
- Reads JSON files from HDFS, processes them, and writes results back to HDFS in
'''
def run_job(hdfs_base, hdfs_output):
    spark = SparkSession.builder.appName("extraction_job:v1.0.0").config("spark.executor.memory", "2g").config("spark.executor.cores", "2").config("spark.driver.memory", "2g").getOrCreate()
    
    try:
        print("Starting trending words extraction...")
        categories = {'giai_tri': 'GiaiTri', 'cong_nghe': 'CongNghe', 'suc_khoe': 'SucKhoe'}
        dfs = []
        
        for folder, cat_name in categories.items():
            try:
                df_cat = spark.read.option("inferSchema", "true").json(f"{hdfs_base.rstrip('/')}/{folder}")
                dfs.append(df_cat.withColumn("chu_de", lit(cat_name)))
            except:
                pass
        
        if not dfs:
            raise Exception("No data found!")
        
        df = reduce(DataFrame.unionByName, dfs)
        print(f"Loaded {df.count()} records")
        
        df = df.select(
            date_format(col("publish_date"), "yyyyMMdd").alias("ngay"),
            col("source").alias("nguon"),
            col("chu_de"),
            col("title"),
            col("content")
        ).filter(col("ngay").isNotNull())
        
        df = df.withColumn("full_text",regexp_replace(concat_ws(" ", col("title"), col("content")),REGEX_TEXT," "))
        df = df.withColumn("keywords", udf(extract_keywords, ArrayType(StringType()))(col("full_text")))
        df = df.select(
            col("ngay"), col("nguon"), col("chu_de"), 
            explode(col("keywords")).alias("tu_khoa")
        ).filter(col("tu_khoa").isNotNull())
        
        result_df = df.groupBy("ngay", "nguon", "chu_de", "tu_khoa").count().withColumnRenamed("count", "so_lan_xuat_hien").orderBy(desc("so_lan_xuat_hien"))
        result_df.write.mode("overwrite").parquet(hdfs_output)
        result_df.coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{hdfs_output}_csv")
        
        print(f"✓ Completed: {result_df.count()} keywords")
        result_df.limit(10).show(truncate=False)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    hdfs_base = os.getenv("HDFS_BASE_PATH", "hdfs://localhost:9870/raw_zone")
    hdfs_output = os.getenv("HDFS_OUTPUT_PATH", "hdfs://localhost:9870/work_zone/table_trending_words")
    if len(sys.argv) > 1:
        hdfs_base = sys.argv[1]
    if len(sys.argv) > 2:
        hdfs_output = sys.argv[2]
    run_job(hdfs_base, hdfs_output)