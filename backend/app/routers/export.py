"""
导出路由 - 生成可独立部署的 HTML 文件
"""
import json
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class ExportRequest(BaseModel):
    projectName: str = "我的看板"
    widgets: list = []
    theme: Optional[dict] = None
    canvasWidth: int = 1920
    canvasHeight: int = 1080


class ExportResponse(BaseModel):
    html: str
    filename: str


EXPORT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    body {{
      font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
      background: {bg_primary};
      color: {text_primary};
      overflow: hidden;
      width: 100vw;
      height: 100vh;
    }}
    .canvas {{
      position: relative;
      width: {canvas_w}px;
      height: {canvas_h}px;
      margin: 0 auto;
      transform-origin: top center;
    }}
    .widget {{
      position: absolute;
      border-radius: 12px;
      overflow: hidden;
    }}
    /* KPI */
    .kpi-card {{
      background: {bg_card};
      border: 1px solid {border_color};
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      padding: 16px;
    }}
    .kpi-title {{ font-size: 14px; color: {text_secondary}; margin-bottom: 8px; }}
    .kpi-value {{ font-size: 36px; font-weight: 700; color: {accent}; }}
    .kpi-unit {{ font-size: 14px; color: {text_secondary}; margin-left: 4px; }}
    .kpi-trend {{ font-size: 13px; margin-top: 6px; }}
    .kpi-trend.up {{ color: #00e396; }}
    .kpi-trend.down {{ color: #ff4560; }}
    .kpi-trend.flat {{ color: {text_muted}; }}
    /* Text */
    .text-block {{
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
    }}
    .text-block h1 {{
      font-weight: 700;
    }}
    /* Chart */
    .chart-container {{
      background: {bg_card};
      border: 1px solid {border_color};
      border-radius: 12px;
      height: 100%;
      padding: 16px;
    }}
    .chart-title {{
      font-size: 14px;
      color: {text_secondary};
      margin-bottom: 8px;
    }}
    .chart-box {{
      width: 100%;
      height: calc(100% - 30px);
    }}
  </style>
</head>
<body>
  <div class="canvas" id="canvas">
    {widgets_html}
  </div>
  <script>
    // 自适应缩放
    function fitCanvas() {{
      const canvas = document.getElementById('canvas');
      const scaleX = window.innerWidth / {canvas_w};
      const scaleY = window.innerHeight / {canvas_h};
      const scale = Math.min(scaleX, scaleY);
      canvas.style.transform = `scale(${{scale}})`;
    }}
    window.addEventListener('resize', fitCanvas);
    fitCanvas();

    // 初始化图表
    const charts = {charts_json};
    charts.forEach(c => {{
      const el = document.getElementById(c.id);
      if (el) {{
        const chart = echarts.init(el);
        chart.setOption(c.option);
        window.addEventListener('resize', () => chart.resize());
      }}
    }});
  </script>
</body>
</html>"""

# 默认暗色主题变量
DEFAULT_THEME = {
    "bg_primary": "#0a0e27",
    "bg_secondary": "#131837",
    "bg_card": "#161d42",
    "border_color": "#2a3560",
    "accent": "#00d4ff",
    "text_primary": "#e0e6ff",
    "text_secondary": "#8892b0",
    "text_muted": "#4a5578",
}


def generate_kpi_html(widget):
    """生成 KPI 卡片 HTML"""
    p = widget.get("props", {})
    trend_class = p.get("trend", "flat")
    trend_icon = {"up": "↑ 上升", "down": "↓ 下降", "flat": "→ 持平"}.get(trend_class, "")
    color_style = f'color: {p["color"]};' if p.get("color") else ""

    return f"""<div class="kpi-card">
      <div class="kpi-title">{p.get("title", "指标")}</div>
      <div class="kpi-value" style="{color_style}">
        {p.get("value", "0")}<span class="kpi-unit">{p.get("unit", "")}</span>
      </div>
      <div class="kpi-trend {trend_class}">{trend_icon}</div>
    </div>"""


def generate_text_html(widget):
    """生成文本组件 HTML"""
    p = widget.get("props", {})
    font_size = p.get("fontSize", 24)
    align = p.get("align", "center")
    color = p.get("color", "#e0e6ff")
    return f"""<div class="text-block" style="text-align:{align};">
      <h1 style="font-size:{font_size}px; color:{color};">{p.get("content", "标题")}</h1>
    </div>"""


def generate_chart_html(widget, chart_id):
    """生成图表容器 HTML"""
    p = widget.get("props", {})
    return f"""<div class="chart-container">
      <div class="chart-title">{p.get("title", "图表")}</div>
      <div class="chart-box" id="{chart_id}"></div>
    </div>"""


def generate_line_option(widget):
    """生成折线图 ECharts option"""
    p = widget.get("props", {})
    return {
        "tooltip": {"trigger": "axis"},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "category", "data": ["1月", "2月", "3月", "4月", "5月", "6月"],
                  "axisLine": {"lineStyle": {"color": "#4a5578"}}},
        "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "#2a3560"}},
                  "axisLine": {"lineStyle": {"color": "#4a5578"}}},
        "series": [{
            "type": "line",
            "data": [820, 932, 901, 1034, 1290, 1530],
            "smooth": p.get("smooth", True),
            "areaStyle": {"opacity": 0.15} if p.get("area", False) else None,
            "itemStyle": {"color": "#00d4ff"},
            "lineStyle": {"color": "#00d4ff"},
        }],
        "backgroundColor": "transparent",
    }


def generate_bar_option(widget):
    """生成柱状图 ECharts option"""
    p = widget.get("props", {})
    return {
        "tooltip": {"trigger": "axis"},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "category", "data": ["产品A", "产品B", "产品C", "产品D", "产品E"],
                  "axisLine": {"lineStyle": {"color": "#4a5578"}}},
        "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "#2a3560"}},
                  "axisLine": {"lineStyle": {"color": "#4a5578"}}},
        "series": [{
            "type": "bar",
            "data": [120, 200, 150, 80, 170],
            "itemStyle": {"color": "#7b61ff"},
        }],
        "backgroundColor": "transparent",
    }


def generate_pie_option(widget):
    """生成饼图 ECharts option"""
    p = widget.get("props", {})
    radius = ["45%", "70%"] if p.get("donut", True) else [0, "70%"]
    return {
        "tooltip": {"trigger": "item"},
        "legend": {"bottom": "5%", "textStyle": {"color": "#8892b0"}},
        "series": [{
            "type": "pie",
            "radius": radius,
            "center": ["50%", "45%"],
            "data": [
                {"value": 1048, "name": "直接访问"},
                {"value": 735, "name": "邮件营销"},
                {"value": 580, "name": "联盟广告"},
                {"value": 484, "name": "视频广告"},
                {"value": 300, "name": "搜索引擎"},
            ],
            "label": {"show": p.get("showLabel", True), "color": "#8892b0"},
            "emphasis": {"itemStyle": {"shadowBlur": 10}},
        }],
        "backgroundColor": "transparent",
    }


@router.post("/html", response_model=ExportResponse)
async def export_html(request: ExportRequest):
    """导出为单文件 HTML（含 ECharts CDN）"""
    theme = DEFAULT_THEME
    widgets_html_parts = []
    charts_data = []
    chart_counter = 0

    for widget in request.widgets:
        wid = widget.get("id", f"w_{chart_counter}")
        wtype = widget.get("type", "")
        pos = widget.get("position", {"x": 0, "y": 0})
        size = widget.get("size", {"w": 300, "h": 200})

        style = f'left:{pos["x"]}px; top:{pos["y"]}px; width:{size["w"]}px; height:{size["h"]}px;'
        inner_html = ""

        if wtype == "kpi":
            inner_html = generate_kpi_html(widget)
        elif wtype == "text":
            inner_html = generate_text_html(widget)
        elif wtype in ("line", "bar", "pie"):
            chart_id = f"chart_{chart_counter}"
            chart_counter += 1
            inner_html = generate_chart_html(widget, chart_id)

            if wtype == "line":
                option = generate_line_option(widget)
            elif wtype == "bar":
                option = generate_bar_option(widget)
            else:
                option = generate_pie_option(widget)

            charts_data.append({"id": chart_id, "option": option})
        else:
            inner_html = f'<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#4a5578;">🚧 {wtype}</div>'

        widgets_html_parts.append(f'<div class="widget" style="{style}">{inner_html}</div>')

    html = EXPORT_HTML_TEMPLATE.format(
        title=request.projectName,
        canvas_w=request.canvasWidth,
        canvas_h=request.canvasHeight,
        widgets_html="\n    ".join(widgets_html_parts),
        charts_json=json.dumps(charts_data, ensure_ascii=False),
        **theme,
    )

    filename = f"{request.projectName.replace(' ', '_')}.html"
    return ExportResponse(html=html, filename=filename)
