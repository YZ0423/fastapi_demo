"""
Routers模块

该模块包含FastAPI应用的所有路由处理器。

当前包含:
- todos: Todo事项相关的API端点
"""

from . import todos

# 导出所有路由
__all__ = ["todos"]
