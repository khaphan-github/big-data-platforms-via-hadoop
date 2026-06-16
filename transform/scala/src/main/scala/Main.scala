import java.util.Properties

import org.apache.spark.sql.{Row, SparkSession}
import org.apache.spark.sql.types._
import vn.hus.nlp.tokenizer.VietTokenizer

object Main {
  private val DEFAULT_HDFS_BASE  = "hdfs://namenode:9000/raw_zone"
  private val DEFAULT_MODELS_DIR = "/tmp/vnlp-models"
  private val DEFAULT_OUTPUT     = "hdfs://namenode:9000/work_zone/table_trending_words_csv"

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
      val path = s"$hdfsBase/$folder/articles.json"
      try {
        val rows = spark.read
          .option("mode", "PERMISSIVE")
          .option("multiline", "true")
          .json(path)
          .select("publish_date", "source", "category", "content")
          .collect()

        rows.foreach { row =>
          val ngay    = str(row, 0)
          val nguon   = str(row, 1)
          val chuDe   = str(row, 2)
          val content = str(row, 3)

          if (content.nonEmpty) {
            tokenizer.segment(content)
              .split("\\s+")
              .filter(_.nonEmpty)
              .foreach { token =>
                val cleanToken = token.replace("_", " ").trim
                val key = (ngay, nguon, chuDe, cleanToken)
                tokenCounts(key) = tokenCounts.getOrElse(key, 0L) + 1L
              }
          }
        }
        println(s"[$folder] processed ${rows.length} articles")
      } catch {
        case e: Exception =>
          println(s"[WARN] Failed to process $folder: ${e.getMessage}")
      }
    }

    val resultRows = tokenCounts.map { case ((ngay, nguon, chuDe, tuKhoa), count) =>
      Row(ngay, nguon, chuDe, tuKhoa, count)
    }.toSeq

    val resultDF = spark.createDataFrame(
      spark.sparkContext.parallelize(resultRows),
      schema
    )
    resultDF.coalesce(1).write.mode("overwrite").option("header", "true").csv(outputPath)
    println(s"Written ${resultRows.size} rows to: $outputPath")

    spark.stop()
  }
}
