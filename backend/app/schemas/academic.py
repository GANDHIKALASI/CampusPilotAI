"""
Pydantic schemas for BCA Semester V and VI Academic Curriculum Structure.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.document import DocumentItem


class UnitItem(BaseModel):
    """Syllabus unit within a theory subject."""
    id: str
    subject_id: str
    unit_number: int
    title: str
    topics: str
    order_index: int = 0


class PracticalItem(BaseModel):
    """Practical laboratory exercise."""
    id: str
    subject_id: str
    exercise_number: int
    title: str
    description: Optional[str] = None
    order_index: int = 0


class ProjectReportSection(BaseModel):
    """Required section within the Project Work-I report."""
    section_number: int
    title: str
    description: Optional[str] = None
    required: bool = True


class ProjectEvaluationCriteria(BaseModel):
    """Formal evaluation criteria for Project Work-I."""
    criteria_number: Optional[int] = None
    criterion: Optional[str] = None
    title: Optional[str] = None
    weight: Optional[str] = None
    description: Optional[str] = None


class ProjectGuidelinesItem(BaseModel):
    """Project Work-I structure, report sections and evaluation pattern."""
    id: Optional[str] = None
    subject_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    report_sections: List[ProjectReportSection] = []
    evaluation_criteria: List[ProjectEvaluationCriteria] = []


class SubjectItem(BaseModel):
    """Academic subject in BCA curriculum."""
    id: str
    semester_id: str
    code: Optional[str] = None
    name: str
    subject_type: str = "theory"  # 'theory', 'practical', 'project'
    order_index: int = 0
    description: Optional[str] = None
    units: Optional[List[UnitItem]] = None
    practicals: Optional[List[PracticalItem]] = None
    project_guidelines: Optional[ProjectGuidelinesItem] = None
    documents_count: Optional[int] = 0


class SemesterItem(BaseModel):
    """Academic semester containing curriculum subjects."""
    id: str
    code: str
    name: str
    title: Optional[str] = None
    semester_number: Optional[int] = None
    academic_year: Optional[str] = "3rd Year"
    order_index: int = 0
    description: Optional[str] = None
    subjects: List[SubjectItem] = []

    def model_post_init(self, __context: Any) -> None:
        if not self.title:
            self.title = self.name
        if self.semester_number is None:
            self.semester_number = self.order_index


class FullCurriculumResponse(BaseModel):
    """Complete hierarchical academic curriculum tree."""
    program: str = "Bachelor of Computer Applications (BCA)"
    academic_system: str = "Semester"
    semesters: List[SemesterItem]
    status: str = "success"


class SubjectDetailResponse(BaseModel):
    """Detailed view of an individual subject with units, exercises and documents."""
    id: str
    semester_id: str
    code: Optional[str] = None
    name: str
    subject_type: str = "theory"
    order_index: int = 0
    description: Optional[str] = None
    units: List[UnitItem] = []
    practicals: List[PracticalItem] = []
    project_guidelines: Optional[ProjectGuidelinesItem] = None
    documents: List[DocumentItem] = []
    documents_count: int = 0
    status: str = "success"
