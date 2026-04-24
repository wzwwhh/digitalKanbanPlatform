"""
数据源路由 - API 探测、DB 连接、查询
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.api_probe import probe_api

router = APIRouter()


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


class DbConnectRequest(BaseModel):
    dialect: str  # mysql, postgresql, sqlite
    host: str = "localhost"
    port: int = 3306
    user: str = ""
    password: str = ""
    database: str = ""


@router.post("/db/connect")
async def db_connect(request: DbConnectRequest):
    """测试数据库连接，返回表列表"""
    # TODO: 模块 I 实现
    return {"success": False, "message": "数据库连接功能开发中（模块 I）", "tables": []}


@router.post("/db/query")
async def db_query(connection_id: str = "", sql: str = ""):
    """执行 SQL 查询"""
    # TODO: 模块 I 实现
    return {"columns": [], "rows": [], "rowCount": 0}
