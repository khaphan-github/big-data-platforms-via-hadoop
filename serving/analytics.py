from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from db.database import get_db_connection


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


def _ensure_static_dir() -> None:
	STATIC_DIR.mkdir(parents=True, exist_ok=True)


def get_keywords_by_category() -> pd.DataFrame:
	"""Lấy số lượng từ khóa theo chủ đề."""
	conn = get_db_connection()
	if conn is None:
		return pd.DataFrame(columns=["chu_de", "so_luong_tu_khoa"])

	query = """
	SELECT chu_de, COUNT(DISTINCT tu_khoa) AS so_luong_tu_khoa
	FROM table_trending_words
	GROUP BY chu_de;
	"""
	df = pd.read_sql(query, conn)
	conn.close()
	return df


def plot_pie_chart_by_category() -> str:
	"""Vẽ biểu đồ tròn số lượng từ khóa theo chủ đề."""
	df = get_keywords_by_category()
	_ensure_static_dir()
	output_path = STATIC_DIR / "pie_chart_category.png"

	if df.empty:
		plt.figure(figsize=(8, 6))
		plt.title("Số lượng từ khóa theo chủ đề")
		plt.text(0.5, 0.5, "Khong co du lieu", ha="center", va="center")
		plt.axis("off")
		plt.savefig(output_path)
		plt.close()
		return str(output_path)

	plt.figure(figsize=(8, 6))
	plt.pie(df["so_luong_tu_khoa"], labels=df["chu_de"], autopct="%1.1f%%")
	plt.title("Số lượng từ khóa theo chủ đề")
	plt.savefig(output_path)
	plt.close()
	return str(output_path)


def get_top_20_keywords() -> pd.DataFrame:
	"""Top 20 từ khóa xuất hiện nhiều nhất."""
	conn = get_db_connection()
	if conn is None:
		return pd.DataFrame(columns=["tu_khoa", "tong_so_lan"])

	query = """
	SELECT tu_khoa, SUM(so_lan_xuat_hien) AS tong_so_lan
	FROM table_trending_words
	GROUP BY tu_khoa
	ORDER BY tong_so_lan DESC
	LIMIT 20;
	"""
	df = pd.read_sql(query, conn)
	conn.close()
	return df


def plot_top_20_keywords() -> str:
	"""Vẽ biểu đồ bar top 20 từ khóa."""
	df = get_top_20_keywords()
	_ensure_static_dir()
	output_path = STATIC_DIR / "top_20_keywords.png"

	plt.figure(figsize=(14, 6))
	if df.empty:
		plt.title("Top 20 từ khóa trending (tất cả chủ đề)")
		plt.text(0.5, 0.5, "Khong co du lieu", ha="center", va="center")
		plt.axis("off")
	else:
		df = df.sort_values("tong_so_lan", ascending=True)
		plt.barh(df["tu_khoa"], df["tong_so_lan"], color="steelblue")
		plt.xlabel("Số lần xuất hiện")
		plt.title("Top 20 từ khóa trending (tất cả chủ đề)")

	plt.tight_layout()
	plt.savefig(output_path)
	plt.close()
	return str(output_path)


def get_top_10_by_category() -> pd.DataFrame:
	"""Top 10 từ khóa theo từng chủ đề."""
	conn = get_db_connection()
	if conn is None:
		return pd.DataFrame(columns=["chu_de", "tu_khoa", "tong_so_lan"])

	query = """
	SELECT chu_de, tu_khoa, SUM(so_lan_xuat_hien) AS tong_so_lan
	FROM table_trending_words
	GROUP BY chu_de, tu_khoa
	ORDER BY chu_de, tong_so_lan DESC;
	"""
	df = pd.read_sql(query, conn)
	conn.close()
	return df


def plot_top_10_by_category() -> str:
	"""Vẽ 3 biểu đồ bar - 1 cho mỗi chủ đề."""
	df = get_top_10_by_category()
	_ensure_static_dir()
	output_path = STATIC_DIR / "top_10_by_category.png"
	categories = ["GiaiTri", "CongNghe", "SucKhoe"]

	fig, axes = plt.subplots(1, 3, figsize=(18, 6))

	for idx, cat in enumerate(categories):
		ax = axes[idx]
		cat_data = df[df["chu_de"] == cat]

		if cat_data.empty:
			ax.set_title(f"Top 10 từ khóa - {cat}")
			ax.text(0.5, 0.5, "Khong co du lieu", ha="center", va="center")
			ax.axis("off")
			continue

		cat_data = cat_data.nlargest(10, "tong_so_lan").sort_values("tong_so_lan", ascending=True)
		ax.barh(cat_data["tu_khoa"], cat_data["tong_so_lan"], color="teal")
		ax.set_title(f"Top 10 từ khóa - {cat}")
		ax.set_xlabel("Số lần xuất hiện")

	plt.tight_layout()
	plt.savefig(output_path)
	plt.close(fig)
	return str(output_path)
