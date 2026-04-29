"""
Mock 数据 API - 提供模拟业务数据供看板演示使用
"""
import random
from datetime import datetime, timedelta
from fastapi import APIRouter

router = APIRouter()


def _generate_sales_data():
    """生成模拟销售数据"""
    categories = ["手机", "电脑", "平板", "耳机", "手表"]
    months = []
    now = datetime.now()
    for i in range(6):
        d = now - timedelta(days=30 * (5 - i))
        months.append(d.strftime("%Y-%m"))

    records = []
    for month in months:
        for cat in categories:
            records.append({
                "month": month,
                "category": cat,
                "sales": random.randint(800, 5000),
                "revenue": round(random.uniform(10000, 200000), 2),
                "orders": random.randint(50, 500),
            })
    return records


def _generate_user_stats():
    """生成模拟用户统计数据"""
    channels = ["搜索引擎", "社交媒体", "直接访问", "邮件推广", "广告投放"]
    records = []
    now = datetime.now()
    for i in range(30):
        d = now - timedelta(days=29 - i)
        records.append({
            "date": d.strftime("%Y-%m-%d"),
            "pv": random.randint(5000, 20000),
            "uv": random.randint(1000, 8000),
            "new_users": random.randint(100, 1500),
            "bounce_rate": round(random.uniform(0.2, 0.6), 3),
        })

    channel_data = [{"channel": ch, "users": random.randint(500, 5000)} for ch in channels]
    return {"daily": records, "channels": channel_data}


def _generate_order_list():
    """生成模拟订单列表"""
    statuses = ["已完成", "进行中", "已取消", "待发货"]
    products = ["iPhone 16", "MacBook Pro", "iPad Air", "AirPods Pro", "Apple Watch"]
    records = []
    now = datetime.now()
    for i in range(20):
        records.append({
            "order_id": f"ORD-{10000 + i}",
            "product": random.choice(products),
            "amount": round(random.uniform(99, 15999), 2),
            "status": random.choice(statuses),
            "date": (now - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
            "customer": f"客户{random.randint(1001, 9999)}",
        })
    return records


# === 路由 ===

@router.get("/sales")
async def mock_sales():
    """模拟销售数据 - 月度 x 品类"""
    return {"data": _generate_sales_data(), "total": 30}


@router.get("/users")
async def mock_users():
    """模拟用户统计 - 日PV/UV + 渠道分布"""
    return _generate_user_stats()


@router.get("/orders")
async def mock_orders():
    """模拟订单列表"""
    return {"data": _generate_order_list(), "total": 20}


@router.get("/kpi")
async def mock_kpi():
    """模拟 KPI 汇总"""
    return {
        "today_orders": random.randint(800, 2000),
        "today_revenue": round(random.uniform(50000, 200000), 2),
        "conversion_rate": round(random.uniform(0.02, 0.08), 4),
        "avg_order_value": round(random.uniform(200, 800), 2),
        "active_users": random.randint(3000, 15000),
        "new_users_today": random.randint(100, 800),
    }


@router.get("/catalog")
async def mock_catalog():
    """
    返回所有可用的 Mock 数据源元信息目录。
    前端用此接口渲染"一键添加示例数据源"列表。
    同时也是接口契约文档——后续开发人员按此字段结构写真实接口即可。
    """
    return [
        {
            "name": "销售数据",
            "icon": "📊",
            "description": "月度 × 品类销售统计（含销量、营收、订单数）",
            "url": "/api/mock/sales",
            "method": "GET",
            "dataPath": "data",
            "fields": ["month", "category", "sales", "revenue", "orders"],
            "fieldAnnotations": {
                "month": "月份 (YYYY-MM)",
                "category": "产品品类",
                "sales": "销量（件）",
                "revenue": "营收（元）",
                "orders": "订单数",
            },
            "sample": [
                {"month": "2026-03", "category": "手机", "sales": 2300, "revenue": 138000.50, "orders": 210},
                {"month": "2026-03", "category": "电脑", "sales": 890, "revenue": 267000.00, "orders": 95},
            ],
        },
        {
            "name": "用户统计",
            "icon": "👥",
            "description": "近30天每日 PV/UV + 渠道分布",
            "url": "/api/mock/users",
            "method": "GET",
            "dataPath": "daily",
            "fields": ["date", "pv", "uv", "new_users", "bounce_rate"],
            "fieldAnnotations": {
                "date": "日期 (YYYY-MM-DD)",
                "pv": "页面浏览量",
                "uv": "独立访客数",
                "new_users": "新增用户",
                "bounce_rate": "跳出率 (0~1)",
            },
            "sample": [
                {"date": "2026-04-28", "pv": 12500, "uv": 4200, "new_users": 680, "bounce_rate": 0.35},
                {"date": "2026-04-27", "pv": 11800, "uv": 3900, "new_users": 520, "bounce_rate": 0.38},
            ],
        },
        {
            "name": "订单列表",
            "icon": "📋",
            "description": "最近订单明细（含产品、金额、状态）",
            "url": "/api/mock/orders",
            "method": "GET",
            "dataPath": "data",
            "fields": ["order_id", "product", "amount", "status", "date", "customer"],
            "fieldAnnotations": {
                "order_id": "订单编号",
                "product": "产品名称",
                "amount": "订单金额（元）",
                "status": "状态（已完成/进行中/已取消/待发货）",
                "date": "下单日期",
                "customer": "客户标识",
            },
            "sample": [
                {"order_id": "ORD-10001", "product": "iPhone 16", "amount": 7999.00, "status": "已完成", "date": "2026-04-28", "customer": "客户3521"},
                {"order_id": "ORD-10002", "product": "MacBook Pro", "amount": 14999.00, "status": "待发货", "date": "2026-04-27", "customer": "客户1088"},
            ],
        },
        {
            "name": "KPI 汇总",
            "icon": "📈",
            "description": "今日核心经营指标（适配 KPI 卡片 / 数字翻牌器）",
            "url": "/api/mock/kpi",
            "method": "GET",
            "dataPath": "",
            "fields": ["today_orders", "today_revenue", "conversion_rate", "avg_order_value", "active_users", "new_users_today"],
            "fieldAnnotations": {
                "today_orders": "今日订单数",
                "today_revenue": "今日营收（元）",
                "conversion_rate": "转化率",
                "avg_order_value": "客单价（元）",
                "active_users": "活跃用户数",
                "new_users_today": "今日新增用户",
            },
            "sample": [
                {"today_orders": 1350, "today_revenue": 128500.80, "conversion_rate": 0.045, "avg_order_value": 450.20, "active_users": 8900, "new_users_today": 420},
            ],
        },
    ]
