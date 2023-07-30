from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

AD_base = declarative_base()

class AD_model(AD_base):
    __tablename__ = 'AnimatedDrawings'

    id = Column(String, primary_key=True)
    masked_image_url = Column(String, nullable=True)
    annotations_url = Column(String, nullable=True)