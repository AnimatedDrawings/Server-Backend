from sqlalchemy import Column, Integer, LargeBinary
from database import Base

class AD(Base):
    __tablename__ = 'question'

    id = Column(Integer, primary_key=True)
    original_image = Column(LargeBinary, nullable=True)
    cropped_image = Column(LargeBinary, nullable=True)

