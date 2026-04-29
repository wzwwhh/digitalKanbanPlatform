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
    dataSources: list = []  # 数据源列表，导出时嵌入 fetch 逻辑
    theme: Optional[str] = None  # 主题名称（如 'dark-tech'）
    canvasWidth: int = 1920
    canvasHeight: int = 1080


class ExportResponse(BaseModel):
    html: str
    filename: str


# 主题调色板（与前端 themes/ 目录同步）
THEME_PALETTES = {
    "dark-tech": {
        "bg_primary": "#0a0e27", "bg_secondary": "#131837", "bg_card": "#161d42",
        "border_color": "#2a3560", "accent": "#00d4ff",
        "text_primary": "#e0e6ff", "text_secondary": "#8892b0", "text_muted": "#4a5578",
    },
    "light-biz": {
        "bg_primary": "#f0f2f5", "bg_secondary": "#ffffff", "bg_card": "#ffffff",
        "border_color": "#e8e8e8", "accent": "#1890ff",
        "text_primary": "#1a1a1a", "text_secondary": "#595959", "text_muted": "#bfbfbf",
    },
    "cyber-neon": {
        "bg_primary": "#0d0221", "bg_secondary": "#1a0a3e", "bg_card": "#1a0a3e",
        "border_color": "#4a1a8a", "accent": "#ff00ff",
        "text_primary": "#ffffff", "text_secondary": "#c0a0e0", "text_muted": "#6a4a8a",
    },
    "minimal-white": {
        "bg_primary": "#ffffff", "bg_secondary": "#f8f9fa", "bg_card": "#ffffff",
        "border_color": "#dee2e6", "accent": "#228be6",
        "text_primary": "#212529", "text_secondary": "#495057", "text_muted": "#adb5bd",
    },
    "forest-green": {
        "bg_primary": "#0b1a0f", "bg_secondary": "#132218", "bg_card": "#162a1c",
        "border_color": "#2d5a3a", "accent": "#34d399",
        "text_primary": "#e0f2e9", "text_secondary": "#8fb3a0", "text_muted": "#4a7560",
    },
}

DEFAULT_THEME = THEME_PALETTES["dark-tech"]


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
    @keyframes marquee {{
      0% {{ transform: translateX(0); }}
      100% {{ transform: translateX(-50%); }}
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
    const chartInstances = {{}};
    charts.forEach(c => {{
      const el = document.getElementById(c.id);
      if (el) {{
        const chart = echarts.init(el);
        chart.setOption(c.option);
        chartInstances[c.id] = chart;
        window.addEventListener('resize', () => chart.resize());
      }}
    }});

    // 数据源动态刷新
    const dataSources = {datasources_json};
    const widgetBindings = {bindings_json};

    async function refreshData() {{
      for (const binding of widgetBindings) {{
        const ds = dataSources.find(d => d.id === binding.sourceId);
        if (!ds || !ds.url) continue;
        try {{
          const resp = await fetch(ds.url);
          if (!resp.ok) continue;
          const raw = await resp.json();
          let data = raw;
          if (ds.dataPath) {{
            for (const p of ds.dataPath.split('.')) {{ data = data?.[p]; }}
          }}
          if (!data) continue;

          // KPI 更新
          if (binding.type === 'kpi' && binding.mapping?.value) {{
            const val = Array.isArray(data) ? data[0]?.[binding.mapping.value] : data[binding.mapping.value];
            const el = document.querySelector(`#${{binding.elId}} .kpi-value`);
            if (el && val !== undefined) el.textContent = typeof val === 'number' && val >= 1000 ? val.toLocaleString() : val;
          }}
          // 图表更新
          if (['line','bar'].includes(binding.type) && binding.chartId && Array.isArray(data)) {{
            const chart = chartInstances[binding.chartId];
            if (chart && binding.mapping?.x && binding.mapping?.y) {{
              chart.setOption({{
                xAxis: {{ data: data.map(r => r[binding.mapping.x]) }},
                series: [{{ data: data.map(r => r[binding.mapping.y]) }}]
              }});
            }}
          }}
        }} catch(e) {{ /* ignore fetch errors */ }}
      }}
    }}

    if (widgetBindings.length > 0) {{
      refreshData();
      setInterval(refreshData, 30000);
    }}

    // 时钟更新
    const clockIds = {clock_ids_json};
    function updateClocks() {{
      const now = new Date();
      const time = now.toLocaleTimeString('zh-CN', {{hour12: false}});
      const date = now.toLocaleDateString('zh-CN', {{year:'numeric', month:'2-digit', day:'2-digit', weekday:'short'}});
      clockIds.forEach(id => {{
        const ce = document.getElementById('clock-' + id);
        const de = document.getElementById('date-' + id);
        if (ce) ce.textContent = time;
        if (de) de.textContent = date;
      }});
    }}
    if (clockIds.length > 0) {{
      updateClocks();
      setInterval(updateClocks, 1000);
    }}
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
    categories = p.get("categories") or ["1月", "2月", "3月", "4月", "5月", "6月"]
    values = p.get("values") or [820, 932, 901, 1034, 1290, 1530]
    return {
        "tooltip": {"trigger": "axis"},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "category", "data": categories,
                  "axisLine": {"lineStyle": {"color": "#4a5578"}}},
        "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "#2a3560"}},
                  "axisLine": {"lineStyle": {"color": "#4a5578"}}},
        "series": [{
            "type": "line",
            "data": values,
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
    categories = p.get("categories") or ["产品A", "产品B", "产品C", "产品D", "产品E"]
    values = p.get("values") or [120, 200, 150, 80, 170]
    return {
        "tooltip": {"trigger": "axis"},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "category", "data": categories,
                  "axisLine": {"lineStyle": {"color": "#4a5578"}}},
        "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "#2a3560"}},
                  "axisLine": {"lineStyle": {"color": "#4a5578"}}},
        "series": [{
            "type": "bar",
            "data": values,
            "itemStyle": {"color": "#7b61ff"},
        }],
        "backgroundColor": "transparent",
    }


def generate_pie_option(widget):
    """生成饼图 ECharts option"""
    p = widget.get("props", {})
    radius = ["45%", "70%"] if p.get("donut", True) else [0, "70%"]
    data = p.get("data") or [
        {"value": 1048, "name": "直接访问"},
        {"value": 735, "name": "邮件营销"},
        {"value": 580, "name": "联盟广告"},
        {"value": 484, "name": "视频广告"},
        {"value": 300, "name": "搜索引擎"},
    ]
    return {
        "tooltip": {"trigger": "item"},
        "legend": {"bottom": "5%", "textStyle": {"color": "#8892b0"}},
        "series": [{
            "type": "pie",
            "radius": radius,
            "center": ["50%", "45%"],
            "data": data,
            "label": {"show": p.get("showLabel", True), "color": "#8892b0"},
            "emphasis": {"itemStyle": {"shadowBlur": 10}},
        }],
        "backgroundColor": "transparent",
    }

def generate_gauge_option(widget):
    p = widget.get("props", {})
    return {
        "series": [{"type": "gauge", "data": [{"value": p.get("value", 50)}],
                     "min": p.get("min", 0), "max": p.get("max", 100),
                     "axisLine": {"lineStyle": {"color": [[0.3, "#ff4560"], [0.7, "#feb019"], [1, "#00e396"]]}},
                     "detail": {"formatter": "{value}", "fontSize": 20, "color": "#e0e6ff"}}],
        "backgroundColor": "transparent",
    }

def generate_radar_option(widget):
    p = widget.get("props", {})
    indicators = p.get("indicators") or [
        {"name": "销售", "max": 100}, {"name": "管理", "max": 100},
        {"name": "技术", "max": 100}, {"name": "客服", "max": 100}, {"name": "研发", "max": 100},
    ]
    values = p.get("values") or [80, 60, 90, 70, 85]
    return {
        "radar": {"indicator": indicators, "axisName": {"color": "#8892b0"}},
        "series": [{"type": "radar", "data": [{"value": values, "areaStyle": {"opacity": 0.2}}]}],
        "backgroundColor": "transparent",
    }

def generate_scatter_option(widget):
    p = widget.get("props", {})
    data = p.get("data") or [[10, 8], [20, 15], [30, 25], [40, 20], [50, 35], [60, 30], [70, 45]]
    return {
        "xAxis": {"axisLine": {"lineStyle": {"color": "#4a5578"}}},
        "yAxis": {"splitLine": {"lineStyle": {"color": "#2a3560"}}, "axisLine": {"lineStyle": {"color": "#4a5578"}}},
        "series": [{"type": "scatter", "data": data, "symbolSize": 10, "itemStyle": {"color": "#00d4ff"}}],
        "backgroundColor": "transparent",
    }

def generate_ranking_html(widget, theme):
    p = widget.get("props", {})
    items = p.get("data") or [("项目A", 95), ("项目B", 82), ("项目C", 70), ("项目D", 60), ("项目E", 45)]
    rows = ""
    for i, item in enumerate(items[:p.get("maxItems", 10)]):
        name = item[0] if isinstance(item, (list, tuple)) else item.get("name", "")
        val = item[1] if isinstance(item, (list, tuple)) else item.get("value", 0)
        pct = min(100, int(val))
        rows += f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;font-size:13px;">'
        rows += f'<span style="width:18px;text-align:center;color:{theme["accent"]};font-weight:700;">{i+1}</span>'
        rows += f'<span style="flex:1;color:{theme["text_primary"]};">{name}</span>'
        rows += f'<div style="width:40%;height:8px;background:{theme["border_color"]};border-radius:4px;overflow:hidden;">'
        rows += f'<div style="width:{pct}%;height:100%;background:{theme["accent"]};border-radius:4px;"></div></div>'
        rows += f'<span style="width:40px;text-align:right;color:{theme["text_secondary"]};">{val}</span></div>'
    return f'<div class="chart-container"><div class="chart-title">{p.get("title","排行榜")}</div>{rows}</div>'

def generate_table_html(widget, theme):
    p = widget.get("props", {})
    sample = widget.get("sample") or [{"col1": "示例1", "col2": "100"}, {"col1": "示例2", "col2": "200"}]
    if not sample:
        return f'<div class="chart-container"><div class="chart-title">{p.get("title","表格")}</div><div style="color:{theme["text_muted"]};text-align:center;padding:20px;">暂无数据</div></div>'
    keys = list(sample[0].keys()) if sample else []
    ths = "".join(f'<th style="padding:6px 10px;border-bottom:1px solid {theme["border_color"]};color:{theme["text_secondary"]};font-size:12px;text-align:left;">{k}</th>' for k in keys)
    trs = ""
    for row in sample[:20]:
        tds = "".join(f'<td style="padding:5px 10px;font-size:12px;color:{theme["text_primary"]};">{row.get(k,"")}</td>' for k in keys)
        trs += f"<tr>{tds}</tr>"
    return f'<div class="chart-container"><div class="chart-title">{p.get("title","表格")}</div><table style="width:100%;border-collapse:collapse;"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>'

def generate_numberflip_html(widget, theme):
    p = widget.get("props", {})
    val = str(p.get("value", 0))
    digits = "".join(f'<span style="display:inline-block;min-width:24px;padding:4px 6px;margin:0 2px;background:{theme["bg_primary"]};border-radius:4px;font-size:32px;font-weight:700;color:{theme["accent"]};text-align:center;">{d}</span>' for d in val)
    return f'<div class="kpi-card"><div class="kpi-title">{p.get("title","数字翻牌")}</div><div style="display:flex;align-items:center;justify-content:center;gap:2px;">{p.get("prefix","")}{digits}{p.get("suffix","")}</div></div>'

def generate_progress_html(widget, theme):
    p = widget.get("props", {})
    pct = p.get("percent", 75)
    color = p.get("color") or theme["accent"]
    r = 45
    circ = 2 * 3.14159 * r
    offset = circ * (1 - pct / 100)
    return f'''<div class="kpi-card">
      <div class="kpi-title">{p.get("title","进度")}</div>
      <svg width="100" height="100" style="margin:8px auto;display:block;">
        <circle cx="50" cy="50" r="{r}" fill="none" stroke="{theme["border_color"]}" stroke-width="8"/>
        <circle cx="50" cy="50" r="{r}" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round"
          stroke-dasharray="{circ}" stroke-dashoffset="{offset}" transform="rotate(-90 50 50)"/>
        <text x="50" y="55" text-anchor="middle" fill="{theme["text_primary"]}" font-size="18" font-weight="700">{pct}%</text>
      </svg></div>'''

def generate_clock_html(widget, theme):
    p = widget.get("props", {})
    wid = widget.get("id", "clock")
    return f'''<div style="display:flex;align-items:center;justify-content:center;height:100%;flex-direction:column;">
      <div id="clock-{wid}" style="font-size:28px;font-weight:700;color:{theme["text_primary"]};font-variant-numeric:tabular-nums;"></div>
      <div id="date-{wid}" style="font-size:12px;color:{theme["text_muted"]};margin-top:4px;"></div>
    </div>'''

def generate_marquee_html(widget, theme):
    p = widget.get("props", {})
    text = p.get("text", "滚动字幕")
    speed = max(5, p.get("speed", 50))
    dur = max(5, 200 // speed)
    return f'''<div style="overflow:hidden;height:100%;display:flex;align-items:center;">
      <div style="white-space:nowrap;animation:marquee {dur}s linear infinite;font-size:14px;color:{theme["accent"]};">
        {text} &nbsp;&nbsp;&nbsp;&nbsp; {text}
      </div></div>'''

def generate_borderbox_html(widget, theme):
    p = widget.get("props", {})
    title = p.get("title", "")
    style = p.get("style", "tech-1")
    glow_color = "#00d4ff" if style == "tech-1" else "#7b61ff" if style == "tech-2" else theme["border_color"]
    border_css = f"border:1px solid {glow_color};"
    if p.get("glowing", True) and style != "simple":
        border_css += f"box-shadow:0 0 12px {glow_color}40, inset 0 0 12px {glow_color}10;"
    title_html = f'<div style="position:absolute;top:-10px;left:16px;padding:0 8px;background:{theme["bg_primary"]};color:{glow_color};font-size:12px;">{title}</div>' if title else ""
    return f'<div style="position:relative;height:100%;border-radius:8px;{border_css}">{title_html}</div>'

def generate_map_html(widget, theme):
    p = widget.get("props", {})
    return f'<div class="chart-container"><div class="chart-title">{p.get("title","全国数据分布")}</div><div style="display:flex;align-items:center;justify-content:center;height:calc(100% - 30px);color:{theme["text_muted"]};">🗺️ 地图组件（需在线环境加载）</div></div>'


@router.post("/html", response_model=ExportResponse)
async def export_html(request: ExportRequest):
    """导出为单文件 HTML（含 ECharts CDN）"""
    theme = DEFAULT_THEME.copy()
    if request.theme and isinstance(request.theme, str):
        theme = THEME_PALETTES.get(request.theme, DEFAULT_THEME).copy()
    widgets_html_parts = []
    charts_data = []
    chart_counter = 0
    clock_ids = []

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
        elif wtype in ("line", "bar", "pie", "gauge", "radar", "scatter"):
            chart_id = f"chart_{chart_counter}"
            chart_counter += 1
            inner_html = generate_chart_html(widget, chart_id)
            option_generators = {
                "line": generate_line_option, "bar": generate_bar_option,
                "pie": generate_pie_option, "gauge": generate_gauge_option,
                "radar": generate_radar_option, "scatter": generate_scatter_option,
            }
            option = option_generators[wtype](widget)
            charts_data.append({"id": chart_id, "option": option})
        elif wtype == "ranking":
            inner_html = generate_ranking_html(widget, theme)
        elif wtype == "table":
            inner_html = generate_table_html(widget, theme)
        elif wtype == "number-flip":
            inner_html = generate_numberflip_html(widget, theme)
        elif wtype == "progress":
            inner_html = generate_progress_html(widget, theme)
        elif wtype == "clock":
            inner_html = generate_clock_html(widget, theme)
            clock_ids.append(wid)
        elif wtype == "marquee":
            inner_html = generate_marquee_html(widget, theme)
        elif wtype == "border-box":
            inner_html = generate_borderbox_html(widget, theme)
        elif wtype == "map":
            inner_html = generate_map_html(widget, theme)
        else:
            inner_html = f'<div style="display:flex;align-items:center;justify-content:center;height:100%;color:{theme["text_muted"]};">{wtype}</div>'

        widgets_html_parts.append(f'<div class="widget" id="{wid}" style="{style}">{inner_html}</div>')

    # 构建数据绑定信息（用于导出 HTML 的动态刷新）
    bindings = []
    chart_idx = 0
    for widget in request.widgets:
        ds = widget.get("dataSource")
        if not ds or not ds.get("sourceId"):
            if widget.get("type") in ("line", "bar", "pie"):
                chart_idx += 1
            continue
        wtype = widget.get("type", "")
        binding = {
            "elId": widget.get("id", ""),
            "type": wtype,
            "sourceId": ds["sourceId"],
            "mapping": ds.get("mapping", {}),
        }
        if wtype in ("line", "bar", "pie", "gauge", "radar", "scatter"):
            binding["chartId"] = f"chart_{chart_idx}"
            chart_idx += 1
        bindings.append(binding)

    # 精简数据源信息（只传 id/url/dataPath）
    # 关键：数据库类型数据源没有 url，需映射到 server.py 的路由路径
    ds_export = []
    for ds in (request.dataSources or []):
        ds_id = ds.get("id", "unknown")
        safe_name = ds_id.replace("-", "_").replace(" ", "_")
        if ds.get("type") == "database":
            # 数据库类型 → 指向 server.py 自动生成的查询路由
            ds_export.append({
                "id": ds_id,
                "url": f"/api/data/{safe_name}",
                "dataPath": "data",  # server.py 返回 {"data": [...]}
            })
        else:
            ds_export.append({
                "id": ds_id,
                "url": ds.get("url", ""),
                "dataPath": ds.get("dataPath", ""),
            })

    html = EXPORT_HTML_TEMPLATE.format(
        title=request.projectName,
        canvas_w=request.canvasWidth,
        canvas_h=request.canvasHeight,
        widgets_html="\n    ".join(widgets_html_parts),
        charts_json=json.dumps(charts_data, ensure_ascii=False),
        datasources_json=json.dumps(ds_export, ensure_ascii=False),
        bindings_json=json.dumps(bindings, ensure_ascii=False),
        clock_ids_json=json.dumps(clock_ids, ensure_ascii=False),
        **theme,
    )

    filename = f"{request.projectName.replace(' ', '_')}.html"
    return ExportResponse(html=html, filename=filename)


# ========== ZIP 部署包导出 ==========

import zipfile
import io
import base64

class ZipExportResponse(BaseModel):
    zipBase64: str
    filename: str


def generate_readme(request):
    """自动生成 README.md（含完整的连接信息和调用代码示例）"""
    lines = [f"# {request.projectName}", "",
             "> 本部署包由 AI 看板平台自动导出", "",
             "## 快速启动", "```bash",
             "pip install -r requirements.txt",
             "python server.py",
             "# 打开浏览器访问 http://localhost:8080", "```", "",
             "## 数据源配置", "",
             "以下是本看板使用的所有数据源。后续开发人员只需保持相同的字段名和返回格式，即可将 Mock/示例数据替换为真实数据。", ""]

    for ds in request.dataSources or []:
        dtype = ds.get("type", "api")
        ds_name = ds.get("name", "未命名")
        lines.append(f"### {ds_name} ({dtype.upper()})")

        if dtype == "api":
            url = ds.get("url", "")
            method = ds.get("method", "GET")
            lines.append(f"- **URL**: `{url}`")
            lines.append(f"- **方法**: {method}")
            if ds.get("dataPath"):
                lines.append(f"- **数据路径**: `{ds['dataPath']}`")

            # 字段说明表格
            fields = ds.get("fields", [])
            annotations = ds.get("fieldAnnotations", {})
            if fields:
                lines.append("")
                lines.append("| 字段名 | 说明 |")
                lines.append("|--------|------|")
                for f in fields:
                    ann = annotations.get(f, "")
                    lines.append(f"| `{f}` | {ann} |")

            # 调用代码示例
            lines.append("")
            lines.append("#### 调用示例 (JavaScript)")
            lines.append("```javascript")
            lines.append(f"const resp = await fetch('{url}')")
            lines.append("const data = await resp.json()")
            dp = ds.get("dataPath")
            if dp:
                lines.append(f"const rows = data.{dp}  // Array<{{ {', '.join(fields[:4])} }}> ")
            else:
                lines.append(f"// data → {{ {', '.join(fields[:4])} }}")
            lines.append("```")

            lines.append("")
            lines.append("#### 调用示例 (Python)")
            lines.append("```python")
            lines.append("import requests")
            lines.append(f'resp = requests.{method.lower()}("{url}")')
            lines.append("data = resp.json()")
            if dp:
                lines.append(f'rows = data["{dp}"]')
            lines.append("```")

        else:
            # 数据库类型
            db_type = ds.get("dbType", "sqlite")
            lines.append(f"- **数据库类型**: {db_type.upper()}")
            if db_type == "mysql":
                lines.append(f"- **主机**: `{ds.get('host', 'localhost')}:{ds.get('port', 3306)}`")
                lines.append(f"- **数据库**: `{ds.get('database', '')}`")
                lines.append(f"- **用户**: `{ds.get('user', 'root')}`")
            else:
                lines.append(f"- **数据库文件**: `{ds.get('dbPath', 'sample_data.db')}`")
            lines.append(f"- **表**: `{ds.get('table', '')}`")
            if ds.get("sql"):
                lines.append(f"- **查询SQL**: `{ds.get('sql')}`")

            fields = ds.get("fields", [])
            annotations = ds.get("fieldAnnotations", {})
            if fields:
                lines.append("")
                lines.append("| 字段名 | 说明 |")
                lines.append("|--------|------|")
                for f in fields:
                    ann = annotations.get(f, "")
                    lines.append(f"| `{f}` | {ann} |")

            # 连接代码示例
            lines.append("")
            if db_type == "mysql":
                lines.append("#### 连接示例 (Python)")
                lines.append("```python")
                lines.append("import pymysql")
                lines.append(f"conn = pymysql.connect(")
                lines.append(f"    host='{ds.get('host', 'localhost')}',")
                lines.append(f"    port={ds.get('port', 3306)},")
                lines.append(f"    user='{ds.get('user', 'root')}',")
                lines.append(f"    password='YOUR_PASSWORD',  # TODO: 填入真实密码")
                lines.append(f"    database='{ds.get('database', '')}',")
                lines.append(f"    charset='utf8mb4',")
                lines.append(f"    cursorclass=pymysql.cursors.DictCursor")
                lines.append(f")")
                lines.append(f'cursor = conn.cursor()')
                sql = ds.get("sql", f"SELECT * FROM {ds.get('table', '?')} LIMIT 10")
                lines.append(f'cursor.execute("{sql}")')
                lines.append(f'rows = cursor.fetchall()')
                lines.append("```")
            else:
                lines.append("#### 连接示例 (Python)")
                lines.append("```python")
                lines.append("import sqlite3")
                lines.append(f"conn = sqlite3.connect('{ds.get('dbPath', 'sample_data.db')}')")
                lines.append("conn.row_factory = sqlite3.Row")
                sql = ds.get("sql", f"SELECT * FROM {ds.get('table', '?')} LIMIT 10")
                lines.append(f'rows = [dict(r) for r in conn.execute("{sql}").fetchall()]')
                lines.append("```")

        # 样本数据
        sample = ds.get("sample", [])
        if sample:
            lines.append("")
            lines.append("#### 样本数据")
            lines.append("```json")
            lines.append(json.dumps(sample[:2], ensure_ascii=False, indent=2))
            lines.append("```")

        lines.append("")

    lines += ["## 组件列表", ""]
    for w in request.widgets:
        p = w.get("props", {})
        title = p.get("title") or p.get("content") or w.get("type", "")
        ds_info = ""
        if w.get("dataSource", {}).get("sourceId"):
            ds_info = f" → 数据源 `{w['dataSource']['sourceId']}`"
        lines.append(f"- **{title}** ({w.get('type', '?')}){ds_info}")
    return "\n".join(lines)


def generate_server_py(request):
    """
    生成完整可运行的 FastAPI 部署服务端。
    
    - 为 API 类型数据源生成代理路由（解决跨域）
    - 为数据库类型数据源生成查询路由
    - 静态文件托管（index.html）
    """
    api_sources = []
    db_sources = []
    for ds in request.dataSources or []:
        if ds.get("type") == "database":
            db_sources.append(ds)
        else:
            api_sources.append(ds)

    # 构建路由代码
    route_blocks = []
    
    for ds in api_sources:
        url = ds.get("url", "")
        ds_id = ds.get("id", "unknown")
        safe_name = ds_id.replace("-", "_").replace(" ", "_")
        method = ds.get("method", "GET").lower()
        route_blocks.append(f'''
@app.get("/api/data/{safe_name}")
async def data_{safe_name}():
    """数据代理: {ds.get('name', '')} → {url}"""
    try:
        resp = httpx.{method}("{url}", timeout=15)
        return resp.json()
    except Exception as e:
        return {{"error": str(e)}}
''')
    
    for ds in db_sources:
        ds_id = ds.get("id", "unknown")
        safe_name = ds_id.replace("-", "_").replace(" ", "_")
        db_type = ds.get("dbType", "sqlite")
        table = ds.get("table", "")
        sql = ds.get("sql", f"SELECT * FROM {table}")
        
        if db_type == "mysql":
            route_blocks.append(f'''
@app.get("/api/data/{safe_name}")
async def data_{safe_name}():
    """数据库查询: {ds.get('name', '')} → {table}"""
    import pymysql
    try:
        conn = pymysql.connect(
            host="{ds.get('host', 'localhost')}",
            port={ds.get('port', 3306)},
            user="{ds.get('user', 'root')}",
            password=DB_PASSWORDS.get("{ds_id}", "YOUR_PASSWORD"),
            database="{ds.get('database', '')}",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        with conn.cursor() as cur:
            cur.execute("""{sql}""")
            rows = cur.fetchall()
        conn.close()
        return {{"data": rows, "total": len(rows)}}
    except Exception as e:
        return {{"error": str(e)}}
''')
        else:
            route_blocks.append(f'''
@app.get("/api/data/{safe_name}")
async def data_{safe_name}():
    """数据库查询: {ds.get('name', '')} → {table}"""
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(__file__), "{ds.get('dbPath', 'sample_data.db')}")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute("""{sql}""").fetchall()]
        conn.close()
        return {{"data": rows, "total": len(rows)}}
    except Exception as e:
        return {{"error": str(e)}}
''')

    routes_code = "\n".join(route_blocks)
    
    # 密码占位
    db_passwords = {}
    for ds in db_sources:
        if ds.get("dbType") == "mysql":
            db_passwords[ds.get("id", "")] = "YOUR_PASSWORD"
    passwords_code = json.dumps(db_passwords, ensure_ascii=False, indent=4)

    return f'''"""
{request.projectName} — 部署服务器
由 AI 看板平台自动生成

启动方式:
  pip install -r requirements.txt
  python server.py
  浏览器访问 http://localhost:8080
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx
import os

app = FastAPI(title="{request.projectName}")

# ===== 数据库密码配置（TODO: 填入真实密码）=====
DB_PASSWORDS = {passwords_code}

# ===== 数据路由（自动生成）=====
{routes_code}

# ===== 静态文件托管 =====
@app.get("/")
async def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("  {request.projectName}")
    print("  看板地址: http://localhost:8080")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8080)
'''


def generate_datasource_spec(request):
    """生成机器可读的数据源规格说明文件"""
    spec = {
        "projectName": request.projectName,
        "generatedAt": __import__("datetime").datetime.now().isoformat(),
        "dataSources": [],
    }
    for ds in request.dataSources or []:
        ds_spec = {
            "id": ds.get("id"),
            "name": ds.get("name"),
            "type": ds.get("type", "api"),
            "fields": ds.get("fields", []),
            "fieldAnnotations": ds.get("fieldAnnotations", {}),
            "sample": ds.get("sample", [])[:3],
        }
        if ds.get("type") == "api":
            ds_spec["connection"] = {
                "url": ds.get("url", ""),
                "method": ds.get("method", "GET"),
                "dataPath": ds.get("dataPath", ""),
            }
        else:
            ds_spec["connection"] = {
                "dbType": ds.get("dbType", "sqlite"),
                "host": ds.get("host", ""),
                "port": ds.get("port", ""),
                "database": ds.get("database", ""),
                "table": ds.get("table", ""),
                "sql": ds.get("sql", ""),
            }
        spec["dataSources"].append(ds_spec)
    return json.dumps(spec, ensure_ascii=False, indent=2)


@router.post("/zip")
async def export_zip(request: ExportRequest):
    """导出为 ZIP 部署包（含完整可运行服务端）"""
    html_resp = await export_html(request)

    readme = generate_readme(request)
    server_py = generate_server_py(request)
    ds_spec = generate_datasource_spec(request)
    
    # requirements.txt
    has_mysql = any(d.get("dbType") == "mysql" for d in (request.dataSources or []) if d.get("type") == "database")
    has_api_proxy = any(d.get("type") != "database" for d in (request.dataSources or []))
    
    deps = ["fastapi>=0.100.0", "uvicorn>=0.20.0"]
    if has_api_proxy:
        deps.append("httpx>=0.24.0")
    if has_mysql:
        deps.append("pymysql>=1.1.0")
    requirements = "\n".join(deps) + "\n"

    buf = io.BytesIO()
    proj = request.projectName.replace(" ", "_")
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{proj}/index.html", html_resp.html)
        zf.writestr(f"{proj}/server.py", server_py)
        zf.writestr(f"{proj}/requirements.txt", requirements)
        zf.writestr(f"{proj}/README.md", readme)
        zf.writestr(f"{proj}/data_source_spec.json", ds_spec)

    buf.seek(0)
    return ZipExportResponse(zipBase64=base64.b64encode(buf.read()).decode(), filename=f"{proj}.zip")


