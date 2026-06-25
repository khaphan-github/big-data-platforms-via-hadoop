import java.util.Properties
import scala.io.{Codec, Source}

import org.apache.spark.sql.{DataFrame, Row, SparkSession}
import org.apache.spark.sql.functions.lit
import org.apache.spark.sql.types._
import vn.hus.nlp.tokenizer.VietTokenizer

object Main {
  private val DEFAULT_HDFS_BASE  = "hdfs://namenode:9000/raw_zone"
  private val DEFAULT_MODELS_DIR = "/tmp/vnlp-models"
  private val DEFAULT_OUTPUT     = "hdfs://namenode:9000/work_zone/table_trending_words_csv"

  private lazy val stopWords: Set[String] = {
    val is = getClass.getResourceAsStream("/stopwords_vi.txt")
    if (is == null) {
      println("[WARN] stopwords_vi.txt not found on classpath")
      Set.empty
    } else {
      Source.fromInputStream(is)(Codec.UTF8).getLines().map(_.dropWhile(_ == '\uFEFF').trim.toLowerCase).filter(_.nonEmpty).toSet
    }
  }

  /** Convert any publish_date format to yyyyMMdd.
   *  Handles: "2026-06-23 10:58:00.0" → "20260623"
   *            "20260531"              → "20260531"
   */
  def formatDate(raw: String): String = {
    if (raw == null || raw.isEmpty) ""
    else if (raw.matches("\\d{8}")) raw
    else raw.take(10).replaceAll("-", "")
  }

  def buildTokenizer(modelsDir: String): VietTokenizer = {
    val props = new Properties()
    props.setProperty("sentDetectionModel", s"$modelsDir/sentDetection/VietnameseSD.bin.gz")
    props.setProperty("lexiconDFA",         s"$modelsDir/tokenization/automata/dfaLexicon.xml")
    props.setProperty("externalLexicon",    s"$modelsDir/tokenization/automata/externalLexicon.xml")
    props.setProperty("normalizationRules", s"$modelsDir/tokenization/normalization/rules.txt")
    props.setProperty("lexers",             s"$modelsDir/tokenization/lexers/lexers.xml")
    props.setProperty("unigramModel",       s"$modelsDir/tokenization/bigram/unigram.xml")
    props.setProperty("bigramModel",        s"$modelsDir/tokenization/bigram/bigram.xml")
    props.setProperty("namedEntityPrefix",  s"$modelsDir/tokenization/prefix/namedEntityPrefix.xml")
    new VietTokenizer(props)
  }

  private def str(row: Row, idx: Int): String =
    if (row.isNullAt(idx)) "" else row.getString(idx)

  private def safeSelect(df: DataFrame, cols: String*): DataFrame = {
    val present = cols.filter(df.columns.contains)
    val missing = cols.filterNot(df.columns.contains)
    missing.foldLeft(df.select(present.map(df(_)): _*)) { (acc, c) =>
      acc.withColumn(c, lit(""))
    }
  }

  def main(args: Array[String]): Unit = {
    val hdfsBase   = if (args.length > 0) args(0) else DEFAULT_HDFS_BASE
    val modelsDir  = if (args.length > 1) args(1) else DEFAULT_MODELS_DIR
    val outputPath = if (args.length > 2) args(2) else DEFAULT_OUTPUT

    val spark = SparkSession.builder()
      .appName("trending-words")
      .config("spark.driver.bindAddress", "0.0.0.0")
      .getOrCreate()

    println(s"Initializing VnTokenizer from: $modelsDir")
    val tokenizer = buildTokenizer(modelsDir)
    println("VnTokenizer ready.")

    val schema = StructType(Seq(
      StructField("ngay",             StringType, nullable = true),
      StructField("nguon",            StringType, nullable = true),
      StructField("chu_de",           StringType, nullable = true),
      StructField("tu_khoa",          StringType, nullable = false),
      StructField("so_lan_xuat_hien", LongType,   nullable = false)
    ))

    // Accumulate (ngay, nguon, chu_de, tu_khoa) -> count across all categories
    val tokenCounts = collection.mutable.HashMap.empty[(String, String, String, String), Long]

    val categories = Seq("giai_tri", "cong_nghe", "suc_khoe")
    categories.foreach { folder =>
      val path = s"$hdfsBase/$folder/*"
      try {
        // We must ensure the columns exist before selecting them, or select them safely.
        // Let's check the schema. If "category" doesn't exist, we can create a dummy column or just select what exists.
        val df = spark.read.option("multiline", "true").json(path)
        val selectedDf = safeSelect(df, "publish_date", "source", "category", "content")
        val rows = selectedDf.collect()

        rows.foreach { row =>
          val ngay    = formatDate(str(row, 0))
          val nguon   = str(row, 1)
          val chuDe   = { val c = str(row, 2); if (c.nonEmpty) c else folder }
          val content = str(row, 3)

          if (content.nonEmpty) {
            val segmented = tokenizer.segment(content)
            if (segmented != null) {
              segmented.split("\\s+")
                .filter(_.nonEmpty)
                .map(_.replace("_", " ").trim.toLowerCase)
                .map(_.replaceAll("[^a-zA-Z0-9ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠ-ỹ ]", "").replaceAll("\\s+", " "))
                .filter(_.nonEmpty)
                .filterNot(stopWords.contains)
                .foreach { cleanToken =>
                  val key = (ngay, nguon, chuDe, cleanToken)
                  tokenCounts(key) = tokenCounts.getOrElse(key, 0L) + 1L
                }
            }
          }
        }
        println(s"[$folder] processed ${rows.length} articles")
      } catch {
        case e: Exception =>
          println(s"[WARN] Failed to process $folder: ${e.getMessage}")
          e.printStackTrace()
      }
    }

    val resultRows = tokenCounts.map { case ((ngay, nguon, chuDe, tuKhoa), count) =>
      Row(ngay, nguon, chuDe, tuKhoa, count)
    }.toSeq

    val resultDF = spark.createDataFrame(
      spark.sparkContext.parallelize(resultRows),
      schema
    )
    resultDF.coalesce(1).write.mode("overwrite").option("header", "true").option("sep", "\t").csv(outputPath)
    println(s"Written ${resultRows.size} rows to: $outputPath")

    spark.stop()
  }
}
