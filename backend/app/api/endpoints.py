from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import cds as models
from ..core.database import get_db
from pydantic import BaseModel, ConfigDict

router = APIRouter()

# --- SCHEMAS (Pydantic models) ---
class SchoolBase(BaseModel):
    institution_id: str
    name: str
    city_state_zip: Optional[str] = None
    website_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AdmissionData(BaseModel):
    academic_year: str
    total_applicants: Optional[int] = None
    total_admitted: Optional[int] = None
    total_enrolled: Optional[int] = None
    applicants_international: Optional[int] = None
    admitted_international: Optional[int] = None
    enrolled_international: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

class SchoolDetail(SchoolBase):
    admission_data: List[AdmissionData] = []

class SchoolListItem(SchoolBase):
    rank_2025: Optional[int] = None
    rank_type: Optional[str] = None
    total_applicants: Optional[int] = None
    total_admitted: Optional[int] = None
    applicants_international: Optional[int] = None
    admitted_international: Optional[int] = None

# --- ENDPOINTS ---

@router.get("/schools", response_model=List[SchoolListItem])
def get_schools(
    q: Optional[str] = None, 
    letter: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Lấy danh sách trường kèm số liệu tuyển sinh cơ bản."""
    query = db.query(
        models.Institution_Master,
        models.Admission_C
    ).outerjoin(
        models.Admission_C, 
        models.Institution_Master.institution_id == models.Admission_C.institution_id
    )
    
    if q:
        query = query.filter(models.Institution_Master.name.ilike(f"%{q}%"))
    
    if letter:
        query = query.filter(models.Institution_Master.name.ilike(f"{letter}%"))
    
    # Sắp xếp và phân trang
    results = query.order_by(models.Institution_Master.name).offset(skip).limit(limit).all()
    
    schools = []
    for school, admission in results:
        # Pydantic v2 syntax
        item = SchoolListItem.model_validate(school)
        # Thêm rank từ Institution_Master
        item.rank_2025 = school.rank_2025
        item.rank_type = school.rank_type
        if admission:
            item.total_applicants = admission.total_applicants
            item.total_admitted = admission.total_admitted
            item.applicants_international = admission.applicants_international
            item.admitted_international = admission.admitted_international
        schools.append(item)
        
    return schools

@router.get("/schools/{school_id}", response_model=SchoolDetail)
def get_school_detail(school_id: str, db: Session = Depends(get_db)):
    """Lấy chi tiết thông tin một trường và dữ liệu tuyển sinh."""
    school = db.query(models.Institution_Master).filter(models.Institution_Master.institution_id == school_id).first()
    
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    
    # Lấy dữ liệu tuyển sinh liên quan (thủ công hoặc qua relationship)
    admissions = db.query(models.Admission_C).filter(models.Admission_C.institution_id == school_id).all()
    
    # Convert sang schema output
    school_data = SchoolBase.model_validate(school)
    
    result = SchoolDetail(
        **school_data.model_dump(),
        admission_data=[AdmissionData.model_validate(a) for a in admissions]
    )
    return result
