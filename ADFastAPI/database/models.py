from sqlalchemy import Column, Integer, LargeBinary, String
from sqlalchemy.ext.declarative import declarative_base

AD_base = declarative_base()

class AD(AD_base):
    __tablename__ = 'AnimatedDrawings'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    # original_image = Column(LargeBinary, nullable=True)
    # cropped_image = Column(LargeBinary, nullable=True)