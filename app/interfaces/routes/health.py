from fastapi import APIRouter

router = APIRouter(tags=["system"])

@router.get("/health")
def health():
    return {"ok": True, "project": "bs1"}