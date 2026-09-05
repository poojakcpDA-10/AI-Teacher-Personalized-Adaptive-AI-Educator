
from app.services.llm_service import llm_service
from app.services import rag_service


def _time_bucket(minutes: int) -> str:
    if minutes <= 10080 and minutes >= 1440:  # >= 1 day worth, treat as multi-day
        return "multi_day"
    if minutes <= 7:
        return "very_short"
    if minutes <= 25:
        return "short"
    return "long"


async def build_lesson_plan(
    student_id: str,
    topic: str,
    level: str,
    language: str,
    time_minutes: int,
    document_id: str | None,
    instructions: str,
    weak_concepts: list[str] | None = None,
) -> dict:
    bucket = _time_bucket(time_minutes)

    context_snippets = []
    if document_id or rag_service.has_documents(student_id):
        results = rag_service.retrieve_context(student_id, topic, document_id=document_id, top_k=6)
        context_snippets = [r["text"][:800] for r in results]

    context_block = "\n---\n".join(context_snippets) if context_snippets else "(No uploaded material — teach from general knowledge.)"
    weak = ", ".join(weak_concepts or []) or "none recorded yet"

    if bucket == "multi_day":
        days = max(1, min(14, round(time_minutes / 1440)))
        prompt = f"""
Create a {days}-day personalized learning plan for the topic "{topic}".
Student level: {level}. Language: {language}. Weak concepts so far: {weak}.
Extra instructions from student: {instructions}

Relevant source material (may be empty):
{context_block}

Return ONLY JSON in this exact shape:
{{"sections": [{{"title": "Day 1: ...", "duration_minutes": 60, "type": "concept", "content": "what to cover"}}, ...]}}
One entry per day. duration_minutes is the recommended study time for that day.
"""
    else:
        prompt = f"""
Create a structured lesson plan to teach "{topic}" in exactly {time_minutes} minutes.
Student level: {level}. Language: {language}. Weak concepts so far: {weak}.
Extra instructions from student: {instructions}

Relevant source material (may be empty, in which case teach from general knowledge but say so):
{context_block}

Follow this teaching structure: introduction, one or more core concepts (with
analogies suited to a {level} learner), at least one worked example, at
least one interactive question (type: "question") placed *during* the
lesson (not only at the end), and a final assessment (type: "assessment").
Durations in minutes must sum to approximately {time_minutes}.

Return ONLY JSON in this exact shape:
{{"sections": [{{"title": "...", "duration_minutes": 3, "type": "introduction|concept|example|question|assessment", "content": "..."}}, ...]}}
"""

    plan = await llm_service.generate_json(prompt)
    if not plan or "sections" not in plan:
        plan = _fallback_plan(topic, time_minutes, bucket)

    plan["topic"] = topic
    plan["level"] = level
    plan["language"] = language
    plan["time_minutes"] = time_minutes
    plan["grounded_in_material"] = bool(context_snippets)
    return plan


def _fallback_plan(topic: str, minutes: int, bucket: str) -> dict:
    if bucket == "very_short":
        return {"sections": [
            {"title": f"Key idea of {topic}", "duration_minutes": max(1, minutes - 2), "type": "concept",
             "content": f"A very concise explanation of the single most important idea in {topic}."},
            {"title": "Quick Check", "duration_minutes": 2, "type": "question",
             "content": "One quick question to confirm understanding."},
        ]}
    if bucket == "multi_day":
        days = max(1, round(minutes / 1440))
        return {"sections": [
            {"title": f"Day {i+1}", "duration_minutes": 60, "type": "concept",
             "content": f"Study session {i+1} on {topic}."} for i in range(days)
        ]}
    return {"sections": [
        {"title": "Introduction", "duration_minutes": max(2, round(minutes * 0.15)), "type": "introduction",
         "content": f"Introduce {topic} and connect it to something familiar."},
        {"title": "Core Concept", "duration_minutes": max(3, round(minutes * 0.3)), "type": "concept",
         "content": f"Explain the central idea behind {topic}."},
        {"title": "Worked Example", "duration_minutes": max(3, round(minutes * 0.2)), "type": "example",
         "content": "Walk through one concrete example."},
        {"title": "Check Understanding", "duration_minutes": max(2, round(minutes * 0.15)), "type": "question",
         "content": "Ask a question to check understanding."},
        {"title": "Final Assessment", "duration_minutes": max(2, round(minutes * 0.2)), "type": "assessment",
         "content": "2-3 questions covering the lesson."},
    ]}
