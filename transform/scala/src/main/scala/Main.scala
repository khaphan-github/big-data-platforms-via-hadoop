import vn.hus.nlp.tokenizer.segmenter.Segmenter
import scala.collection.mutable
import scala.io.Source
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._

object Main {
  private val DEFAULT_HDFS_BASE = "hdfs://localhost:9000/raw_zone"
  private val DEFAULT_HDFS_OUTPUT = "hdfs://localhost:9000/work_zone"
  private val REGEX_TEXT = "[^a-zA-Z0-9àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ\\s]"

  // Load stopwords from resources file
  def loadStopwords(): Set[String] = {
    try {
      val resourceStream = getClass.getResourceAsStream("/stopwords_vi.txt")
      if (resourceStream != null) {
        val stopwords = scala.io.Source.fromInputStream(resourceStream, "UTF-8")
          .getLines()
          .map(_.trim.toLowerCase)
          .filter(_.nonEmpty)
          .toSet
        resourceStream.close()
        println(s"Loaded ${stopwords.size} stopwords from resources")
        stopwords
      } else {
        println("Stopwords file not found in resources, using empty set")
        Set()
      }
    } catch {
      case e: Exception =>
        println(s"Error loading stopwords: ${e.getMessage}")
        Set()
    }
  }

  def extractKeywords(text: String, stopwords: Set[String], minFreq: Int = 2): Seq[(String, Int)] = {
    try {
      val segmenter = new Segmenter()
      val segmentations = segmenter.segment(text)
      
      // Get words from first segmentation
      val words = if (segmentations != null && segmentations.size() > 0) {
        segmentations.iterator.next().toSeq
      } else {
        Seq()
      }
      
      // Filter stopwords, remove punctuation and count frequency
      val keywordFreq = mutable.Map[String, Int]()
      words.foreach { word =>
        // Remove punctuation and normalize
        val cleanWord = word
          .replaceAll("[.,:;!?()\\[\\]\"]", "")
          .toLowerCase()
          .trim()
        
        if (!stopwords.contains(cleanWord) && cleanWord.length > 1) {
          keywordFreq(cleanWord) = keywordFreq.getOrElse(cleanWord, 0) + 1
        }
      }
      
      // Sort by frequency (descending)
      keywordFreq
        .filter { case (_, freq) => freq >= minFreq }
        .toSeq
        .sortBy { case (_, freq) => -freq }
    } catch {
      case e: Exception =>
        println(s"Error: ${e.getMessage}")
        e.printStackTrace()
        Seq()
    }
  }

  /**
   * Spark IO
   */

  def sparkContext(): SparkSession = {
    SparkSession.builder()
      .appName("keyword_extractor:v1.2.0")
      .config("spark.executor.memory", "3g")
      .config("spark.executor.cores", "4")
      .config("spark.driver.memory", "2g")
      .config("spark.sql.adaptive.enabled", "true")
      .getOrCreate()
  }

  def loadDataFromHdfs(spark: SparkSession, hdfsBase: String): org.apache.spark.sql.DataFrame = {
    val categories = Map(
      "giai_tri" -> "Entertainment",
      "cong_nghe" -> "Technology",
      "suc_khoe" -> "Health"
    )

    val dfs = categories.flatMap { case (folder, catName) =>
      try {
        // Read from local filesystem instead of HDFS to avoid RPC issues
        val localPath = s"${hdfsBase.stripSuffix("/")}/$folder/articles.json"
        println(s"Reading from: $localPath")
        val df = spark.read
          .schema(
            "id STRING, title STRING, content STRING, source STRING, category STRING, publish_date STRING, url STRING, author STRING, created_at STRING"
          )
          .option("mode", "PERMISSIVE")
          .json(localPath)
        val count = df.count()
        println(s"Loaded $folder: $count records")
        Some(df)
      } catch {
        case e: Exception =>
          e.printStackTrace()
          println(s"[WARN] Failed to load $folder: ${e.getClass.getName} - ${e.getMessage}")
          None
      }
    }.toSeq

    if (dfs.isEmpty) throw new Exception("No data found in any category!")
    
    val df = dfs.reduce(_ unionByName _)
    println(s"Total loaded: ${df.count()} records")
    df
  }

  def processAndCleanData(df: org.apache.spark.sql.DataFrame): org.apache.spark.sql.DataFrame = {
    df.select(
      date_format(col("publish_date"), "yyyyMMdd").alias("ngay"),
      col("source").alias("nguon"),
      col("category").alias("chu_de"),
      col("title"),
      col("content")
    )
    .filter(col("ngay").isNotNull)
    .withColumn(
      "full_text",
      regexp_replace(
        concat_ws(" ", col("title"), col("content")),
        REGEX_TEXT,
        " "
      )
    )
  }

  def extractKeywordsToArray(df: org.apache.spark.sql.DataFrame, stopwords: Set[String]): org.apache.spark.sql.DataFrame = {
    val extractKeywordsUDF = udf((text: String) => {
      extractKeywords(text, stopwords, minFreq = 2)
        .map { case (word, freq) => word }
    })
    df.withColumn("keywords", extractKeywordsUDF(col("full_text")))
  }

  def explodeAndFilterKeywords(df: org.apache.spark.sql.DataFrame): org.apache.spark.sql.DataFrame = {
    df.select(
      col("ngay"),
      col("nguon"),
      col("chu_de"),
      explode(col("keywords")).alias("tu_khoa")
    )
    .filter(col("tu_khoa").isNotNull && length(col("tu_khoa")) >= 2)
  }

  def aggregateKeywords(df: org.apache.spark.sql.DataFrame): org.apache.spark.sql.DataFrame = {
    df.groupBy("ngay", "nguon", "chu_de", "tu_khoa")
      .count()
      .withColumnRenamed("count", "so_lan_xuat_hien")
      .orderBy(desc("so_lan_xuat_hien"))
  }

  def writeResults(resultDF: org.apache.spark.sql.DataFrame, hdfsOutput: String): Unit = {
    println(s"Writing results to $hdfsOutput")
    resultDF.write.mode("overwrite").parquet(hdfsOutput)
    resultDF.coalesce(1).write.mode("overwrite").option("header", "true").csv(s"${hdfsOutput}_csv")
    println(s"Completed: ${resultDF.count()} trending keywords extracted")
    resultDF.limit(10).show(truncate = false)
  }

  def runJob(hdfsBase: String, hdfsOutput: String): Unit = {
    val spark = sparkContext()
    val stopwords = loadStopwords()

    try {
      // 1. READ HDFS
      var df = loadDataFromHdfs(spark, hdfsBase)

      // 2. MAP REDUCE PIPELINE
      df = processAndCleanData(df)
      df = extractKeywordsToArray(df, stopwords)
      df = explodeAndFilterKeywords(df)
      val resultDF = aggregateKeywords(df)

      // 3. WRITE OUTPUT
      writeResults(resultDF, hdfsOutput)

    } catch {
      case e: Exception =>
        println(s"[ERROR] ${e.getMessage}")
        e.printStackTrace()
        throw e
    } finally {
      spark.stop()
    }
  }

  def main(args: Array[String]): Unit = {
    val hdfsBase   = if (args.length > 0) args(0) else DEFAULT_HDFS_BASE
    val hdfsOutput = if (args.length > 1) args(1) else DEFAULT_HDFS_OUTPUT
    
    println(s"HDFS Base: $hdfsBase")
    println(s"HDFS Output: $hdfsOutput")
    
    runJob(hdfsBase, hdfsOutput)
  }
}