package bigdt.transform.keywords

import scala.io.Source
import scala.collection.mutable

/**
 * Vietnamese text tokenization and keyword extraction utilities
 * Note: Currently uses simple whitespace-based tokenization
 * For production use, integrate VnCoreNLP separately or use external tokenization service
 */
object VietnameseTokenizer {
  private val stopwordsCache = mutable.Map[String, Set[String]]()

  /**
   * Load stopwords from classpath resource
   */
  def loadStopwords(): Set[String] = {
    stopwordsCache.getOrElseUpdate("vietnamese", {
      try {
        val resource = getClass.getResourceAsStream("/stopwords_vi.txt")
        if (resource != null) {
          try {
            val source = Source.fromInputStream(resource, "UTF-8")
            val stopwords = source.getLines().map(_.trim).filter(_.nonEmpty).toSet
            source.close()
            stopwords
          } catch {
            case e: Exception =>
              println(s"[WARN] Failed to read stopwords: ${e.getMessage}")
              Set.empty[String]
          }
        } else {
          Set.empty[String]
        }
      } catch {
        case e: Exception =>
          println(s"[WARN] Failed to load stopwords: ${e.getMessage}")
          Set.empty[String]
      }
    })
  }

  /**
   * Tokenize Vietnamese text using simple whitespace splitting
   * For advanced Vietnamese tokenization, use external VnCoreNLP service
   */
  def tokenize(text: String): Array[String] = {
    if (text == null || text.trim.isEmpty) {
      return Array()
    }
    // Simple whitespace-based tokenization
    text.trim.split("\\s+").filter(_.nonEmpty)
  }

  /**
   * Extract keywords from text: tokenize, lowercase, filter stopwords and short words
   */
  def extractKeywords(text: String, minLength: Int = 2): Array[String] = {
    if (text == null || text.trim.isEmpty) {
      return Array()
    }
    
    val stopwords = loadStopwords()
    val tokens = tokenize(text.toLowerCase.trim)
    
    tokens
      .filter(t => t.nonEmpty && t.length >= minLength && !stopwords.contains(t) && !t.startsWith("http"))
      .distinct
  }
}
