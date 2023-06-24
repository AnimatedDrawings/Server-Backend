from database.database import Base
from sqlalchemy import Column, Integer, LargeBinary, String

class AD(Base):
    __tablename__ = 'AD'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    # original_image = Column(LargeBinary, nullable=True)
    # cropped_image = Column(LargeBinary, nullable=True)