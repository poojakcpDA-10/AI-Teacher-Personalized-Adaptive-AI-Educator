
from sqlalchemy.orm import Session as DBSession
from app import models
from app.agents import teaching_agents


async def finalize_session(db: DBSession, session: models.TeachingSession) -> models.Assessment:
    lesson = session.lesson
    state = session.state or {}
    qa_log = state.get("qa_log", [])

    report = await teaching_agents.generate_assessment_report(lesson.topic, qa_log, lesson.language)

    assessment = models.Assessment(
        session_id=session.id,
        topic=lesson.topic,
        score_percent=report["score_percent"],
        strong_areas=report["strong_areas"],
        weak_areas=report["weak_areas"],
        misconceptions=report["misconceptions"],
        recommended_revision=report["recommended_revision"],
        next_topic=report["next_topic"],
        raw_questions=report["raw_questions"],
    )
    db.add(assessment)

    _update_learner_profile(db, lesson.student_id, lesson.topic, report)

    session.status = "completed"
    lesson.status = "completed"
    db.commit()
    db.refresh(assessment)
    return assessment


def _update_learner_profile(db: DBSession, student_id: str, topic: str, report: dict):
    profile = db.query(models.LearnerProfile).filter_by(student_id=student_id).first()
    if not profile:
        profile = models.LearnerProfile(student_id=student_id)
        db.add(profile)
        db.flush()

    topics = set(profile.topics_studied or [])
    topics.add(topic)
    profile.topics_studied = list(topics)

    mastered = set(profile.concepts_mastered or [])
    for area in report.get("strong_areas", []):
        mastered.add(area)
    weak = set(profile.weak_concepts or [])
    for area in report.get("weak_areas", []):
        weak.add(area)
    # A concept newly mastered should no longer count as weak
    weak -= mastered
    profile.concepts_mastered = list(mastered)
    profile.weak_concepts = list(weak)
    db.commit()
