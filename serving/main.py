from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from analytics import plot_pie_chart_by_category, plot_top_10_by_category, plot_top_20_keywords

app = FastAPI(title="Trending Keywords Analytics")
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

@app.get("/api/charts/pie")
async def get_pie_chart():
    """Vẽ biểu đồ tròn"""
    plot_pie_chart_by_category()
    return {"message": "Pie chart created", "url": "/static/pie_chart_category.png"}

@app.get("/api/charts/top20")
async def get_top_20_chart():
    """Vẽ Top 20"""
    plot_top_20_keywords()
    return {"message": "Top 20 chart created", "url": "/static/top_20_keywords.png"}

@app.get("/api/charts/top10")
async def get_top_10_chart():
    """Vẽ Top 10 per chủ đề"""
    plot_top_10_by_category()
    return {"message": "Top 10 by category created", "url": "/static/top_10_by_category.png"}


@app.get("/charts")
async def charts_page():
    """Trang hiển thị biểu đồ."""
    return FileResponse(STATIC_DIR / "charts.html")

# Serve static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)