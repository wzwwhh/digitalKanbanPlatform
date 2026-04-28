"""
初始化示例 SQLite 数据库
运行: python init_sample_db.py
生成: sample_data.db (与 backend 目录同级)
"""
import sqlite3
import os
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "sample_data.db")


def init():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ========== 表1: 销售数据 ==========
    cur.execute("""
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            sales INTEGER NOT NULL,
            revenue REAL NOT NULL,
            orders INTEGER NOT NULL
        )
    """)

    months = ["1月", "2月", "3月", "4月", "5月", "6月",
              "7月", "8月", "9月", "10月", "11月", "12月"]
    categories = ["电子产品", "服装", "食品", "家居", "运动"]

    for month in months:
        for cat in categories:
            sales = random.randint(100, 2000)
            revenue = round(sales * random.uniform(50, 200), 2)
            orders = random.randint(50, 500)
            cur.execute(
                "INSERT INTO sales (month, category, sales, revenue, orders) VALUES (?, ?, ?, ?, ?)",
                (month, cat, sales, revenue, orders)
            )

    # ========== 表2: 用户统计 ==========
    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            pv INTEGER NOT NULL,
            uv INTEGER NOT NULL,
            channel TEXT NOT NULL
        )
    """)

    channels = ["直接访问", "搜索引擎", "社交媒体", "邮件营销", "广告投放"]
    for day in range(1, 31):
        for ch in channels:
            pv = random.randint(500, 10000)
            uv = random.randint(100, pv)
            cur.execute(
                "INSERT INTO users (date, pv, uv, channel) VALUES (?, ?, ?, ?)",
                (f"2026-04-{day:02d}", pv, uv, ch)
            )

    # ========== 表3: 订单明细 ==========
    cur.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    products = ["iPhone 16", "MacBook Pro", "AirPods", "iPad Air", "Apple Watch",
                "Nike 跑鞋", "Adidas T恤", "Levi's 牛仔裤", "优衣库外套"]
    statuses = ["已完成", "待发货", "已发货", "已取消"]

    for i in range(100):
        cur.execute(
            "INSERT INTO orders (order_no, product, amount, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                f"ORD-2026{i+1:04d}",
                random.choice(products),
                round(random.uniform(99, 12999), 2),
                random.choice(statuses),
                f"2026-04-{random.randint(1,27):02d} {random.randint(8,22):02d}:{random.randint(0,59):02d}"
            )
        )

    conn.commit()
    conn.close()
    print(f"[OK] 示例数据库已创建: {DB_PATH}")
    print(f"   - sales: {len(months) * len(categories)} 条")
    print(f"   - users: {29 * len(channels)} 条")
    print(f"   - orders: 100 条")


if __name__ == "__main__":
    init()
