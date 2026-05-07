from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import sqlite3
import json
from pathlib import Path

router = APIRouter()

# 数据库文件路径
DB_PATH = Path(__file__).parent.parent.parent / "projects.db"

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_db()
    cursor = conn.cursor()

    # 项目表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 看板表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS boards (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # 数据源表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_sources (
            id TEXT PRIMARY KEY,
            board_id TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            config TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

# 启动时初始化数据库
init_db()

# Pydantic 模型
class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Board(BaseModel):
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str

class BoardCreate(BaseModel):
    name: str
    description: Optional[str] = None

class BoardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class DataSource(BaseModel):
    id: str
    board_id: str
    name: str
    type: str
    config: Dict[str, Any]
    created_at: str
    updated_at: str

class DataSourceCreate(BaseModel):
    name: str
    type: str
    config: Dict[str, Any]

class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

# 项目管理接口
@router.get("/", response_model=List[Project])
def list_projects():
    """获取所有项目"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.post("/", response_model=Project)
def create_project(project: ProjectCreate):
    """创建项目"""
    from datetime import datetime
    import uuid

    project_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO projects (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (project_id, project.name, project.description, now, now)
    )
    conn.commit()
    conn.close()

    return {
        "id": project_id,
        "name": project.name,
        "description": project.description,
        "created_at": now,
        "updated_at": now
    }

@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str):
    """获取项目详情"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="项目不存在")

    return dict(row)

@router.put("/{project_id}", response_model=Project)
def update_project(project_id: str, project: ProjectUpdate):
    """更新项目"""
    from datetime import datetime

    conn = get_db()
    cursor = conn.cursor()

    # 检查项目是否存在
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="项目不存在")

    # 更新字段
    updates = []
    params = []
    if project.name is not None:
        updates.append("name = ?")
        params.append(project.name)
    if project.description is not None:
        updates.append("description = ?")
        params.append(project.description)

    if updates:
        now = datetime.now().isoformat()
        updates.append("updated_at = ?")
        params.append(now)
        params.append(project_id)

        cursor.execute(
            f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()

    # 返回更新后的项目
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row)

@router.delete("/{project_id}")
def delete_project(project_id: str):
    """删除项目"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="项目不存在")
    conn.commit()
    conn.close()
    return {"message": "项目已删除"}

# 看板管理接口
@router.get("/{project_id}/boards", response_model=List[Board])
def list_boards(project_id: str):
    """获取项目的所有看板"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM boards WHERE project_id = ? ORDER BY updated_at DESC", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.post("/{project_id}/boards", response_model=Board)
def create_board(project_id: str, board: BoardCreate):
    """创建看板"""
    from datetime import datetime
    import uuid

    board_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    conn = get_db()
    cursor = conn.cursor()

    # 检查项目是否存在
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="项目不存在")

    cursor.execute(
        "INSERT INTO boards (id, project_id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (board_id, project_id, board.name, board.description, now, now)
    )
    conn.commit()
    conn.close()

    return {
        "id": board_id,
        "project_id": project_id,
        "name": board.name,
        "description": board.description,
        "created_at": now,
        "updated_at": now
    }

@router.get("/{project_id}/boards/{board_id}", response_model=Board)
def get_board(project_id: str, board_id: str):
    """获取看板详情"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM boards WHERE id = ? AND project_id = ?", (board_id, project_id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="看板不存在")

    return dict(row)

@router.put("/{project_id}/boards/{board_id}", response_model=Board)
def update_board(project_id: str, board_id: str, board: BoardUpdate):
    """更新看板"""
    from datetime import datetime

    conn = get_db()
    cursor = conn.cursor()

    # 检查看板是否存在
    cursor.execute("SELECT * FROM boards WHERE id = ? AND project_id = ?", (board_id, project_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="看板不存在")

    # 更新字段
    updates = []
    params = []
    if board.name is not None:
        updates.append("name = ?")
        params.append(board.name)
    if board.description is not None:
        updates.append("description = ?")
        params.append(board.description)

    if updates:
        now = datetime.now().isoformat()
        updates.append("updated_at = ?")
        params.append(now)
        params.append(board_id)

        cursor.execute(
            f"UPDATE boards SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()

    # 返回更新后的看板
    cursor.execute("SELECT * FROM boards WHERE id = ?", (board_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row)

@router.delete("/{project_id}/boards/{board_id}")
def delete_board(project_id: str, board_id: str):
    """删除看板"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM boards WHERE id = ? AND project_id = ?", (board_id, project_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="看板不存在")
    conn.commit()
    conn.close()
    return {"message": "看板已删除"}

# 数据源管理接口
@router.get("/{project_id}/boards/{board_id}/data-sources", response_model=List[DataSource])
def list_data_sources(project_id: str, board_id: str):
    """获取看板的所有数据源"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data_sources WHERE board_id = ? ORDER BY updated_at DESC", (board_id,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        data = dict(row)
        data['config'] = json.loads(data['config'])
        result.append(data)

    return result

@router.post("/{project_id}/boards/{board_id}/data-sources", response_model=DataSource)
def create_data_source(project_id: str, board_id: str, data_source: DataSourceCreate):
    """创建数据源"""
    from datetime import datetime
    import uuid

    data_source_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    conn = get_db()
    cursor = conn.cursor()

    # 检查看板是否存在
    cursor.execute("SELECT * FROM boards WHERE id = ? AND project_id = ?", (board_id, project_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="看板不存在")

    cursor.execute(
        "INSERT INTO data_sources (id, board_id, name, type, config, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (data_source_id, board_id, data_source.name, data_source.type, json.dumps(data_source.config), now, now)
    )
    conn.commit()
    conn.close()

    return {
        "id": data_source_id,
        "board_id": board_id,
        "name": data_source.name,
        "type": data_source.type,
        "config": data_source.config,
        "created_at": now,
        "updated_at": now
    }

@router.get("/{project_id}/boards/{board_id}/data-sources/{data_source_id}", response_model=DataSource)
def get_data_source(project_id: str, board_id: str, data_source_id: str):
    """获取数据源详情"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data_sources WHERE id = ? AND board_id = ?", (data_source_id, board_id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="数据源不存在")

    data = dict(row)
    data['config'] = json.loads(data['config'])
    return data

@router.put("/{project_id}/boards/{board_id}/data-sources/{data_source_id}", response_model=DataSource)
def update_data_source(project_id: str, board_id: str, data_source_id: str, data_source: DataSourceUpdate):
    """更新数据源"""
    from datetime import datetime

    conn = get_db()
    cursor = conn.cursor()

    # 检查数据源是否存在
    cursor.execute("SELECT * FROM data_sources WHERE id = ? AND board_id = ?", (data_source_id, board_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="数据源不存在")

    # 更新字段
    updates = []
    params = []
    if data_source.name is not None:
        updates.append("name = ?")
        params.append(data_source.name)
    if data_source.type is not None:
        updates.append("type = ?")
        params.append(data_source.type)
    if data_source.config is not None:
        updates.append("config = ?")
        params.append(json.dumps(data_source.config))

    if updates:
        now = datetime.now().isoformat()
        updates.append("updated_at = ?")
        params.append(now)
        params.append(data_source_id)

        cursor.execute(
            f"UPDATE data_sources SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()

    # 返回更新后的数据源
    cursor.execute("SELECT * FROM data_sources WHERE id = ?", (data_source_id,))
    row = cursor.fetchone()
    conn.close()

    data = dict(row)
    data['config'] = json.loads(data['config'])
    return data

@router.delete("/{project_id}/boards/{board_id}/data-sources/{data_source_id}")
def delete_data_source(project_id: str, board_id: str, data_source_id: str):
    """删除数据源"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM data_sources WHERE id = ? AND board_id = ?", (data_source_id, board_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="数据源不存在")
    conn.commit()
    conn.close()
    return {"message": "数据源已删除"}
