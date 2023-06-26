from fastapi import APIRouter, Depends
from database.models import AD
from database.database import get_db
from sqlalchemy.orm import Session

from api.make_AD import schema

router = APIRouter(
    prefix="/api/make_AD",
)

@router.get("/list", response_model=list[schema.AD])
def AD_list(db: Session = Depends(get_db)):
    result = db.query(AD).all()
    return result