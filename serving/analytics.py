from pathlib import Path
from collections import Counter
import html
import re
import unicodedata

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import text

from db.database import engine


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


VIETNAMESE_STOPWORDS = {
    "và", "là", "của", "có", "cho", "với", "các", "những", "một", "này",
    "đó", "được", "trong", "khi", "về", "từ", "theo", "sau", "trước",
    "đến", "tại", "trên", "dưới", "vào", "ra", "lại", "đã", "đang", "sẽ",
    "bị", "do", "vì", "nên", "nếu", "thì", "hay", "hoặc", "như", "rằng",
    "để", "cùng", "nhiều", "ít", "hơn", "nhất", "rất", "mới", "cũ",
    "người", "ngày", "năm", "tháng", "giờ", "kỳ", "lần", "việc", "vụ",
    "tin", "bài", "sự", "nói", "biết", "sau khi", "không", "đây", "kia",

    # English/common noise
    "the", "and", "or", "of", "to", "in", "on", "for", "with", "by", "from",
    "is", "are", "was", "were", "be", "as", "at", "this", "that"
}


def _ensure_static_dir():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(value):
    if value is None or pd.isna(value):
        return ""

    value = str(value)
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = unicodedata.normalize("NFC", value)
    value = value.lower()

    return value


def extract_vietnamese_keywords(text):
    text = clean_text(text)

    # Bắt cả chữ tiếng Việt có dấu
    words = re.findall(
        r"[a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯ"
        r"àáâãèéêìíòóôõùúăđĩũơư"
        r"Ạ-ỹ]+",
        text
    )

    keywords = []

    for word in words:
        word = word.strip().lower()

        if len(word) < 2:
            continue

        if word.isdigit():
            continue

        if word in VIETNAMESE_STOPWORDS:
            continue

        keywords.append(word)

    return keywords


# ==========================================
# QUERY LAYER
# ==========================================

def get_articles_by_category():
    query = """
    SELECT
        c.name AS category,
        COUNT(a.id) AS total_articles
    FROM categories c
    LEFT JOIN articles a
        ON a.category_id = c.id
    GROUP BY c.id, c.name
    ORDER BY total_articles DESC
    """

    return pd.read_sql(text(query), engine)


def get_article_texts():
    query = """
    SELECT
        a.title,
        a.description,
        c.name AS category
    FROM articles a
    JOIN categories c
        ON c.id = a.category_id
    WHERE a.is_duplicate = 0 OR a.is_duplicate IS NULL
    """

    return pd.read_sql(text(query), engine)


def get_top_20_keywords():
    df = get_article_texts()

    counter = Counter()

    for _, row in df.iterrows():
        text = f"{row.get('title', '')} {row.get('description', '')}"
        counter.update(extract_vietnamese_keywords(text))

    return pd.DataFrame(
        counter.most_common(20),
        columns=["keyword", "frequency"]
    )


def get_top_10_keywords_by_category():
    df = get_article_texts()

    rows = []

    for category, group in df.groupby("category"):
        counter = Counter()

        for _, row in group.iterrows():
            text = f"{row.get('title', '')} {row.get('description', '')}"
            counter.update(extract_vietnamese_keywords(text))

        for keyword, frequency in counter.most_common(10):
            rows.append({
                "category": category,
                "keyword": keyword,
                "frequency": frequency
            })

    return pd.DataFrame(rows)


# ==========================================
# CHART LAYER
# ==========================================

def plot_pie_chart_by_category():
    df = get_articles_by_category()

    _ensure_static_dir()
    output_path = STATIC_DIR / "pie_chart_category.png"

    plt.figure(figsize=(8, 6))

    if df.empty:
        plt.text(0.5, 0.5, "Không có dữ liệu", ha="center", va="center")
        plt.axis("off")
    else:
        plt.pie(
            df["total_articles"],
            labels=df["category"],
            autopct="%1.1f%%"
        )
        plt.title("Tỷ lệ bài viết theo chủ đề")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return str(output_path)


def plot_top_20_articles():
    """
    Giữ tên hàm cũ để main.py không cần sửa.
    Nhưng nội dung đã đổi thành Top 20 từ khóa.
    """
    df = get_top_20_keywords()

    _ensure_static_dir()
    output_path = STATIC_DIR / "top_20_articles.png"

    plt.figure(figsize=(14, 8))

    if df.empty:
        plt.text(0.5, 0.5, "Không có dữ liệu", ha="center", va="center")
        plt.axis("off")
    else:
        df = df.sort_values("frequency", ascending=True)

        plt.barh(df["keyword"], df["frequency"])
        plt.title("Top 20 từ khóa xuất hiện nhiều nhất")
        plt.xlabel("Số lần xuất hiện")
        plt.ylabel("Từ khóa")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return str(output_path)

def plot_top_10_by_category():
    df = get_top_10_keywords_by_category()

    _ensure_static_dir()
    output_path = STATIC_DIR / "top_10_by_category.png"

    if df.empty:
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "Không có dữ liệu", ha="center", va="center", fontsize=16)
        plt.axis("off")
        plt.savefig(output_path, dpi=180)
        plt.close()
        return str(output_path)

    categories = df["category"].dropna().unique()

    fig, axes = plt.subplots(
        len(categories),
        1,
        figsize=(18, 6 * len(categories))
    )

    if len(categories) == 1:
        axes = [axes]

    for ax, category in zip(axes, categories):
        cat_df = df[df["category"] == category].copy()
        cat_df = cat_df.sort_values("frequency", ascending=True)

        ax.barh(cat_df["keyword"], cat_df["frequency"])
        ax.set_title(f"Top 10 từ khóa - {category}", fontsize=18, pad=14)
        ax.set_xlabel("Số lần xuất hiện", fontsize=13)
        ax.set_ylabel("Từ khóa", fontsize=13)
        ax.tick_params(axis="y", labelsize=13)
        ax.tick_params(axis="x", labelsize=12)

        for i, value in enumerate(cat_df["frequency"]):
            ax.text(value, i, f" {value}", va="center", fontsize=12)

    plt.tight_layout(pad=3)
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    return str(output_path)