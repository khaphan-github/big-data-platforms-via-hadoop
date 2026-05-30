package bigdt.transform.keywords

import org.apache.spark.sql.{SparkSession, DataFrame}
import org.apache.spark.sql.types._
import org.apache.spark.sql.functions._
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.security.UserGroupInformation
import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers
import org.scalatest.{BeforeAndAfterAll, Ignore}

/**
 * Spark integration tests - requires proper Hadoop/YARN environment
 * Skip in local test environments due to Hadoop security constraints with Java 25+
 * Run these tests in a proper Spark/Hadoop cluster or container environment
 */
@Ignore
class TrendingWordsSparkJobSpec extends AnyFlatSpec with Matchers with BeforeAndAfterAll {
  private var spark: SparkSession = _

  override def beforeAll(): Unit = {
    spark = SparkSession
      .builder()
      .appName("trending-words-test")
      .master("local[1]")
      .config("spark.sql.shuffle.partitions", "1")
      .getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
  }

  override def afterAll(): Unit = {
    if (spark != null) {
      spark.stop()
    }
  }

  "TrendingWordsJob" should "union dataframes from multiple categories" in {
    val s = spark
    import s.implicits._
    
    val schema = StructType(Seq(
      StructField("publish_date", StringType, true),
      StructField("source", StringType, true),
      StructField("title", StringType, true),
      StructField("content", StringType, true)
    ))

    val data1 = Seq(
      ("2026-05-28", "ThanhNien", "Tin công nghệ", "Công nghệ mới")
    ).toDF("publish_date", "source", "title", "content")

    val data2 = Seq(
      ("2026-05-28", "TuoiTre", "Phim hay", "Phim mới trên màn ảnh")
    ).toDF("publish_date", "source", "title", "content")

    val df1 = data1.withColumn("chu_de", lit("CongNghe"))
    val df2 = data2.withColumn("chu_de", lit("GiaiTri"))

    val combined = df1.unionByName(df2)
    combined.count() should be(2)
    combined.select("chu_de").distinct().count() should be(2)
  }

  it should "parse dates to yyyyMMdd format" in {
    val s = spark
    import s.implicits._
    
    val data = Seq(
      ("2026-05-28", "ThanhNien", "Title", "Content", "Category")
    ).toDF("publish_date", "source", "title", "content", "chu_de")

    val formatted = data.select(
      date_format(col("publish_date"), "yyyyMMdd").alias("ngay")
    )

    val result = formatted.collect().head.getString(0)
    result should be("20260528")
  }

  it should "combine title and content into full_text" in {
    val s = spark
    import s.implicits._
    
    val data = Seq(
      ("Title text", "Content text")
    ).toDF("title", "content")

    val combined = data.select(
      concat_ws(" ", col("title"), col("content")).alias("full_text")
    )

    val result = combined.collect().head.getString(0)
    result should be("Title text Content text")
  }

  it should "clean regex special characters" in {
    val s = spark
    import s.implicits._
    
    val REGEX_TEXT = """[^a-zA-Z0-9_àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ\s]"""
    val data = Seq(
      ("hello @world! 123 việt #nam")
    ).toDF("text")

    val cleaned = data.select(
      regexp_replace(col("text"), REGEX_TEXT, " ").alias("cleaned")
    )

    val result = cleaned.collect().head.getString(0)
    result should contain("hello")
    result should contain("world")
    result should contain("123")
    result should contain("việt")
  }

  it should "explode array of keywords to multiple rows" in {
    val s = spark
    import s.implicits._
    
    val data = Seq(
      ("20260528", "ThanhNien", "CongNghe", Array("máy", "tính", "phần mềm"))
    ).toDF("ngay", "nguon", "chu_de", "keywords")

    val exploded = data.select(
      col("ngay"),
      col("nguon"),
      col("chu_de"),
      explode(col("keywords")).alias("tu_khoa")
    )

    exploded.count() should be(3)
    exploded.select("tu_khoa").collect().map(_.getString(0)) should contain allOf("máy", "tính", "phần mềm")
  }

  it should "group and count keyword occurrences" in {
    val s = spark
    import s.implicits._
    
    val data = Seq(
      ("20260528", "ThanhNien", "CongNghe", "máy"),
      ("20260528", "ThanhNien", "CongNghe", "máy"),
      ("20260528", "ThanhNien", "CongNghe", "tính"),
      ("20260528", "TuoiTre", "CongNghe", "máy")
    ).toDF("ngay", "nguon", "chu_de", "tu_khoa")

    val grouped = data
      .groupBy("ngay", "nguon", "chu_de", "tu_khoa")
      .count()
      .withColumnRenamed("count", "so_lan_xuat_hien")

    grouped.count() should be(3)
    
    val maxRow = grouped.orderBy(desc("so_lan_xuat_hien")).first()
    maxRow.getLong(maxRow.fieldIndex("so_lan_xuat_hien")) should be(2)
  }
}
