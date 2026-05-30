# BigDT Transform Keywords - Trending Words Extraction

Vietnamese NLP-based trending keywords extraction Spark job for analyzing news articles stored in HDFS.

## 📦 Project Structure

```
keywords/
├── pyproject.toml              # Modern Python packaging config
├── setup.py                    # Setup script with wheel support
├── MANIFEST.in                 # Include data files in wheel
│
├── trending_words_job.py       # Main Spark job entry point
├── tokenizer_handler.py        # Vietnamese text processing
├── __init__.py                 # Package initialization
├── stopwords_vi.txt            # Vietnamese stopwords (~300 words)
│
├── e2e/                        # End-to-end test scripts
│   ├── 01_generate_mock_data.sh
│   ├── 02_run_job.sh           # Wheel-based Spark submission
│   ├── 03_cleanup.sh
│   └── run_e2e.sh
│
└── tests/
    └── test_tokenizer_handler.py
```

## 🚀 Quick Start

### Build Wheel & Run

```bash
source .venv/bin/activate
python3 -m build --wheel
bash e2e/02_run_job.sh
```

## 📚 Wheel vs Zip

| Feature      | Wheel            | Zip        |
| ------------ | ---------------- | ---------- |
| Metadata     | ✅ Yes           | ❌ No      |
| Installation | ✅ pip install   | ❌ Manual  |
| Dependencies | ✅ Declared      | ❌ Manual  |
| Standard     | ✅ PyPI standard | ❌ Generic |

## 🔧 Spark Submission

```bash
spark-submit \
  --py-files dist/bigdt_transform_keywords-0.1.0-py3-none-any.whl \
  trending_words_job.py
```

## 🔨 Build Commands

```bash
python3 -m build --wheel              # Build wheel
python3 -m zipfile -l dist/*.whl      # List contents
rm -rf build dist *.egg-info          # Clean build
```

## 📊 Output Schema

| Column           | Type            | Example   |
| ---------------- | --------------- | --------- |
| ngay             | date (yyyyMMdd) | 20260527  |
| nguon            | string          | ThanhNien |
| chu_de           | string          | CongNghe  |
| tu_khoa          | string          | AI        |
| so_lan_xuat_hien | long            | 45        |

**Output Locations:**

- Parquet: `hdfs://namenode:9000/work_zone/table_trending_words/`
- CSV: `hdfs://namenode:9000/work_zone/table_trending_words_csv/`

---

**Version:** 0.1.0 | **Status:** ✅ Production Ready
