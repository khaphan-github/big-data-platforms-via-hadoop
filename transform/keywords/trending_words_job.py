"""
Spark Job: Extract Trending Words from Articles
Reads raw article data from HDFS by category, processes it, and outputs trending keywords
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, explode, regexp_replace, count, desc, 
    to_date, date_format, udf, concat_ws, lit
)
from pyspark.sql.types import ArrayType, StringType
import os
import sys
from datetime import datetime
from transform.keywords.tokenizer_handler import TokenizerHandler


class TrendingWordsSparkJob:
    """Spark job to extract and count trending keywords from articles"""
    
    # Category mapping for HDFS paths
    CATEGORIES = {
        'giai_tri': 'GiaiTri',
        'cong_nghe': 'CongNghe',
        'suc_khoe': 'SucKhoe'
    }
    
    def __init__(self, hdfs_base_path, hdfs_output_path):
        """
        Initialize Spark job
        Args:
            hdfs_base_path: Base path on HDFS (e.g., hdfs://namenode:9000/raw_zone)
            hdfs_output_path: Destination path on HDFS (e.g., hdfs://namenode:9000/work_zone/table_trending_words)
        """
        self.hdfs_base = hdfs_base_path.rstrip('/')
        self.hdfs_output = hdfs_output_path
        self.spark = self._create_spark_session()
        self.tokenizer = TokenizerHandler()
    
    def _create_spark_session(self):
        """Create and configure Spark session"""
        return SparkSession.builder \
            .appName("TrendingWordsExtraction") \
            .config("spark.executor.memory", "2g") \
            .config("spark.executor.cores", "2") \
            .config("spark.driver.memory", "2g") \
            .getOrCreate()
    
    def _extract_keywords_udf(self):
        """Create UDF for keyword extraction"""
        return udf(TokenizerHandler.extract_keywords, ArrayType(StringType()))
    
    def run(self):
        """Execute the trending words extraction job"""
        try:
            print(f"Starting trending words extraction...")
            
            # Step 1: Read data from HDFS by category
            dfs = []
            for folder, category_name in self.CATEGORIES.items():
                category_path = f"{self.hdfs_base}/{folder}"
                try:
                    df_cat = self.spark.read.option("inferSchema", "true").json(category_path)
                    df_cat = df_cat.withColumn("chu_de", lit(category_name))
                    dfs.append(df_cat)
                except Exception as e:
                    continue
            
            if not dfs:
                raise Exception("No data could be read!")
            
            from functools import reduce
            from pyspark.sql import DataFrame
            df = reduce(DataFrame.unionByName, dfs)
            print(f"Loaded {df.count()} records")
            
            # Step 2: Parse and extract fields
            df = df.select(
                date_format(col("publish_date"), "yyyyMMdd").alias("ngay"),
                col("source").alias("nguon"),
                col("chu_de"),
                col("title"),
                col("content")
            ).filter(col("ngay").isNotNull())
            
            # Step 3-6: Clean, tokenize, explode, and aggregate
            # ??? stupid
            df = df.withColumn(
                "full_text",
                regexp_replace(
                    concat_ws(" ", col("title"), col("content")),
                    "[^a-zA-Z0-9_àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ\\s]",
                    " ",
                ),
            )
            
            extract_keywords_func = self._extract_keywords_udf()
            df = df.withColumn("keywords", extract_keywords_func(col("full_text")))
            df = df.select(col("ngay"), col("nguon"), col("chu_de"), explode(col("keywords")).alias("tu_khoa")).filter(col("tu_khoa").isNotNull())
            
            # Step 7: Aggregate and write results
            result_df = df.groupBy("ngay", "nguon", "chu_de", "tu_khoa").count().withColumnRenamed("count", "so_lan_xuat_hien").orderBy(desc("so_lan_xuat_hien"))
            
            result_df.write.mode("overwrite").parquet(self.hdfs_output)
            result_df.coalesce(1).write.mode("overwrite").option("header", "true").csv(self.hdfs_output + "_csv")
            
            print(f"Completed! Results: {result_df.count()} keywords")
            result_df.limit(10).show(truncate=False)
            
            return result_df
            
        except Exception as e:
            print(f"[ERROR] Job failed: {str(e)}")
            raise
        finally:
            self.spark.stop()


def main():
    """Main entry point"""
    # Default paths (configurable via arguments)
    hdfs_base = os.getenv("HDFS_BASE_PATH", "hdfs://localhost:9870/raw_zone")
    hdfs_output = os.getenv("HDFS_OUTPUT_PATH", "hdfs://localhost:9870/work_zone/table_trending_words")
    
    # Allow override via command line arguments
    if len(sys.argv) > 1:
        hdfs_base = sys.argv[1]
    if len(sys.argv) > 2:
        hdfs_output = sys.argv[2]
    
    job = TrendingWordsSparkJob(hdfs_base, hdfs_output)
    job.run()

if __name__ == "__main__":
    main()
