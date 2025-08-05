from sqlalchemy import Column, String, Integer,BigInteger, Boolean, Numeric, TIMESTAMP, ForeignKey, DateTime
from sqlalchemy.sql import func
#from sqlalchemy.orm import relationship
#from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from geoalchemy2 import Geometry
from utils.dbcon import Base
#from models.trail_model import TrailModel

class GpxTestModel(Base):
    __tablename__ = 'gpx_test'
    __table_args__ = {'schema': 'user_gpx'}

    id = Column(BigInteger, primary_key=True)
    
    trail_id = Column(String(100), ForeignKey('paths.trails.trail_id', ondelete='CASCADE'))
    
    route = Column(Geometry(geometry_type='LINESTRING', srid=4326))
    location = Column(Geometry(geometry_type='POINTZ', srid=4326), nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # 可選：建立關聯（如果有定義 `TrailModel`）
    #trail = relationship("TrailModel", back_populates="gpx_points", passive_deletes=True)