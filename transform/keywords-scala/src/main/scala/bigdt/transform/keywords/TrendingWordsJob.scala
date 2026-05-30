package bigdt.transform.keywords

import org.apache.spark.sql.{SparkSession, DataFrame}
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types.ArrayType
import java.io.File

/**
 * BigDT Transform - Trending Keywords Extraction (Scala)
 * Extracts and aggregates Vietnamese keywords from JSON documents in HDFS
 */
object TrendingWordsJob {
  private val REGEX_TEXT = """[^a-zA-Z0-9_àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ\s]"""
  private val DEFAULT_HDFS_BASE = "hdfs://localhost:9870/raw_zone"
  private val DEFAULT_HDFS_OUTPUT = "hdfs://localhost:9870/work_zone/table_trending_words"

  def main(args: Array[String]): Unit = {
    var hdfsBase = sys.env.getOrElse("HDFS_BASE_PATH", DEFAULT_HDFS_BASE)
    var hdfsOutput = sys.env.getOrElse("HDFS_OUTPUT_PATH", DEFAULT_HDFS_OUTPUT)

    if (args.length > 0) hdfsBase = args(0)
    if (args.length > 1) hdfsOutput = args(1)

    runJob(hdfsBase, hdfsOutput)
  }

  def runJob(hdfsBase: String, hdfsOutput: String): Unit = {
    val spark = SparkSession
      .builder()
      .appName("extraction_job:v1.0.0")
      .config("spark.executor.memory", "2g")
      .config("spark.executor.cores", "2")
      .config("spark.driver.memory", "2g")
      .getOrCreate()

    try {
      println("Starting trending words extraction...")
      val categories = Map(
        "giai_tri" -> "GiaiTri",
        "cong_nghe" -> "CongNghe",
        "suc_khoe" -> "SucKhoe"
      )

      // Load all category folders and union them
      val dfs = categories.flatMap { case (folder, catName) =>
        try {
          val path = s"${hdfsBase.stripSuffix("/")}/$folder"
          val df = spark.read
            .option("inferSchema", "true")
            .json(path)
            .withColumn("chu_de", lit(catName))
          Some(df)
        } catch {
          case e: Exception =>
            println(s"[WARN] Failed to load $folder: ${e.getMessage}")
            None
        }
      }.toSeq

      if (dfs.isEmpty) {
        throw new Exception("No data found in any category folder!")
      }

      var df = dfs.reduce(_ unionByName _)
      println(s"Loaded ${df.count()} records")

      // Select and clean columns
      df = df.select(
        date_format(col("publish_date"), "yyyyMMdd").alias("ngay"),
        col("source").alias("nguon"),
        col("chu_de"),
        col("title"),
        col("content")
      )
      
      // Filter for valid dates
      df = df.filter(col("ngay").isNotNull)

      // Combine title and content, clean regex
      df = df.withColumn(
        "full_text",
        regexp_replace(
          concat_ws(" ", col("title"), col("content")),
          REGEX_TEXT,
          " "
        )
      )

      // Extract keywords using UDF
      val extractKeywordsUDF = udf((text: String) => VietnameseTokenizer.extractKeywords(text))
      df = df.withColumn("keywords", extractKeywordsUDF(col("full_text")))

      // Explode keywords to one row per keyword
      df = df.select(
        col("ngay"),
        col("nguon"),
        col("chu_de"),
        explode(col("keywords")).alias("tu_khoa")
      )
      
      // Filter for valid keywords
      df = df.filter(col("tu_khoa").isNotNull)

      // Group by and count occurrences
      val resultDF = df
        .groupBy("ngay", "nguon", "chu_de", "tu_khoa")
        .count()
        .withColumnRenamed("count", "so_lan_xuat_hien")
        .orderBy(desc("so_lan_xuat_hien"))

      // Write output: Parquet (primary) + CSV (secondary)
      resultDF.write.mode("overwrite").parquet(hdfsOutput)
      resultDF.coalesce(1).write.mode("overwrite").option("header", "true").csv(s"${hdfsOutput}_csv")

      println(s"Completed: ${resultDF.count()} keywords")
      resultDF.limit(10).show(truncate = false)

    } catch {
      case e: Exception =>
        println(s"[ERROR] ${e.getMessage}")
        e.printStackTrace()
        throw e
    } finally {
      spark.stop()
    }
  }
}
