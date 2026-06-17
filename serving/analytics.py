from pathlib import Path

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


def _ensure_static_dir():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# QUERY LAYER
# ==========================================

def get_articles_by_category():
    query = """
    SELECT
        chu_de AS category,
        SUM(so_lan_xuat_hien) AS total_articles
    FROM trending_words
    GROUP BY chu_de
    ORDER BY total_articles DESC
    """

    return pd.read_sql(text(query), engine)


def get_top_20_keywords():
    query = """
    SELECT
        tu_khoa AS keyword,
        SUM(so_lan_xuat_hien) AS frequency
    FROM trending_words
    GROUP BY tu_khoa
    ORDER BY frequency DESC
    LIMIT 20
    """

    return pd.read_sql(text(query), engine)


def get_top_10_keywords_by_category():
    query = """
    SELECT category, keyword, frequency
    FROM (
        SELECT
            chu_de AS category,
            tu_khoa AS keyword,
            SUM(so_lan_xuat_hien) AS frequency,
            ROW_NUMBER() OVER (
                PARTITION BY chu_de
                ORDER BY SUM(so_lan_xuat_hien) DESC
            ) AS keyword_rank
        FROM trending_words
        GROUP BY chu_de, tu_khoa
    ) ranked_keywords
    WHERE keyword_rank <= 10
    ORDER BY category, frequency DESC
    """

    return pd.read_sql(text(query), engine)


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
