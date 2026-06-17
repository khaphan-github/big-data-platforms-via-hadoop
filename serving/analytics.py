from pathlib import Path
import pandas as pd
from sqlalchemy import text

from db.database import engine

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


def _ensure_static_dir():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)


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


def get_top_20_articles():
    query = """
    SELECT
        title,
        published_date
    FROM articles
    ORDER BY published_date DESC
    LIMIT 20
    """

    return pd.read_sql(text(query), engine)


def get_top_10_by_category():
    query = """
    SELECT
        c.name AS category,
        a.title,
        a.published_date
    FROM articles a
    JOIN categories c
        ON c.id = a.category_id
    ORDER BY c.name, a.published_date DESC
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
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.axis("off")
    else:
        plt.pie(
            df["total_articles"],
            labels=df["category"],
            autopct="%1.1f%%"
        )
        plt.title("Articles by Category")

    plt.savefig(output_path)
    plt.close()

    return str(output_path)


def plot_top_20_articles():
    df = get_top_20_articles()

    _ensure_static_dir()
    output_path = STATIC_DIR / "top_20_articles.png"

    plt.figure(figsize=(14, 8))

    if df.empty:
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.axis("off")
    else:
        df["rank"] = range(len(df), 0, -1)

        plt.barh(
            df["title"].str.slice(0, 50),
            df["rank"]
        )

        plt.title("Top 20 Latest Articles")
        plt.xlabel("Rank")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return str(output_path)


def plot_top_10_by_category():
    df = get_top_10_by_category()

    _ensure_static_dir()
    output_path = STATIC_DIR / "top_10_by_category.png"

    if df.empty:
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.axis("off")
        plt.savefig(output_path)
        plt.close()
        return str(output_path)

    categories = df["category"].unique()

    fig, axes = plt.subplots(
        len(categories),
        1,
        figsize=(12, 5 * len(categories))
    )

    if len(categories) == 1:
        axes = [axes]

    for ax, category in zip(axes, categories):

        cat_df = (
            df[df["category"] == category]
            .head(10)
            .copy()
        )

        ax.barh(
            cat_df["title"].str.slice(0, 40),
            range(len(cat_df))
        )

        ax.set_title(category)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return str(output_path)