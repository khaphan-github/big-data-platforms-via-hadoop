#!/bin/bash

# Upload Mock Data to HDFS via Docker
# Uses Docker to execute hdfs commands in the namenode container

set -e

INPUT_DIR="${1:-.}"
NAMENODE_CONTAINER="hadoop-namenode"
HDFS_BASE_PATH="/raw_zone"

echo "=== HDFS Data Uploader ==="
echo "Input directory: $INPUT_DIR"
echo "Target HDFS path: $HDFS_BASE_PATH"
echo ""

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "❌ Error: Input directory not found: $INPUT_DIR"
    exit 1
fi

# Check if docker and namenode container exist
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker not found. Please install Docker."
    exit 1
fi

if ! docker ps | grep -q $NAMENODE_CONTAINER; then
    echo "❌ Error: Namenode container '$NAMENODE_CONTAINER' is not running."
    echo "   Please start the Docker cluster with: docker-compose up -d"
    exit 1
fi

echo "✓ Connected to namenode container: $NAMENODE_CONTAINER"
echo ""

# Create HDFS base directories
echo "Creating HDFS directories..."
docker exec -u hadoop $NAMENODE_CONTAINER hdfs dfs -mkdir -p $HDFS_BASE_PATH/giai_tri 2>/dev/null || true
docker exec -u hadoop $NAMENODE_CONTAINER hdfs dfs -mkdir -p $HDFS_BASE_PATH/cong_nghe 2>/dev/null || true
docker exec -u hadoop $NAMENODE_CONTAINER hdfs dfs -mkdir -p $HDFS_BASE_PATH/suc_khoe 2>/dev/null || true
echo "✓ HDFS directories created"
echo ""

# Upload files for each category
upload_category() {
    local category=$1
    local hdfs_path="$HDFS_BASE_PATH/$category"
    local local_path="$INPUT_DIR/$category"
    
    if [ ! -d "$local_path" ]; then
        echo "[WARN] Skipping $category: directory not found"
        return
    fi
    
    local articles_file="$local_path/articles.json"
    if [ ! -f "$articles_file" ]; then
        echo "[WARN] Skipping $category: articles.json not found"
        return
    fi
    
    echo "Uploading $category articles..."
    
    # Read file and pipe directly to hdfs dfs put
    cat "$articles_file" | docker exec -i $NAMENODE_CONTAINER hdfs dfs -put - "$hdfs_path/articles.json"
    
    echo "  ✓ articles.json uploaded"
    echo ""
}

# Upload all categories
upload_category "giai_tri"
upload_category "cong_nghe"
upload_category "suc_khoe"

# Verify upload
echo "Verifying HDFS contents..."
echo ""
docker exec $NAMENODE_CONTAINER hdfs dfs -ls -R $HDFS_BASE_PATH

echo ""
echo "✅ Upload complete!"
echo ""
echo "Data is now ready for Spark processing."
echo ""
echo "Example: Run Spark job with"
echo "  spark-submit \\"
echo "    --class bigdt.transform.keywords.TrendingWordsJob \\"
echo "    --master local[4] \\"
echo "    target/scala-2.12/trending-words-job-assembly.jar \\"
echo "    hdfs://localhost:9870/raw_zone \\"
echo "    ./output"
