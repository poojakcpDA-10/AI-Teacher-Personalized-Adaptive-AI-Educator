from sqlalchemy.orm import Session as DBSession
from sqlalchemy.orm.attributes import flag_modified
from app import models
from app.agents import teaching_agents
from app.services import video_service


def _subject_hint(topic: str) -> str:
    t = topic.lower()
    if any(k in t for k in ["math", "algebra", "calculus", "geometry", "equation"]):
        return "math"
    if any(k in t for k in ["physics", "force", "motion", "energy", "electric"]):
        return "physics"
    if any(k in t for k in ["biology", "cell", "organ", "anatomy", "gene"]):
        return "biology"
    if any(k in t for k in ["history", "war", "revolution", "empire", "century"]):
        return "history"
    if any(k in t for k in ["python", "code", "programming", "algorithm", "react", "javascript", "software"]):
        return "programming"
    return "general"


async def create_session(db: DBSession, lesson: models.LessonPlan) -> models.TeachingSession:
    session = models.TeachingSession(lesson_id=lesson.id, current_section_index=0, state={})
    db.add(session)
    lesson.status = "in_progress"
    db.commit()
    db.refresh(session)
    return session


def _make_turn(session_id: str, turn_type: str, media: dict, content: str, **extra) -> models.SessionTurn:
    turn = models.SessionTurn(
        session_id=session_id, turn_type=turn_type, role="teacher", content=content,
        segments=media.get("segments"), video_url=media.get("video_url"),
        audio_url=media.get("audio_url"), visual_url=media.get("visual_url"),
        **extra,
    )
    return turn


async def next_turn(db: DBSession, session: models.TeachingSession):
    """Produce the next teacher turn, or None if the lesson is finished."""
    lesson = session.lesson
    sections = (lesson.plan_json or {}).get("sections", [])
    state = dict(session.state or {})

    if state.get("pending_question"):
        raise ValueError("A question is still awaiting the student's answer.")

    idx = session.current_section_index
    if idx >= len(sections):
        session.status = "completed"
        db.commit()
        return None

    section = sections[idx]
    stype = section.get("type", "concept")
    subject = _subject_hint(lesson.topic)

    if stype in ("introduction", "concept", "example"):
        explanation = await teaching_agents.explain_concept(
            topic=lesson.topic, section_title=section.get("title", ""),
            section_content_hint=section.get("content", ""), level=lesson.level,
            language=lesson.language, student_id=lesson.student_id, document_id=lesson.document_id,
        )
        visual_spec = None
        if stype in ("concept", "example"):
            visual_spec = await teaching_agents.plan_visual(lesson.topic, subject, section.get("title", ""))

        segments = [{"label": "Explain", "text": explanation, "expression": "explain", "visual_spec": None}]
        if visual_spec:
            segments.append({
                "label": "Demonstrate",
                "text": f"Let's look at this: {section.get('title', lesson.topic)}.",
                "expression": "demonstrate",
                "visual_spec": visual_spec,
            })

        # If the plan puts a question right after this concept, fold Explain
        # -> Demonstrate -> Question into one continuous video so the whole
        # beat plays back as a single clip.
        next_section = sections[idx + 1] if idx + 1 < len(sections) else None
        merges_question = bool(next_section) and next_section.get("type") == "question"

        if merges_question:
            question_text = await teaching_agents.generate_question(
                lesson.topic, next_section.get("title", ""), lesson.level, lesson.language, "conceptual")
            segments.append({"label": "Question", "text": question_text, "expression": "question", "visual_spec": None})

            media = video_service.build_combined_video(segments, lesson.language)
            turn = _make_turn(session.id, "lesson_segment", media,
                               content=f"{explanation}\n\n{question_text}", visual_spec=visual_spec)
            db.add(turn)
            state["pending_question"] = question_text
            state["pending_language"] = lesson.language
            state["pending_is_assessment"] = False
            session.state = state
            flag_modified(session, "state")
            session.current_section_index = idx + 2
            db.commit()
            db.refresh(turn)
            return turn

        media = video_service.build_combined_video(segments, lesson.language)
        turn = _make_turn(session.id, "lesson_segment", media, content=explanation, visual_spec=visual_spec)
        db.add(turn)
        session.current_section_index = idx + 1
        db.commit()
        db.refresh(turn)
        return turn

    if stype == "question":
        question_text = await teaching_agents.generate_question(
            lesson.topic, section.get("title", ""), lesson.level, lesson.language, "conceptual")
        media = video_service.build_combined_video(
            [{"label": "Question", "text": question_text, "expression": "question", "visual_spec": None}],
            lesson.language,
        )
        turn = _make_turn(session.id, "question", media, content=question_text)
        db.add(turn)
        state["pending_question"] = question_text
        state["pending_language"] = lesson.language
        state["pending_is_assessment"] = False
        session.state = state
        flag_modified(session, "state")
        session.current_section_index = idx + 1
        db.commit()
        db.refresh(turn)
        return turn

    if stype == "assessment":
        target = section.get("num_questions", 3)
        if state.get("assessment_section_idx") != idx:
            state["assessment_section_idx"] = idx
            state["assessment_remaining"] = target

        if state.get("assessment_remaining", 0) <= 0:
            session.current_section_index = idx + 1
            session.state = state
            flag_modified(session, "state")
            db.commit()
            return await next_turn(db, session)

        q_num = target - state["assessment_remaining"] + 1
        question_text = await teaching_agents.generate_question(
            lesson.topic, f"Assessment question {q_num}/{target}", lesson.level, lesson.language, "mixed")
        media = video_service.build_combined_video(
            [{"label": "Assessment", "text": question_text, "expression": "question", "visual_spec": None}],
            lesson.language,
        )
        turn = _make_turn(session.id, "assessment_question", media, content=question_text)
        db.add(turn)
        state["pending_question"] = question_text
        state["pending_language"] = lesson.language
        state["pending_is_assessment"] = True
        session.state = state
        flag_modified(session, "state")
        db.commit()
        db.refresh(turn)
        return turn

    # Unknown section type -> skip it
    session.current_section_index = idx + 1
    db.commit()
    return await next_turn(db, session)


async def submit_answer(db: DBSession, session: models.TeachingSession, answer_text: str) -> dict:
    state = dict(session.state or {})
    question = state.get("pending_question")
    if not question:
        raise ValueError("No question is currently pending for this session.")

    lesson = session.lesson
    language = state.get("pending_language", lesson.language)

    student_turn = models.SessionTurn(
        session_id=session.id, turn_type="answer", role="student", content=answer_text)
    db.add(student_turn)

    eval_result = await teaching_agents.evaluate_answer(question, answer_text, lesson.topic, language)
    is_correct = bool(eval_result.get("is_correct"))
    student_turn.is_correct = is_correct
    feedback = eval_result.get("feedback", "")

    if is_correct:
        # Evaluate only — one short, positive video segment.
        media = video_service.build_combined_video(
            [{"label": "Feedback", "text": feedback, "expression": "evaluation_correct", "visual_spec": None}],
            language,
        )
        eval_turn = _make_turn(session.id, "evaluation", media, content=feedback, is_correct=True)
        db.add(eval_turn)
    else:
        # Evaluate -> Adapt, combined into ONE video: the feedback, then a
        # fresh explanation with a new example addressing the misconception.
        misc = await teaching_agents.detect_misconception(question, answer_text, lesson.topic, language)
        adapt_text = f"{misc.get('alternative_explanation', '')} For example: {misc.get('new_example', '')}"
        segments = [
            {"label": "Feedback", "text": feedback, "expression": "evaluation_incorrect", "visual_spec": None},
            {"label": "Let's re-look at this", "text": adapt_text, "expression": "misconception", "visual_spec": None},
        ]
        media = video_service.build_combined_video(segments, language)
        eval_turn = _make_turn(
            session.id, "adapt", media, content=f"{feedback}\n\n{adapt_text}",
            is_correct=False, misconception=misc.get("misconception"),
        )
        db.add(eval_turn)

    qa_log = state.get("qa_log", [])
    qa_log.append({"question": question, "answer": answer_text, "is_correct": is_correct})
    state["qa_log"] = qa_log

    if state.get("pending_is_assessment"):
        state["assessment_remaining"] = max(0, state.get("assessment_remaining", 1) - 1)

    state["pending_question"] = None
    state["pending_is_assessment"] = False
    session.state = state
    flag_modified(session, "state")
    db.commit()
    db.refresh(student_turn)
    db.refresh(eval_turn)

    return {"student_turn": student_turn, "eval_turn": eval_turn, "misconception_turn": None}


def progress(session: models.TeachingSession) -> dict:
    lesson = session.lesson
    sections = (lesson.plan_json or {}).get("sections", [])
    total = len(sections) or 1
    return {
        "current_section_index": session.current_section_index,
        "total_sections": total,
        "percent_complete": round(100 * min(session.current_section_index, total) / total, 1),
        "status": session.status,
    }