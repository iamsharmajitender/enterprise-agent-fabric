from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by compose and load balancers."""
    return {"status": "UP"}
