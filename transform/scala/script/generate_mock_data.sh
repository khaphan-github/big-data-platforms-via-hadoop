#!/bin/bash

# Generate Mock Data for Trending Words Job (Scala)
# Creates one articles.json file in each category folder

set -e

OUTPUT_DIR="${1:-./mock_data}"
NUM_ARTICLES="${2:-10}"
TODAY=$(date +%Y%m%d)

echo "=== Mock Data Generator for Trending Words Job ==="
echo "Output directory: $OUTPUT_DIR"
echo "Articles per category: $NUM_ARTICLES"
echo "Date: $TODAY"
echo ""

# Create category directories
mkdir -p "$OUTPUT_DIR/giai_tri"
mkdir -p "$OUTPUT_DIR/cong_nghe"
mkdir -p "$OUTPUT_DIR/suc_khoe"

# Vietnamese article samples
declare -a GIAI_TRI_TITLES=(
    "Phim Avatar 3 đạt doanh thu kỷ lục toàn cầu"
    "Sao nhạc pop Việt công bố album mới đầy bất ngờ"
    "Sự kiện giải thưởng điện ảnh diễn ra hoành tráng"
    "Ca sĩ nổi tiếng hé lộ dự án nhạc phim mới"
    "Phim hành động Việt Nam gây sốt tại các rạp chiếu"
)

declare -a CONG_NGHE_TITLES=(
    "Công ty công nghệ công bố chip AI mới tạo bước ngoặt"
    "Ứng dụng di động vượt một tỷ lượt tải toàn thế giới"
    "Xu hướng phát triển phần mềm năm 2026 được dự đoán"
    "Công nghệ blockchain cách mạng hóa ngành tài chính"
    "Trí tuệ nhân tạo thay đổi cách chúng ta làm việc"
)

declare -a SUC_KHOE_TITLES=(
    "Vaccine mới cải thiện miễn dịch con người hiệu quả"
    "Nghiên cứu y tế khám phá điều trị bệnh mới đột phá"
    "Chế độ ăn uống lành mạnh được khuyến nghị chuyên gia"
    "Bài tập thể dục hàng ngày cải thiện sức khỏe tinh thần"
    "Ngủ đủ giấc giúp tăng cường hệ miễn dịch cơ thể"
)

declare -a SOURCES_GIAI_TRI=("VnExpress" "Thanhnien" "Zing" "Kenh14" "Vietnamnet")
declare -a SOURCES_CONG_NGHE=("Thoidai" "Genk" "Tinhte" "Ictnews" "Thegioidoco")
declare -a SOURCES_SUC_KHOE=("Baokhoehocdoanh" "Doisong" "Suckhoedoisong" "Thoitiet" "Suckhoecommunity")

# Function to generate JSON file for a category
generate_category_json() {
    local category=$1
    local category_display=$2
    local num=$3
    
    local json_file="$OUTPUT_DIR/$category/articles.json"
    local temp_json=$(mktemp)
    
    # Get arrays based on category
    local titles sources
    case "$category" in
        giai_tri)
            titles=("${GIAI_TRI_TITLES[@]}")
            sources=("${SOURCES_GIAI_TRI[@]}")
            ;;
        cong_nghe)
            titles=("${CONG_NGHE_TITLES[@]}")
            sources=("${SOURCES_CONG_NGHE[@]}")
            ;;
        suc_khoe)
            titles=("${SUC_KHOE_TITLES[@]}")
            sources=("${SOURCES_SUC_KHOE[@]}")
            ;;
    esac
    
    echo "[" > "$temp_json"
    
    for ((i=1; i<=num; i++)); do
        # Add comma if not first article
        if [ $i -gt 1 ]; then
            echo "," >> "$temp_json"
        fi
        
        title_idx=$((RANDOM % ${#titles[@]}))
        source_idx=$((RANDOM % ${#sources[@]}))
        
        cat >> "$temp_json" << EOF
  {
    "id": "${category}_${TODAY}_$((1000+i))",
    "title": "${titles[$title_idx]}",
    "content": "${titles[$title_idx]}. Đây là bài báo mẫu được tạo tự động cho mục đích kiểm thử phát triển. Chúng tôi cung cấp nội dung chi tiết về chủ đề này trong bài viết đầy đủ và bao quát.",
    "source": "${sources[$source_idx]}",
    "category": "$category_display",
    "publish_date": "$TODAY",
    "url": "https://example.com/$category/article_$((1000+i))",
    "author": "Test Author",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  }
EOF
    done
    
    echo "" >> "$temp_json"
    echo "]" >> "$temp_json"
    
    mv "$temp_json" "$json_file"
    echo "✓ Created $json_file with $num articles"
}

# Generate articles for each category
echo "Generating Entertainment category..."
generate_category_json "giai_tri" "Entertainment" $NUM_ARTICLES

echo "Generating Technology category..."
generate_category_json "cong_nghe" "Technology" $NUM_ARTICLES

echo "Generating Health category..."
generate_category_json "suc_khoe" "Health" $NUM_ARTICLES

echo ""
echo "✅ Mock data generation complete!"
echo "   Total categories: 3"
echo "   Articles per category: $NUM_ARTICLES"
echo "   Output directory: $OUTPUT_DIR"
echo ""
echo "Structure:"
echo "  $OUTPUT_DIR/giai_tri/articles.json"
echo "  $OUTPUT_DIR/cong_nghe/articles.json"
echo "  $OUTPUT_DIR/suc_khoe/articles.json"
echo ""
echo "Next step: Upload to HDFS"
echo "   ./script/upload_to_hdfs.sh $OUTPUT_DIR"
