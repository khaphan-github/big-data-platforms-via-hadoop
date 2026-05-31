package bigdt.transform.keywords

import org.apache.spark.sql.{SparkSession, DataFrame}
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types.ArrayType
import scala.collection.mutable
import scala.collection.JavaConverters._
import scala.io.Source
import vn.pipeline.{VnCoreNLP, Annotation}
import java.io.File

/**
 * BigDT Transform - Trending Keywords Extraction
 * Scala single-file implementation: VnCoreNLP-based Vietnamese NLP + Spark aggregation
 */
object TrendingWordsJob {
  private val REGEX_TEXT = """[^a-zA-Z0-9_àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ\s]"""
  private val DEFAULT_HDFS_BASE = "hdfs://namenode:9000/raw_zone"
  private val DEFAULT_HDFS_OUTPUT = "hdfs://namenode:9000/work_zone/table_trending_words"

  private val stopwordsCache = mutable.Map[String, Set[String]]()
  @transient private lazy val vnPipeline = {
    try {
      Some(new VnCoreNLP(Array("wseg", "pos")))
    } catch {
      case _: Exception => None
    }
  }

  def main(args: Array[String]): Unit = {
    var hdfsBase = sys.env.getOrElse("HDFS_BASE_PATH", DEFAULT_HDFS_BASE)
    var hdfsOutput = sys.env.getOrElse("HDFS_OUTPUT_PATH", DEFAULT_HDFS_OUTPUT)
    if (args.length > 0) hdfsBase = args(0)
    if (args.length > 1) hdfsOutput = args(1)
    runJob(hdfsBase, hdfsOutput)
  }

  private def loadStopwords(): Set[String] = {
    stopwordsCache.getOrElseUpdate("vietnamese", {
      try {
        val resource = getClass.getResourceAsStream("/stopwords_vi.txt")
        if (resource != null) {
          val source = Source.fromInputStream(resource, "UTF-8")
          val stopwords = source.getLines().map(_.trim).filter(_.nonEmpty).toSet
          source.close()
          stopwords
        } else Set.empty[String]
      } catch {
        case _: Exception => Set.empty[String]
      }
    })
  }

  private def extractKeywords(text: String, minWordLength: Int = 2): Array[String] = {
    if (text == null || text.trim.isEmpty) return Array()
    val stopwords = loadStopwords()
    vnPipeline match {
      case Some(pipeline) =>
        try {
          val annotation = new Annotation(text)
          pipeline.annotate(annotation)
          val keywords = mutable.ArrayBuffer[String]()
          
          annotation.getSentences.asScala.foreach { sentence =>
            val words = sentence.getWords.asScala.toList
            
            // Get properly segmented words from VnCoreNLP
            val forms = words.map(w => w.getForm.toLowerCase)
            val posTags = words.map(w => {
              val tag = w.getPosTag
              if (tag != null && tag.nonEmpty) tag.substring(0, 1) else "X"
            })
            
            // Extract noun phrases: N+ (consecutive nouns/adjectives)
            var i = 0
            while (i < forms.length) {
              val pos = posTags(i)
              if (pos == "N" || pos == "A") {
                val phrase = mutable.ArrayBuffer[String]()
                phrase += forms(i)
                var j = i + 1
                while (j < forms.length && (posTags(j) == "N" || posTags(j) == "A")) {
                  phrase += forms(j)
                  j += 1
                }
                val phraseStr = phrase.mkString(" ")
                if (phraseStr.length >= minWordLength && !stopwords.contains(phraseStr))
                  keywords += phraseStr
                i = j - 1
              }
              i += 1
            }
            
            // Extract verb phrases: V+ followed by optional N/A
            i = 0
            while (i < forms.length) {
              val pos = posTags(i)
              if (pos == "V") {
                val phrase = mutable.ArrayBuffer[String]()
                phrase += forms(i)
                var j = i + 1
                while (j < forms.length && posTags(j) == "V") {
                  phrase += forms(j)
                  j += 1
                }
                if (j < forms.length && (posTags(j) == "N" || posTags(j) == "A")) {
                  phrase += forms(j)
                  j += 1
                }
                val phraseStr = phrase.mkString(" ")
                if (phraseStr.length >= minWordLength && !stopwords.contains(phraseStr))
                  keywords += phraseStr
                i = j - 1
              }
              i += 1
            }
            
            // Add individual non-stopword tokens with VnCoreNLP segmentation
            forms.zip(posTags).foreach { case (form, pos) =>
              if (form.length >= minWordLength && !stopwords.contains(form) && (pos == "N" || pos == "A" || pos == "V"))
                keywords += form
            }
          }
          
          if (keywords.nonEmpty) keywords.distinct.toArray else simpleTokenize(text, stopwords, minWordLength)
        } catch {
          case _: Exception => simpleTokenize(text, stopwords, minWordLength)
        }
      case None => simpleTokenize(text, stopwords, minWordLength)
    }
  }

  private def simpleTokenize(text: String, stopwords: Set[String], minWordLength: Int): Array[String] = {
    val tokens = text.toLowerCase.trim.split("\\s+").filter(_.nonEmpty)
    val filtered = tokens.filter(w => w.length >= minWordLength && !stopwords.contains(w))
    val keywords = mutable.ArrayBuffer[String]()
    for (len <- 4 to 2 by -1; i <- 0 to (filtered.length - len))
      keywords += filtered.slice(i, i + len).mkString(" ")
    (keywords ++ filtered).distinct.toArray
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

      if (dfs.isEmpty) throw new Exception("No data found in any category folder!")

      var df = dfs.reduce(_ unionByName _)
      println(s"Loaded ${df.count()} records")

      df = df.select(
        date_format(col("publish_date"), "yyyyMMdd").alias("ngay"),
        col("source").alias("nguon"),
        col("chu_de"),
        col("title"),
        col("content")
      )
      
      df = df.filter(col("ngay").isNotNull)

      df = df.withColumn(
        "full_text",
        regexp_replace(
          concat_ws(" ", col("title"), col("content")),
          REGEX_TEXT,
          " "
        )
      )

      val extractKeywordsUDF = udf((text: String) => extractKeywords(text))
      df = df.withColumn("keywords", extractKeywordsUDF(col("full_text")))

      df = df.select(
        col("ngay"),
        col("nguon"),
        col("chu_de"),
        explode(col("keywords")).alias("tu_khoa")
      )
      
      df = df.filter(col("tu_khoa").isNotNull && length(col("tu_khoa")) >= 2)

      val resultDF = df
        .groupBy("ngay", "nguon", "chu_de", "tu_khoa")
        .count()
        .withColumnRenamed("count", "so_lan_xuat_hien")
        .orderBy(desc("so_lan_xuat_hien"))

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
