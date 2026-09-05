
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/students", tags=["students"])


@router.post("", response_model=schemas.StudentOut)
def create_student(payload: schemas.StudentCreate, db: Session = Depends(get_db)):
    student = models.Student(**payload.model_dump())
    db.add(student)
    db.flush()
    profile = models.LearnerProfile(student_id=student.id)
    db.add(profile)
    db.commit()
    db.refresh(student)
    return student


@router.get("", response_model=list[schemas.StudentOut])
def list_students(db: Session = Depends(get_db)):
    return db.query(models.Student).order_by(models.Student.created_at.desc()).all()


@router.get("/{student_id}", response_model=schemas.StudentOut)
def get_student(student_id: str, db: Session = Depends(get_db)):
    student = db.query(models.Student).get(student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    return student


@router.get("/{student_id}/profile", response_model=schemas.LearnerProfileOut)
def get_profile(student_id: str, db: Session = Depends(get_db)):
    profile = db.query(models.LearnerProfile).filter_by(student_id=student_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    return profile


@router.get("/{student_id}/documents", response_model=list[schemas.DocumentOut])
def list_documents(student_id: str, db: Session = Depends(get_db)):
    return db.query(models.Document).filter_by(student_id=student_id).order_by(
        models.Document.created_at.desc()).all()


@router.get("/{student_id}/lessons", response_model=list[schemas.LessonPlanOut])
def list_lessons(student_id: str, db: Session = Depends(get_db)):
    return db.query(models.LessonPlan).filter_by(student_id=student_id).order_by(
        models.LessonPlan.created_at.desc()).all()


@router.get("/{student_id}/assessments", response_model=list[schemas.AssessmentOut])
def list_assessments(student_id: str, db: Session = Depends(get_db)):
    lessons = db.query(models.LessonPlan.id).filter_by(student_id=student_id).scalar_subquery()
    sessions = db.query(models.TeachingSession.id).filter(
        models.TeachingSession.lesson_id.in_(lessons)).scalar_subquery()
    return db.query(models.Assessment).filter(models.Assessment.session_id.in_(sessions)).order_by(
        models.Assessment.created_at.desc()).all()