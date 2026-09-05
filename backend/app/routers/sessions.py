from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.agents import teacher_controller
from app.services import progress_service, llm_service, rag_service

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _get_session(db: Session, session_id: str) -> models.TeachingSession:
    session = db.query(models.TeachingSession).get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session


@router.post("/start")
async def start_session(payload: schemas.SessionStart, db: Session = Depends(get_db)):
    lesson = db.query(models.LessonPlan).get(payload.lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    session = await teacher_controller.create_session(db, lesson)
    return {"session_id": session.id}


@router.post("/{session_id}/next", response_model=schemas.NextStepOut)
async def next_turn(session_id: str, db: Session = Depends(get_db)):
    session = _get_session(db, session_id)
    try:
        turn = await teacher_controller.next_turn(db, session)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if turn is None:
        # Lesson finished -> generate the assessment/learning report
        existing = db.query(models.Assessment).filter_by(session_id=session.id).first()
        if not existing:
            await progress_service.finalize_session(db, session)
        return schemas.NextStepOut(session_id=session_id, finished=True, turn=None,
                                    progress=teacher_controller.progress(session))

    return schemas.NextStepOut(
        session_id=session_id, finished=False,
        turn=schemas.SessionTurnOut.model_validate(turn),
        progress=teacher_controller.progress(session),
    )


@router.post("/answer", response_model=list[schemas.SessionTurnOut])
async def submit_answer(payload: schemas.StudentAnswerIn, db: Session = Depends(get_db)):
    session = _get_session(db, payload.session_id)
    try:
        result = await teacher_controller.submit_answer(db, session, payload.answer_text)
    except ValueError as e:
        raise HTTPException(400, str(e))

    turns = [result["student_turn"], result["eval_turn"]]
    if result["misconception_turn"]:
        turns.append(result["misconception_turn"])
    return [schemas.SessionTurnOut.model_validate(t) for t in turns]


@router.get("/{session_id}/turns", response_model=list[schemas.SessionTurnOut])
def get_turns(session_id: str, db: Session = Depends(get_db)):
    session = _get_session(db, session_id)
    return db.query(models.SessionTurn).filter_by(session_id=session_id).order_by(
        models.SessionTurn.created_at.asc()).all()


@router.get("/{session_id}/assessment", response_model=schemas.AssessmentOut)
def get_assessment(session_id: str, db: Session = Depends(get_db)):
    assessment = db.query(models.Assessment).filter_by(session_id=session_id).first()
    if not assessment:
        raise HTTPException(404, "Assessment not yet available")
    return assessment


@router.post("/chat")

async def chat_followup(
    payload: schemas.ChatIn,
    db: Session = Depends(get_db),
):
    """Grounded follow-up Q&A during/after a lesson ('why does that happen?')."""

    session = _get_session(db, payload.session_id)
    lesson = session.lesson

    context = ""

    if rag_service.has_documents(lesson.student_id):
        hits = rag_service.retrieve_context(
            lesson.student_id,
            payload.message,
            lesson.document_id,
            top_k=4,
        )

        if hits:
            context = "\n---\n".join(
                h["text"][:600] for h in hits
            )

    # Build the source-material instruction separately.
    # This avoids using \n inside an f-string expression.
    if context:
        source_instruction = (
            "Relevant source material:\n"
            + context
        )
    else:
        source_instruction = ""

    prompt = f"""
The student is mid-lesson on "{lesson.topic}"
({lesson.level} level, taught in {lesson.language}).

They asked a follow-up question:
"{payload.message}"

{source_instruction}

Answer clearly and briefly in {lesson.language},
staying consistent with the lesson so far.
"""

    answer = await llm_service.llm_service.generate(prompt)

    turn = models.SessionTurn(
        session_id=session.id,
        turn_type="chat",
        role="student",
        content=payload.message,
    )

    db.add(turn)

    reply_turn = models.SessionTurn(
        session_id=session.id,
        turn_type="chat",
        role="teacher",
        content=answer,
    )

    db.add(reply_turn)

    db.commit()
    db.refresh(reply_turn)

    return schemas.SessionTurnOut.model_validate(reply_turn)

