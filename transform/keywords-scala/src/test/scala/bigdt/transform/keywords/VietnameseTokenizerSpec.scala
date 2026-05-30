package bigdt.transform.keywords

import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers

class VietnameseTokenizerSpec extends AnyFlatSpec with Matchers {

  "VietnameseTokenizer.loadStopwords" should "load Vietnamese stopwords from resource" in {
    val stopwords = VietnameseTokenizer.loadStopwords()
    stopwords should not be empty
    stopwords.size should be > 100
  }

  it should "contain common Vietnamese stopwords" in {
    val stopwords = VietnameseTokenizer.loadStopwords()
    stopwords should contain("là")
    stopwords should contain("và")
    stopwords should contain("của")
  }

  it should "cache stopwords on subsequent calls" in {
    val stopwords1 = VietnameseTokenizer.loadStopwords()
    val stopwords2 = VietnameseTokenizer.loadStopwords()
    stopwords1 should be theSameInstanceAs stopwords2
  }

  "VietnameseTokenizer.tokenize" should "handle null input" in {
    val result = VietnameseTokenizer.tokenize(null)
    result should be(Array())
  }

  it should "handle empty string" in {
    val result = VietnameseTokenizer.tokenize("")
    result should be(Array())
  }

  it should "split text on spaces" in {
    val result = VietnameseTokenizer.tokenize("xin chào thế giới")
    result should contain allOf("xin", "chào", "thế", "giới")
  }

  it should "handle Vietnamese text with diacritics" in {
    val result = VietnameseTokenizer.tokenize("Tôi yêu Việt Nam")
    result should not be empty
    result.head should not be empty
  }

  "VietnameseTokenizer.extractKeywords" should "return empty array for null input" in {
    val result = VietnameseTokenizer.extractKeywords(null)
    result should be(Array())
  }

  it should "return empty array for empty string" in {
    val result = VietnameseTokenizer.extractKeywords("")
    result should be(Array())
  }

  it should "remove stopwords" in {
    val result = VietnameseTokenizer.extractKeywords("là một và tôi")
    // These are all common stopwords, should be filtered out
    result should have length 0
  }

  it should "keep non-stopwords" in {
    val result = VietnameseTokenizer.extractKeywords("máy học công nghệ")
    result.length should be >= 2
    result map (_.toLowerCase) should contain("máy")
    result map (_.toLowerCase) should contain("học")
  }

  it should "filter words shorter than minLength" in {
    val result = VietnameseTokenizer.extractKeywords("a b tình yêu", minLength = 2)
    result should not contain "a"
    result should not contain "b"
  }

  it should "remove URLs" in {
    val result = VietnameseTokenizer.extractKeywords("bài viết tại http://example.com về máy tính")
    result.map(_.toLowerCase) should not contain "http://example.com"
  }

  it should "lowercase all keywords" in {
    val result = VietnameseTokenizer.extractKeywords("MÁYTINH VietNam")
    result.forall(word => word.forall(_.isLower) || word.forall(_.isDigit)) should be(true)
  }
}
