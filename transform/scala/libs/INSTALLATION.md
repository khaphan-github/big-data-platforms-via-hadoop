# vnTokenizer 4.1.1 - Quick Start

Vietnamese word tokenization library. Converts unsegmented Vietnamese text into properly tokenized words.

## Prerequisites

- Java 8+
- Apache Ant 1.10+

```bash
git clone https://github.com/vuthaihoc/vntokenizer4.1.git
# Ubuntu/Debian
sudo apt-get install -y openjdk-11-jdk ant

# macOS
brew install openjdk@11 ant
```

## Build

```bash
ant clean jar
```

Output: `build/jar/vn.hus.nlp.tokenizer-4.1.1.jar` (111 KB)

## Usage

### Command Line

```bash
./vnTokenizer.sh input.txt > output.txt
```

### Java Library

```java
import vn.hus.nlp.tokenizer.Tokenizer;

Tokenizer tokenizer = new Tokenizer();
String result = tokenizer.tokenize("Xin chào thế giới");
```

### Scala/Spark Integration

```bash
cp build/jar/vn.hus.nlp.tokenizer-4.1.1.jar ../../../keywords-scala/libs/
```

Add to `build.sbt`:

```scala
unmanagedJars in Compile += file("libs/vn.hus.nlp.tokenizer-4.1.1.jar")
```

## Troubleshooting

**Missing JAXB (Java 11+):**

```bash
cd lib
wget https://repo1.maven.org/maven2/javax/xml/bind/jaxb-api/2.3.1/jaxb-api-2.3.1.jar
wget https://repo1.maven.org/maven2/com/sun/xml/bind/jaxb-core/2.3.0.1/jaxb-core-2.3.0.1.jar
wget https://repo1.maven.org/maven2/com/sun/xml/bind/jaxb-impl/2.3.1/jaxb-impl-2.3.1.jar
cd ..
ant clean jar
```

**Verify:** `ls -lh build/jar/vn.hus.nlp.tokenizer-4.1.1.jar`
