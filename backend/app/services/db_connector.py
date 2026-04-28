"""
数据库连接器 — SQLite 数据源探测 & 查询

支持:
  - probe: 探测表结构(字段名+类型) + 样本数据
  - query: 执行 SQL 返回结果
  - list_tables: 列出所有表
"""
import sqlite3
import os
from typing import Optional

# 默认示例数据库路径 (backend/sample_data.db)
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "sample_data.db"
)


def _get_conn(db_path: Optional[str] = None, db_type: str = "sqlite", **kwargs):
    """获取数据库连接（SQLite 或 MySQL）"""
    if db_type == "mysql":
        try:
            import pymysql
        except ImportError:
            raise RuntimeError("MySQL 支持需要安装 pymysql: pip install pymysql")
        conn = pymysql.connect(
            host=kwargs.get("host", "localhost"),
            port=int(kwargs.get("port", 3306)),
            user=kwargs.get("user", "root"),
            password=kwargs.get("password", ""),
            database=kwargs.get("database", ""),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        return conn
    else:
        path = db_path or DEFAULT_DB_PATH
        if not os.path.exists(path):
            raise FileNotFoundError(f"数据库文件不存在: {path}")
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn


def list_tables(db_path: Optional[str] = None, db_type: str = "sqlite", **kwargs) -> list:
    """列出数据库中所有表"""
    conn = _get_conn(db_path, db_type, **kwargs)
    try:
        if db_type == "mysql":
            with conn.cursor() as cur:
                cur.execute("SHOW TABLES")
                return [list(row.values())[0] for row in cur.fetchall()]
        else:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            return [row["name"] for row in cur.fetchall()]
    finally:
        conn.close()


def probe_table(table_name: str, db_path: Optional[str] = None, db_type: str = "sqlite", **kwargs) -> dict:
    """探测表结构 + 样本数据"""
    conn = _get_conn(db_path, db_type, **kwargs)
    try:
        if db_type == "mysql":
            with conn.cursor() as cur:
                cur.execute(f"DESCRIBE `{table_name}`")
                cols = cur.fetchall()
                fields = [{"name": c["Field"], "type": c["Type"]} for c in cols]
                cur.execute(f"SELECT COUNT(*) as cnt FROM `{table_name}`")
                row_count = cur.fetchone()["cnt"]
                cur.execute(f"SELECT * FROM `{table_name}` LIMIT 5")
                sample = [dict(row) for row in cur.fetchall()]
        else:
            cur = conn.execute(f"PRAGMA table_info({table_name})")
            columns = cur.fetchall()
            if not columns:
                raise ValueError(f"表 '{table_name}' 不存在")
            fields = [{"name": col["name"], "type": col["type"] or "TEXT"} for col in columns]
            cur = conn.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
            row_count = cur.fetchone()["cnt"]
            cur = conn.execute(f"SELECT * FROM {table_name} LIMIT 5")
            sample = [dict(row) for row in cur.fetchall()]

        return {"table": table_name, "fields": fields, "sample": sample, "rowCount": row_count}
    finally:
        conn.close()


def query_sql(sql: str, db_path: Optional[str] = None, limit: int = 1000) -> dict:
    """
    执行 SQL 查询

    安全限制:
    - 只允许 SELECT 语句
    - 自动加 LIMIT 防止拉全表

    Returns:
        {
            "fields": ["month", "total_revenue"],
            "data": [{"month": "1月", "total_revenue": 12345.6}, ...],
            "rowCount": 12
        }
    """
    # 安全检查：只允许 SELECT
    stripped = sql.strip().upper()
    if not stripped.startswith("SELECT"):
        raise ValueError("仅支持 SELECT 查询语句")

    # 禁止危险关键词
    for keyword in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]:
        if keyword in stripped:
            raise ValueError(f"查询语句中包含不允许的关键词: {keyword}")

    # 自动加 LIMIT（如果用户没加）
    if "LIMIT" not in stripped:
        sql = f"{sql.rstrip().rstrip(';')} LIMIT {limit}"

    conn = _get_conn(db_path)
    try:
        cur = conn.execute(sql)
        rows = cur.fetchall()
        if not rows:
            return {"fields": [], "data": [], "rowCount": 0}

        fields = [desc[0] for desc in cur.description]
        data = [dict(row) for row in rows]

        return {
            "fields": fields,
            "data": data,
            "rowCount": len(data),
        }
    finally:
        conn.close()
