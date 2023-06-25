from fastapi import APIRouter
from database.models import AD
from database.database import SessionLocal

router = APIRouter(
    prefix="/api/AD",
)

@router.get("/list")
def AD_list():
    db = SessionLocal()
    _AD_list = db.query(AD).all()
    db.close()
    return _AD_list['id']