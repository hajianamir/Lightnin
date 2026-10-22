from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import datetime

Base = declarative_base()

class ProjectDB(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    lps_class = Column(String, default="I")
    building_length = Column(Float, default=20.0)
    building_width = Column(Float, default=10.0)
    building_height = Column(Float, default=15.0)
    roof_type = Column(String, default="flat")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    nodes = relationship("ConductorNodeDB", back_populates="project", cascade="all, delete-orphan")
    separation_points = relationship("SeparationPointDB", back_populates="project", cascade="all, delete-orphan")

class ConductorNodeDB(Base):
    __tablename__ = "conductor_nodes"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, nullable=False)
    node_type = Column(String, default="air_termination")

    project = relationship("ProjectDB", back_populates="nodes")

class SeparationPointDB(Base):
    __tablename__ = "separation_points"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, nullable=False)
    associated_node_id = Column(String, nullable=False)
    insulation_medium = Column(String, default="air")
    physical_distance_m = Column(Float, nullable=False)

    project = relationship("ProjectDB", back_populates="separation_points")
