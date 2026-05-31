#!/bin/bash

# Generate Mock Data for Trending Words Job (Scala)
# Creates sample JSON article files in HDFS-compatible folder structure

set -e

OUTPUT_DIR="${1:-.}/mock_data"
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

# Function to generate JSON article
generate_article() {
    local category=$1
    local category_name=$2
    local title=$3
    local source=$4
    local file_id=$5
    
    local filename="$OUTPUT_DIR/$category/article_${category}_${TODAY}_$file_id.json"
    
    cat > "$filename" << EOF
{
    "id": "${category}_${TODAY}_${file_id}",
    "title": "$title",
    "content": "$title. Đây là bài báo mẫu được tạo tự động cho mục đích kiểm thử phát triển. Chúng tôi cung cấp nội dung chi tiết về chủ đề này trong bài viết đầy đủ và bao quát.",
    "source": "$source",
    "category": "$category_name",
    "publish_date": "$TODAY",
    "url": "https://example.com/$category/article_$file_id",
    "author": "Test Author",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    echo "  ✓ $filename"
}

# Generate Entertainment (Giải Trí) articles
echo "Generating Entertainment articles..."
for ((i=1; i<=NUM_ARTICLES; i++)); do
    title_idx=$((RANDOM % ${#GIAI_TRI_TITLES[@]}))
    source_idx=$((RANDOM % ${#SOURCES_GIAI_TRI[@]}))
    generate_article "giai_tri" "Entertainment" "${GIAI_TRI_TITLES[$title_idx]}" "${SOURCES_GIAI_TRI[$source_idx]}" "$((1000+i))"
done

# Generate Technology (Công Nghệ) articles
echo "Generating Technology articles..."
for ((i=1; i<=NUM_ARTICLES; i++)); do
    title_idx=$((RANDOM % ${#CONG_NGHE_TITLES[@]}))
    source_idx=$((RANDOM % ${#SOURCES_CONG_NGHE[@]}))
    generate_article "cong_nghe" "Technology" "${CONG_NGHE_TITLES[$title_idx]}" "${SOURCES_CONG_NGHE[$source_idx]}" "$((1000+i))"
done

# Generate Health (Sức Khỏe) articles
echo "Generating Health articles..."
for ((i=1; i<=NUM_ARTICLES; i++)); do
    title_idx=$((RANDOM % ${#SUC_KHOE_TITLES[@]}))
    source_idx=$((RANDOM % ${#SOURCES_SUC_KHOE[@]}))
    generate_article "suc_khoe" "Health" "${SUC_KHOE_TITLES[$title_idx]}" "${SOURCES_SUC_KHOE[$source_idx]}" "$((1000+i))"
done

echo ""
echo "✅ Mock data generation complete!"
echo "   Total articles generated: $((NUM_ARTICLES * 3))"
echo "   Output directory: $OUTPUT_DIR"
echo ""
echo "Next step: Upload to HDFS"
echo "   ./script/upload_to_hdfs.sh $OUTPUT_DIR"
