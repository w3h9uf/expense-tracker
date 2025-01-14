from fastapi import APIRouter

# 创建 APIRouter 实例
router = APIRouter()

# 示例交易路由
@router.get("/")
def get_transactions():
    return {"message": "Transactions endpoint is working"}
