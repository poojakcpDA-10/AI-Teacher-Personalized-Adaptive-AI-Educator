from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.agents import lesson_planner, teaching_agents

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


@router.post("", response_model=schemas.LessonPlanOut)
async def create_lesson(payload: schemas.LessonRequest, db: Session = Depends(get_db)):
    student = db.query(models.Student).get(payload.student_id)
    if not student:
        raise HTTPException(404, "Student not found")

    profile = db.query(models.LearnerProfile).filter_by(student_id=student.id).first()
    weak_concepts = profile.weak_concepts if profile else []

    plan_json = await lesson_planner.build_lesson_plan(
        student_id=payload.student_id, topic=payload.topic, level=payload.level,
        language=payload.language, time_minutes=payload.time_minutes,
        document_id=payload.document_id, instructions=payload.instructions or "",
        weak_concepts=weak_concepts,
    )

    lesson = models.LessonPlan(
        student_id=payload.student_id, document_id=payload.document_id, topic=payload.topic,
        level=payload.level, language=payload.language, time_minutes=payload.time_minutes,
        plan_json=plan_json,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.get("/{lesson_id}", response_model=schemas.LessonPlanOut)
def get_lesson(lesson_id: str, db: Session = Depends(get_db)):
    lesson = db.query(models.LessonPlan).get(lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    return lesson


@router.post("/learning-path", response_model=schemas.LearningPathOut)
async def create_learning_path(payload: schemas.LearningPathRequest, db: Session = Depends(get_db)):
    student = db.query(models.Student).get(payload.student_id)
    if not student:
        raise HTTPException(404, "Student not found")

    result = await teaching_agents.generate_learning_path(payload.topic, student.current_level)
    steps = result.get("steps", [])

    profile = db.query(models.LearnerProfile).filter_by(student_id=student.id).first()
    if not profile:
        profile = models.LearnerProfile(student_id=student.id)
        db.add(profile)
    profile.current_learning_path = {"topic": payload.topic, "steps": steps, "current_step": 0}
    db.commit()

    return {"topic": payload.topic, "steps": steps, "current_step": 0}
