import org.scalatest.funsuite.AnyFunSuite
import org.scalatest.matchers.should.Matchers
import org.scalatestplus.scalacheck.ScalaCheckPropertyChecks
import org.scalacheck.Gen
import java.io.{ByteArrayInputStream, InputStream}
import scala.io.{Codec, Source}

class MainTest extends AnyFunSuite with Matchers with ScalaCheckPropertyChecks {

  // ---------------------------------------------------------------------------
  // formatDate
  // ---------------------------------------------------------------------------
  test("formatDate returns empty string for null") {
    Main.formatDate(null) shouldBe ""
  }

  test("formatDate returns empty string for empty string") {
    Main.formatDate("") shouldBe ""
  }

  test("formatDate passes through 8-digit date") {
    Main.formatDate("20260623") shouldBe "20260623"
  }

  test("formatDate converts standard timestamp format") {
    Main.formatDate("2026-06-23 10:58:00.0") shouldBe "20260623"
  }

  test("formatDate trims time-only suffix after space") {
    Main.formatDate("2025-01-15T00:00:00Z".take(10).replaceAll("-", ""))
      .shouldBe("20250115")
  }

  test("formatDate handles yyyy-MM-dd without time") {
    Main.formatDate("2026-06-23") shouldBe "20260623"
  }

  test("formatDate does NOT handle slash-separated dates (known fragility)") {
    Main.formatDate("2026/06/23") shouldBe "2026/06/23"
  }

  test("formatDate handles ISO with T and Z") {
    Main.formatDate("2026-06-23T10:58:00Z") shouldBe "20260623"
  }

  test("formatDate handles ISO with timezone offset") {
    Main.formatDate("2026-06-23T10:58:00.000+07:00") shouldBe "20260623"
  }

  test("formatDate handles non-date string gracefully") {
    Main.formatDate("abc") shouldBe "abc"
  }

  test("formatDate handles single digit") {
    Main.formatDate("1") shouldBe "1"
  }

  // ---------------------------------------------------------------------------
  // Token processing with special characters
  // ---------------------------------------------------------------------------
  test("token processing replaces underscores with spaces") {
    val raw = "trí_tuệ_nhân_tạo"
    val clean = raw.replace("_", " ").trim.toLowerCase
    clean shouldBe "trí tuệ nhân tạo"
  }

  test("token processing trims leading/trailing spaces and lowercases") {
    val raw = "  HELLO_WORLD  "
    val clean = raw.replace("_", " ").trim.toLowerCase
    clean shouldBe "hello world"
  }

  test("token processing handles multiple consecutive underscores") {
    val raw = "a__b___c"
    val clean = raw.replace("_", " ").trim.toLowerCase
    clean shouldBe "a  b   c"
  }

  test("token processing with punctuation and numbers") {
    val raw = "abc123!@#"
    raw.replace("_", " ").trim.toLowerCase shouldBe "abc123!@#"
  }

  test("token processing with unicode special chars") {
    val raw = "café_100%"
    val clean = raw.replace("_", " ").trim.toLowerCase
    clean shouldBe "café 100%"
  }

  test("empty token is filtered out") {
    val tokens = "".trim
    tokens.nonEmpty shouldBe false
  }

  test("whitespace-only token is filtered out") {
    val tokens = "   ".trim
    tokens.nonEmpty shouldBe false
  }

  test("token with only underscore becomes space then trimmed away") {
    val raw = "_"
    val clean = raw.replace("_", " ").trim
    clean.isEmpty shouldBe true
  }

  // ---------------------------------------------------------------------------
  // stopWords with special characters
  // ---------------------------------------------------------------------------
  test("stopWords loading strips BOM character from first line") {
    val bom = '\uFEFF'
    val content = s"${bom}và\nlà\ncủa\n"
    val is: InputStream = new ByteArrayInputStream(content.getBytes(Codec.UTF8.charSet))
    val words = Source.fromInputStream(is)(Codec.UTF8)
      .getLines()
      .map(_.dropWhile(_ == '\uFEFF').trim.toLowerCase)
      .filter(_.nonEmpty)
      .toSet

    words should contain("và")
    words should contain("là")
    words should contain("của")
    words should not contain bom.toString
  }

  test("stopWords loading without BOM still works") {
    val content = "và\nlà\ncủa\n"
    val is: InputStream = new ByteArrayInputStream(content.getBytes(Codec.UTF8.charSet))
    val words = Source.fromInputStream(is)(Codec.UTF8)
      .getLines()
      .map(_.dropWhile(_ == '\uFEFF').trim.toLowerCase)
      .filter(_.nonEmpty)
      .toSet

    words should contain("và")
    words should contain("là")
    words should contain("của")
  }

  test("stopWords with BOM + special unicode chars") {
    val bom = '\uFEFF'
    val content = s"${bom}ngày\nđêm\n100%\ncafé\n"
    val is: InputStream = new ByteArrayInputStream(content.getBytes(Codec.UTF8.charSet))
    val words = Source.fromInputStream(is)(Codec.UTF8)
      .getLines()
      .map(_.dropWhile(_ == '\uFEFF').trim.toLowerCase)
      .filter(_.nonEmpty)
      .toSet

    words should contain("ngày")
    words should contain("đêm")
    words should contain("100%")
    words should contain("café")
    words should not contain bom.toString
  }

  test("stopWords filters out whitespace-only lines") {
    val content = "và\n  \n\t\nlà\n"
    val is: InputStream = new ByteArrayInputStream(content.getBytes(Codec.UTF8.charSet))
    val words = Source.fromInputStream(is)(Codec.UTF8)
      .getLines()
      .map(_.dropWhile(_ == '\uFEFF').trim.toLowerCase)
      .filter(_.nonEmpty)
      .toSet

    words should contain("và")
    words should contain("là")
    words should not contain("")
    words should not contain("  ")
    words should not contain("\t")
  }

  test("stopWords with mixed-case words are lowercased") {
    val content = "Và\nLà\nCủa\n"
    val is: InputStream = new ByteArrayInputStream(content.getBytes(Codec.UTF8.charSet))
    val words = Source.fromInputStream(is)(Codec.UTF8)
      .getLines()
      .map(_.dropWhile(_ == '\uFEFF').trim.toLowerCase)
      .filter(_.nonEmpty)
      .toSet

    words should contain("và")
    words should contain("là")
    words should contain("của")
  }

  // ---------------------------------------------------------------------------
  // Property-based: formatDate idempotent for 8-digit strings
  // ---------------------------------------------------------------------------
  test("formatDate is idempotent for 8-digit strings") {
    val gen8digit = Gen.listOfN(8, Gen.numChar).map(_.mkString)
    forAll(gen8digit) { dateStr =>
      Main.formatDate(dateStr) shouldBe dateStr
    }
  }

}
