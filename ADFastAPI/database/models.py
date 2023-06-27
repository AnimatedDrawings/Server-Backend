from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

AD_base = declarative_base()

class AD_model(AD_base):
    __tablename__ = 'AnimatedDrawings'

    id = Column(Integer, primary_key=True)
    cropped_image_url = Column(String, nullable=True)