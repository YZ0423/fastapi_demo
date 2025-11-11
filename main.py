
"""
FastAPI Todo Application

A simple todo management API built with FastAPI.
Provides endpoints for managing todo items and health checks.
"""
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI
import uvicorn

# 导入路由器
from routers import todos

app: FastAPI = FastAPI(
    title="待办事项管理系统",
    description="一个基于FastAPI的简单待办事项管理API",
    version="1.0.0"
)

# 注册路由
app.include_router(todos.router, prefix="/api/v1", tags=["todos"])


@app.get("/")
async def root() -> Dict[str, Any]:
    """
    根路径端点，返回API欢迎信息

    Returns:
        Dict[str, Any]: 包含欢迎消息和文档链接的字典
    """
    return {
        "message": "欢迎使用Todo API",
        "docs": "请访问 /docs 查看API文档"
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    健康检查端点

    Returns:
        Dict[str, Any]: 包含服务状态和时间戳的字典
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

