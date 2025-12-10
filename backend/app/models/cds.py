from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..core.database import Base

class Institution_Master(Base):
    __tablename__ = "institution_master"

    institution_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    city_state_zip = Column(String(255))
    control = Column(String(50))
    website_url = Column(String(255))
    rank_2025 = Column(Integer)
    rank_type = Column(String(255))
    
    # Quan hệ
    admissions = relationship("Admission_C", back_populates="institution")

class Admission_C(Base):
    __tablename__ = "admission_c"

    institution_id = Column(String(50), ForeignKey("institution_master.institution_id"), primary_key=True)
    academic_year = Column(String(10), primary_key=True)
    
    # Tổng quan
    total_applicants = Column(Integer)
    total_admitted = Column(Integer)
    total_enrolled = Column(Integer)
    acceptance_rate = Column(Float)
    
    # International (Các trường mới thêm)
    applicants_international = Column(Integer)
    admitted_international = Column(Integer)
    enrolled_international = Column(Integer)

    institution = relationship("Institution_Master", back_populates="admissions")


