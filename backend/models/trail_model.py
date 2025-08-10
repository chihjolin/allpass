from sqlalchemy import Column, String, Integer,BigInteger, Boolean, Numeric, TIMESTAMP, ForeignKey, DateTime
from sqlalchemy.sql import func
#from sqlalchemy.orm import relationship
#from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from geoalchemy2 import Geometry
from utils.dbcon import Base
#from .user_gpx_model import GpxTestModel

class TrailModel(Base):
    __tablename__ = "trails"
    __table_args__ = {"schema": "paths"}

    trail_id = Column(String(100), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    baiyue_peak_name = Column(String(50))
    location = Column(String(50))
    difficulty = Column(Integer)
    permit_required = Column(Boolean)
    length_km = Column(Numeric(6, 2))
    elevation_gain_m = Column(Integer)
    descent_m = Column(Integer)
    estimated_duration_h = Column(Numeric(5, 2))
    weather_station = Column(String(100))
    route_geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    #建立關聯GpxTestModel
    #gpx_points = relationship(lambda: GpxTestModel, back_populates="trail", cascade="all, delete")


class POIModel(Base):
    __tablename__ = "points_of_interest"
    __table_args__ = {"schema": "paths"}

    id = Column((Integer), primary_key = True)
    trail_id = Column(String(100), ForeignKey("paths.trails.trail_id", ondelete ="CASCADE"))
    name = Column(String(100), nullable = False)
    poi_type = Column(String(50))
    location = Column(Geometry(geometry_type = "POINT", srid = 4326))
    description = Column(String(100))
    created_at = Column(TIMESTAMP(timezone=True), server_default = func.now(), onupdate=func.now())