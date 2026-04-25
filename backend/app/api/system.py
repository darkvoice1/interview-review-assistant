from fastapi import APIRouter

# 系统级路由，主要用于健康检查。
router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    # 提供最基础的存活探针。
    return {"status": "healthy"}
