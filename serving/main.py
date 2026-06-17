from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from analytics import (
    plot_pie_chart_by_category,
    plot_top_20_articles,
    plot_top_10_by_category
)
app = FastAPI(title="Trending Keywords Analytics")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# =========================
# ROOT FIX (tránh Not Found)
# =========================
@app.get("/")
def root():
    return {"message": "API is running", "docs": "/docs", "charts": "/charts"}


# =========================
# API CHARTS
# =========================
@app.get("/api/charts/pie")
def pie_chart():
    path = plot_pie_chart_by_category()
    return {"message": "Pie chart created", "url": "/static/pie_chart_category.png"}


@app.get("/api/charts/top20")
def top20():
    path = plot_top_20_articles()
    return {"message": "Top 20 chart created", "url": "/static/top_20_articles.png"}


@app.get("/api/charts/top10")
def top10():
    path = plot_top_10_by_category()
    return {"message": "Top 10 chart created", "url": "/static/top_10_by_category.png"}


# =========================
# HTML PAGE
# =========================
@app.get("/charts")
def charts_page():
    file_path = STATIC_DIR / "charts.html"
    return FileResponse(file_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3003)