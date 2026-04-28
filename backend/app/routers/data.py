"""
数据源路由 - API 探测 + 数据库探测/查询
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import os

from app.services.api_probe import probe_api
from app.services.db_connector import list_tables, probe_table, query_sql

router = APIRouter()


# ========== API 数据源探测 ==========

class ProbeRequest(BaseModel):
    url: str
    method: str = "GET"
    headers: Optional[dict] = None


class ProbeResponse(BaseModel):
    status: int
    fields: list = []
    sample: list = []
    structure: str = ""


@router.post("/probe", response_model=ProbeResponse)
async def probe_api_endpoint(request: ProbeRequest):
    """探测 API 结构，返回字段列表和示例数据"""
    result = await probe_api(request.url, request.method, request.headers)
    return ProbeResponse(**result)


# ========== 数据库数据源 ==========

@router.get("/db/tables")
async def db_list_tables():
    """列出示例数据库中所有表"""
    try:
        tables = list_tables()
        from app.services.db_connector import DEFAULT_DB_PATH
        return {"success": True, "tables": tables, "dbPath": os.path.basename(DEFAULT_DB_PATH)}
    except Exception as e:
        return {"success": False, "tables": [], "message": str(e)}


class DbProbeRequest(BaseModel):
    table: str


@router.post("/db/probe")
async def db_probe_endpoint(request: DbProbeRequest):
    """探测数据库表结构 + 样本数据"""
    try:
        result = probe_table(request.table)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "fields": [], "sample": [], "message": str(e)}


class DbQueryRequest(BaseModel):
    sql: str


@router.post("/db/query")
async def db_query_endpoint(request: DbQueryRequest):
    """执行 SQL 查询（只允许 SELECT）"""
    try:
        result = query_sql(request.sql)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "fields": [], "data": [], "rowCount": 0, "message": str(e)}


# ========== 自定义数据库连接 ==========

class CustomDbRequest(BaseModel):
    dbType: str = "sqlite"  # "sqlite" | "mysql"
    dbPath: Optional[str] = None  # SQLite 文件路径
    host: Optional[str] = "localhost"
    port: Optional[int] = 3306
    user: Optional[str] = "root"
    password: Optional[str] = ""
    database: Optional[str] = ""


@router.post("/db/connect")
async def db_connect(request: CustomDbRequest):
    """测试自定义数据库连接并列出表"""
    try:
        kwargs = {"host": request.host, "port": request.port,
                  "user": request.user, "password": request.password,
                  "database": request.database}
        tables = list_tables(db_path=request.dbPath, db_type=request.dbType, **kwargs)
        return {"success": True, "tables": tables, "dbType": request.dbType,
                "dbPath": request.dbPath or request.database}
    except Exception as e:
        return {"success": False, "tables": [], "message": str(e)}


class CustomDbProbeRequest(BaseModel):
    table: str
    dbType: str = "sqlite"
    dbPath: Optional[str] = None
    host: Optional[str] = "localhost"
    port: Optional[int] = 3306
    user: Optional[str] = "root"
    password: Optional[str] = ""
    database: Optional[str] = ""


@router.post("/db/probe-custom")
async def db_probe_custom(request: CustomDbProbeRequest):
    """探测自定义数据库的表结构"""
    try:
        kwargs = {"host": request.host, "port": request.port,
                  "user": request.user, "password": request.password,
                  "database": request.database}
        result = probe_table(request.table, db_path=request.dbPath,
                           db_type=request.dbType, **kwargs)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "fields": [], "sample": [], "message": str(e)}


# ========== AI 字段智能推测 ==========

class FieldInferRequest(BaseModel):
    fields: list  # 字段名列表
    sample: list  # 示例数据（前几行）


@router.post("/infer-fields")
async def infer_fields(request: FieldInferRequest):
    """用 AI 推测字段的业务含义"""
    try:
        from app.services.kimi import chat_completion_json
        prompt = f"""根据以下数据库/API的字段名和示例数据，推测每个字段的业务含义。
只返回JSON对象，格式: {{"字段名": "中文说明", ...}}

字段: {request.fields}
示例数据: {request.sample[:3]}"""

        result = await chat_completion_json([{"role": "user", "content": prompt}])
        return {"success": True, "annotations": result}
    except Exception as e:
        return {"success": False, "annotations": {}, "message": str(e)}

