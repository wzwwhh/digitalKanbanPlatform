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
