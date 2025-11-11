"""
FastAPI Todo API Router

This module defines the API endpoints and data models for a simple in-memory
todo application built with FastAPI. It supports CRUD operations, filtering,
searching, and basic statistics for todo items.
"""
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from uuid import uuid4
from datetime import datetime

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status


# 定义枚举类型
class TodoPriority(str, Enum):
    """待办事项优先级枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TodoStatus(str, Enum):
    """待办事项状态枚举"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# Pydantic 模型定义
class TodoCreate(BaseModel):
    """创建待办事项的数据模型"""

    title: str = Field(..., min_length=1, max_length=100, description="待办事项标题")
    description: Optional[str] = Field(None, max_length=500, description="详细描述")
    priority: TodoPriority = TodoPriority.MEDIUM
    due_date: Optional[str] = None


class TodoUpdate(BaseModel):
    """更新待办事项的数据模型"""

    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    priority: Optional[TodoPriority] = None
    status: Optional[TodoStatus] = None
    due_date: Optional[str] = None


class TodoResponse(BaseModel):
    """待办事项响应的数据模型"""

    id: str
    title: str
    description: Optional[str]
    priority: TodoPriority
    status: TodoStatus
    due_date: Optional[str]
    created_at: str
    updated_at: str


class SearchResponse(BaseModel):
    """搜索结果的数据模型"""

    results: List[TodoResponse]
    total_found: int
    search_term: str


class StatsResponse(BaseModel):
    """统计信息的响应数据模型"""

    total_todos: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    completion_rate: float
    highest_priority_count: int
    message: Optional[str] = None


# 创建路由器实例
router: APIRouter = APIRouter()

# 模拟数据库 - 内存存储
todos_db: List[Dict[str, Any]] = []


# 工具函数
def generate_id() -> str:
    """生成唯一的UUID字符串"""
    return str(uuid4())


def get_current_timestamp() -> str:
    """获取当前时间戳字符串"""
    return datetime.now().isoformat()


def find_todo_by_id(todo_id: str) -> Optional[Dict[str, Any]]:
    """根据ID查找待办事项"""
    for todo in todos_db:
        if todo["id"] == todo_id:
            return todo
    return None


def ensure_todo_exists(todo_id: str) -> Dict[str, Any]:
    """确保待办事项存在，不存在则抛出404异常"""
    todo = find_todo_by_id(todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID为 {todo_id} 的待办事项未找到",
        )
    return todo


def safe_todo_update(todo: Dict[str, Any], update_data: Dict[str, Any]) -> None:
    """安全地更新待办事项字段（仅更新非None值）"""
    for field, value in update_data.items():
        if value is not None:
            todo[field] = value
    todo["updated_at"] = get_current_timestamp()


def update_todo_fields(todo: Dict[str, Any], update_data: Dict[str, Any]) -> None:
    """更新待办事项字段"""
    safe_todo_update(todo, update_data)


# 初始化示例数据
def initialize_sample_data() -> List[Dict[str, Any]]:
    """初始化一些示例待办事项"""
    sample_todos: List[Dict[str, Any]] = [
        {
            "id": generate_id(),
            "title": "学习FastAPI",
            "description": "完成第三天的学习任务",
            "priority": TodoPriority.HIGH,
            "status": TodoStatus.COMPLETED,
            "due_date": "2024-01-01",
            "created_at": get_current_timestamp(),
            "updated_at": get_current_timestamp(),
        },
        {
            "id": generate_id(),
            "title": "编写Todo API",
            "description": "实现CRUD操作",
            "priority": TodoPriority.MEDIUM,
            "status": TodoStatus.IN_PROGRESS,
            "due_date": "2024-01-02",
            "created_at": get_current_timestamp(),
            "updated_at": get_current_timestamp(),
        },
        {
            "id": generate_id(),
            "title": "学习异步编程",
            "description": "理解async/await语法",
            "priority": TodoPriority.LOW,
            "status": TodoStatus.PENDING,
            "due_date": "2024-01-03",
            "created_at": get_current_timestamp(),
            "updated_at": get_current_timestamp(),
        },
    ]
    return sample_todos


# 初始化数据
todos_db.extend(initialize_sample_data())


# API 路由定义
@router.get("/", response_model=List[TodoResponse], summary="获取所有待办事项")
async def get_all_todos(
    skip: int = 0,
    limit: int = 10,
    status_filter: Optional[TodoStatus] = None,
    priority: Optional[TodoPriority] = None,
) -> List[TodoResponse]:
    """
    获取所有待办事项，支持分页和过滤

    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的最大记录数（用于分页）
    - **status_filter**: 按状态过滤（可选）
    - **priority**: 按优先级过滤（可选）
    """
    filtered_todos = todos_db.copy()

    # 状态过滤
    if status_filter:
        filtered_todos = [todo for todo in filtered_todos if todo["status"] == status_filter]

    # 优先级过滤
    if priority:
        filtered_todos = [
            todo for todo in filtered_todos if todo["priority"] == priority
        ]

    # 分页
    paginated_todos = filtered_todos[skip : skip + limit]

    # 转换为TodoResponse类型
    return [TodoResponse(**todo) for todo in paginated_todos]


@router.get("/{todo_id}", response_model=TodoResponse, summary="根据ID获取待办事项")
async def get_todo_by_id(todo_id: str) -> TodoResponse:
    """
    根据ID获取单个待办事项

    - **todo_id**: 待办事项的唯一标识符
    """
    todo = ensure_todo_exists(todo_id)
    return TodoResponse(**todo)


@router.post(
    "/",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建新待办事项",
)
async def create_todo(todo: TodoCreate) -> TodoResponse:
    """
    创建新的待办事项

    - **title**: 待办事项标题（必需）
    - **description**: 详细描述（可选）
    - **priority**: 优先级（low/medium/high，默认medium）
    - **due_date**: 截止日期（可选）
    """
    new_todo: Dict[str, Any] = {
        "id": generate_id(),
        "title": todo.title,
        "description": todo.description,
        "priority": todo.priority,
        "status": TodoStatus.PENDING,  # 新创建的事项默认为待处理状态
        "due_date": todo.due_date,
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp(),
    }
    todos_db.append(new_todo)
    return TodoResponse(**new_todo)


@router.put("/{todo_id}", response_model=TodoResponse, summary="更新待办事项")
async def update_todo(todo_id: str, todo_update: TodoUpdate) -> TodoResponse:
    """
    更新待办事项的所有字段

    - **todo_id**: 待办事项的唯一标识符
    - 请求体包含要更新的字段
    """
    todo = ensure_todo_exists(todo_id)

    # 将更新数据转换为字典，排除未设置的字段
    update_data = todo_update.model_dump(exclude_unset=True)
    safe_todo_update(todo, update_data)

    return TodoResponse(**todo)


@router.patch("/{todo_id}", response_model=TodoResponse, summary="部分更新待办事项")
async def partial_update_todo(todo_id: str, todo_update: TodoUpdate) -> TodoResponse:
    """
    部分更新待办事项（与PUT不同，PATCH只更新提供的字段）

    - **todo_id**: 待办事项的唯一标识符
    - 请求体包含要更新的字段（可选）
    """
    todo = ensure_todo_exists(todo_id)

    # 将更新数据转换为字典，排除未设置的字段
    update_data = todo_update.model_dump(exclude_unset=True)
    safe_todo_update(todo, update_data)

    return TodoResponse(**todo)


@router.delete("/{todo_id}", summary="删除待办事项")
async def delete_todo(todo_id: str) -> Dict[str, Any]:
    """
    根据ID删除待办事项

    - **todo_id**: 待办事项的唯一标识符
    """
    for index, todo in enumerate(todos_db):
        if todo["id"] == todo_id:
            deleted_todo = todos_db.pop(index)
            return {
                "message": "待办事项删除成功",
                "deleted_todo": deleted_todo,
                "remaining_count": len(todos_db),
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=f"ID为 {todo_id} 的待办事项未找到"
    )


@router.get(
    "/stats/summary", response_model=StatsResponse, summary="获取待办事项统计信息"
)
async def get_todo_stats() -> Dict[str, Union[int, Dict[str, int], float, str]]:
    """
    获取待办事项的统计信息，包括总数、按状态和优先级的分布
    """
    total = len(todos_db)

    if total == 0:
        return {
            "total_todos": 0,
            "by_status": {},
            "by_priority": {},
            "completion_rate": 0,
            "message": "暂无待办事项",
        }

    # 统计状态分布
    by_status: Dict[str, int] = {status.value: 0 for status in TodoStatus}
    by_priority: Dict[str, int] = {priority.value: 0 for priority in TodoPriority}

    for todo in todos_db:
        status_key = str(todo["status"])
        priority_key = str(todo["priority"])
        by_status[status_key] = by_status.get(status_key, 0) + 1
        by_priority[priority_key] = by_priority.get(priority_key, 0) + 1

    completed_count = by_status.get(TodoStatus.COMPLETED.value, 0)
    completion_rate = round(completed_count / total * 100, 2)

    return {
        "total_todos": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "completion_rate": completion_rate,
        "highest_priority_count": by_priority.get(TodoPriority.HIGH.value, 0),
    }


@router.patch("/{todo_id}/complete", summary="标记待办事项为完成")
async def mark_todo_complete(todo_id: str) -> Dict[str, Any]:
    """
    将待办事项标记为完成状态

    - **todo_id**: 待办事项的唯一标识符
    """
    todo = ensure_todo_exists(todo_id)
    safe_todo_update(todo, {"status": TodoStatus.COMPLETED})

    return {"message": f"待办事项 {todo_id} 已标记为完成", "todo": TodoResponse(**todo)}


@router.patch("/{todo_id}/start", summary="开始处理待办事项")
async def start_todo(todo_id: str) -> Dict[str, Any]:
    """
    将待办事项标记为进行中状态

    - **todo_id**: 待办事项的唯一标识符
    """
    todo = ensure_todo_exists(todo_id)
    safe_todo_update(todo, {"status": TodoStatus.IN_PROGRESS})

    return {"message": f"待办事项 {todo_id} 已开始处理", "todo": TodoResponse(**todo)}


@router.get("/search/", response_model=SearchResponse, summary="搜索待办事项")
async def search_todos(q: str, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
    """
    根据关键词搜索待办事项（搜索标题和描述）

    - **q**: 搜索关键词
    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    """
    if not q or len(q.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="搜索关键词不能为空"
        )

    search_term = q.lower().strip()
    results: List[Dict[str, Any]] = []

    for todo in todos_db:
        title_match = search_term in todo["title"].lower()
        # 安全地处理可选描述字段
        description_match = False
        if todo.get("description") is not None:
            description_match = search_term in todo["description"].lower()

        if title_match or description_match:
            results.append(todo)

    paginated_results = results[skip : skip + limit]

    return {
        "results": [TodoResponse(**todo) for todo in paginated_results],
        "total_found": len(results),
        "search_term": search_term,
    }
