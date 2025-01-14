from fastapi import APIRouter

# 创建 APIRouter 实例
router = APIRouter()

# 示例用户路由
@router.get("/")
def get_users():
    return {"message": "Users endpoint is working"}
