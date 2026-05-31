# Trending Words Extraction Job (Scala)

Extract and aggregate Vietnamese keywords from JSON news articles using Apache Spark. Fast, efficient JVM-native processing with Vietnamese tokenization and stopword filtering.

---

## 1. Business Purpose

Processes news articles from HDFS to extract trending keywords by:

- Reading JSON documents from category folders (Entertainment, Technology, Health)
- Cleaning and tokenizing Vietnamese text
- Removing stopwords and filtering
- Aggregating keyword counts by date, source, and category
- Outputting results to Parquet and CSV

**Output schema:**
| Column | Type | Description |
|--------|------|-------------|
| `ngay` | string | Date (yyyyMMdd) |
| `nguon` | string | News source |
| `chu_de` | string | Category |
| `tu_khoa` | string | Keyword |
| `so_lan_xuat_hien` | long | Occurrence count |

---

## 2. Installation

### Prerequisites

- Java 8+ (tested with Java 25)
- sbt (Scala build tool)

### Install sbt

```bash
# Ubuntu/Debian
curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | sudo gpg --dearmor -o /etc/apt/keyrings/scalasbt.gpg
echo "deb [signed-by=/etc/apt/keyrings/scalasbt.gpg] https://repo.scala-sbt.org/scalasbt/debian all main" | sudo tee /etc/apt/sources.list.d/sbt.list
sudo apt-get update
sudo apt-get install sbt
```

### Set Up Python Virtual Environment

For running Python-based Spark jobs alongside this Scala implementation, set up a virtual environment with PySpark 3.5.0:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install PySpark 3.5.0
pip install pyspark==3.5.0
```

Once activated, you can submit Python Spark jobs using `spark-submit` from within the virtual environment. To deactivate, run:

```bash
deactivate
```

### Clone/Navigate to Project

```bash
cd transform/keywords-scala
```

---

## 3. Test and Build

### Run Tests

```bash
sbt test
```

**Expected output:** 14 tests passed (unit tests only, integration tests skipped)

### Build Fat JAR

```bash
sbt clean assembly
```

**Output:** `target/scala-2.12/trending-words-job-assembly.jar` (5.3 MB)

---

## 4. Run the Job

```bash
spark-submit \
  --class bigdt.transform.keywords.TrendingWordsJob \
  --master spark://localhost:8080 \
  --deploy-mode client \
  --executor-memory 3g \
  --executor-cores 2 \
  target/scala-2.12/trending-words-job-assembly.jar \
  hdfs://localhost:9870/raw_zone \
  hdfs://localhost:9870/work_zone/table_trending_words
```
