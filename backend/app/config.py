"""
配置管理 - 从环境变量或 .env 文件读取
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Settings:
    """应用配置"""
    # Moonshot (Kimi) API
    MOONSHOT_API_KEY: str = os.getenv("MOONSHOT_API_KEY", "")
    MOONSHOT_BASE_URL: str = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
    MOONSHOT_MODEL: str = os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k")

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # 服务端口
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
