"""
Spark Job: Extract Trending Words from Articles
Reads raw article data from HDFS by category,
processes it, and outputs trending keywords
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    explode,
    regexp_replace,
    count,
    desc,
    date_format,
    udf,
    concat_ws,
    lit
)

from pyspark.sql.types import ArrayType, StringType

import os
import sys

from tokenizer_handler import TokenizerHandler


class TrendingWordsSparkJob:
    """
    Spark job to extract and count trending keywords
    from articles
    """

    # Category mapping for HDFS paths
    CATEGORIES = {
        "giai_tri": "GiaiTri",
        "cong_nghe": "CongNghe",
        "suc_khoe": "SucKhoe"
    }

    def __init__(self, hdfs_base_path, hdfs_output_path):
        """
        Initialize Spark job

        Args:
            hdfs_base_path:
                Base path on HDFS
                (e.g., hdfs://namenode:9000/raw_zone)

            hdfs_output_path:
                Destination path on HDFS
                (e.g.,
                hdfs://namenode:9000/work_zone/table_trending_words)
        """

        self.hdfs_base = hdfs_base_path.rstrip("/")
        self.hdfs_output = hdfs_output_path

        self.spark = self._create_spark_session()

        self.tokenizer = TokenizerHandler()

    def _create_spark_session(self):
        """
        Create and configure Spark session
        """

        spark_master = os.getenv(
            "SPARK_MASTER",
            "spark://spark-master:7077"
        )

        return (
            SparkSession.builder
            .appName("TrendingWordsExtraction")
            .master(spark_master)
            .config("spark.executor.memory", "2g")
            .config("spark.executor.cores", "2")
            .config("spark.driver.memory", "2g")
            .config(
                "spark.hadoop.fs.defaultFS",
                "hdfs://namenode:9000"
            )
            .getOrCreate()
        )

    def _extract_keywords_udf(self):
        """
        Create UDF for keyword extraction
        """

        return udf(
            TokenizerHandler.extract_keywords,
            ArrayType(StringType())
        )

    def run(self):
        """
        Execute the trending words extraction job
        """

        try:

            print("=" * 60)
            print("Starting Trending Words Extraction")
            print("=" * 60)

            # =====================================================
            # STEP 1: READ DATA FROM HDFS
            # =====================================================

            dfs = []

            for folder, category_name in self.CATEGORIES.items():

                category_path = f"{self.hdfs_base}/{folder}"

                print(f"Reading: {category_path}")

                try:

                    df_cat = (
                        self.spark.read
                        .option("inferSchema", "true")
                        .json(category_path)
                    )

                    df_cat = df_cat.withColumn(
                        "chu_de",
                        lit(category_name)
                    )

                    dfs.append(df_cat)

                    print(
                        f"Loaded category: {category_name}"
                    )

                except Exception as e:

                    print(
                        f"[WARNING] Cannot read "
                        f"{category_path}"
                    )

                    print(str(e))

            if not dfs:
                raise Exception(
                    "No data could be loaded from HDFS!"
                )

            # =====================================================
            # STEP 2: MERGE DATAFRAMES
            # =====================================================

            from functools import reduce
            from pyspark.sql import DataFrame

            df = reduce(
                DataFrame.unionByName,
                dfs
            )

            total_records = df.count()

            print(f"Total records: {total_records}")

            # =====================================================
            # STEP 3: SELECT REQUIRED COLUMNS
            # =====================================================

            df = (
                df.select(
                    date_format(
                        col("publish_date"),
                        "yyyyMMdd"
                    ).alias("ngay"),

                    col("source").alias("nguon"),

                    col("chu_de"),

                    col("title"),

                    col("content")
                )
                .filter(col("ngay").isNotNull())
            )

            # =====================================================
            # STEP 4: CLEAN TEXT
            # =====================================================

            df = df.withColumn(
                "full_text",

                regexp_replace(

                    concat_ws(
                        " ",
                        col("title"),
                        col("content")
                    ),

                    "[^a-zA-Z0-9_àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ\\s]",

                    " "
                )
            )

            # =====================================================
            # STEP 5: TOKENIZE
            # =====================================================

            extract_keywords_func = (
                self._extract_keywords_udf()
            )

            df = df.withColumn(
                "keywords",
                extract_keywords_func(
                    col("full_text")
                )
            )

            # =====================================================
            # STEP 6: EXPLODE KEYWORDS
            # =====================================================

            df = (
                df.select(
                    col("ngay"),
                    col("nguon"),
                    col("chu_de"),

                    explode(
                        col("keywords")
                    ).alias("tu_khoa")
                )
                .filter(
                    col("tu_khoa").isNotNull()
                )
            )

            # =====================================================
            # STEP 7: COUNT KEYWORDS
            # =====================================================

            result_df = (
                df.groupBy(
                    "ngay",
                    "nguon",
                    "chu_de",
                    "tu_khoa"
                )
                .agg(
                    count("*").alias(
                        "so_lan_xuat_hien"
                    )
                )
                .orderBy(
                    desc("so_lan_xuat_hien")
                )
            )

            # =====================================================
            # STEP 8: WRITE TO HDFS
            # =====================================================

            print(
                f"Writing parquet output:"
                f" {self.hdfs_output}"
            )

            (
                result_df.write
                .mode("overwrite")
                .parquet(self.hdfs_output)
            )

            print(
                f"Writing CSV output:"
                f" {self.hdfs_output}_csv"
            )

            (
                result_df.coalesce(1)
                .write
                .mode("overwrite")
                .option("header", "true")
                .csv(self.hdfs_output + "_csv")
            )

            # =====================================================
            # DONE
            # =====================================================

            total_keywords = result_df.count()

            print("=" * 60)
            print("JOB COMPLETED SUCCESSFULLY")
            print("=" * 60)

            print(
                f"Total keywords: {total_keywords}"
            )

            result_df.show(
                20,
                truncate=False
            )

            return result_df

        except Exception as e:

            print("=" * 60)
            print("[ERROR] SPARK JOB FAILED")
            print("=" * 60)

            print(str(e))

            raise

        finally:

            self.spark.stop()


def main():
    """
    Main entry point
    """

    hdfs_base = os.getenv(
        "HDFS_INPUT",
        "hdfs://namenode:9000/raw_zone"
    )

    hdfs_output = os.getenv(
        "HDFS_OUTPUT",
        "hdfs://namenode:9000/work_zone/table_trending_words"
    )

    # Optional CLI override
    if len(sys.argv) > 1:
        hdfs_base = sys.argv[1]

    if len(sys.argv) > 2:
        hdfs_output = sys.argv[2]

    print(f"HDFS INPUT : {hdfs_base}")
    print(f"HDFS OUTPUT: {hdfs_output}")

    job = TrendingWordsSparkJob(
        hdfs_base,
        hdfs_output
    )

    job.run()


if __name__ == "__main__":
    main()