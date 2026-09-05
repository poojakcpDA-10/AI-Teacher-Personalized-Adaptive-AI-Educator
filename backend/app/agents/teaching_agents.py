
from app.services.llm_service import llm_service
from app.services import rag_service


async def explain_concept(topic: str, section_title: str, section_content_hint: str,
                           level: str, language: str, student_id: str,
                           document_id: str | None) -> str:
    context = ""
    if document_id or rag_service.has_documents(student_id):
        hits = rag_service.retrieve_context(student_id, f"{topic} {section_title}", document_id, top_k=4)
        if hits:
            context = "\n---\n".join(h["text"][:600] for h in hits)

    # Built separately because backslashes (e.g. \n) cannot be used
    # inside an f-string expression.
    if context:
        source_instruction = "Ground your explanation in this source material where relevant:\n" + context
    else:
        source_instruction = "No source material provided — use general knowledge."

    prompt = f"""
You are teaching a {level} student in {language}.
Topic: {topic}
Section: {section_title}
What this section should cover: {section_content_hint}

{source_instruction}

Write the explanation as the teacher would actually say it out loud:
warm, clear, using a simple analogy suited to a {level} learner. Keep it
focused (roughly 80-150 words). Respond in {language}. Do not use markdown headers.
"""
    return await llm_service.generate(prompt)


async def generate_question(topic: str, section_title: str, level: str, language: str,
                             question_type: str = "conceptual") -> str:
    prompt = f"""
Create one {question_type} question (not multiple choice unless asked) to
check a {level} student's understanding of "{section_title}" within the
topic "{topic}". Respond in {language}. Return only the question text,
no preamble, no answer.
"""
    return await llm_service.generate(prompt)


async def evaluate_answer(question: str, student_answer: str, topic: str, language: str) -> dict:
    prompt = f"""
Question asked: {question}
Student's answer: {student_answer}
Topic: {topic}

Evaluate whether the answer is correct or shows understanding (it does not
need to be word-perfect). Return ONLY JSON:
{{"is_correct": true|false, "feedback": "one short sentence of feedback in {language}", "confidence": 0.0-1.0}}
"""
    result = await llm_service.generate_json(prompt)
    if "is_correct" not in result:
        result = {"is_correct": False, "feedback": "Let's look at that again.", "confidence": 0.3}
    return result


async def detect_misconception(question: str, student_answer: str, topic: str, language: str) -> dict:
    prompt = f"""
A student was asked: "{question}"
They answered incorrectly: "{student_answer}"
Topic: {topic}

1. Identify the likely underlying misconception in one sentence.
2. Provide an alternative explanation using a different analogy than a
   typical textbook would (something concrete/everyday).
3. Provide one new, simpler example illustrating the correct idea.
All text in {language}.

Return ONLY JSON:
{{"misconception": "...", "alternative_explanation": "...", "new_example": "..."}}
"""
    result = await llm_service.generate_json(prompt)
    if "misconception" not in result:
        result = {
            "misconception": "The student may have mixed up two related ideas.",
            "alternative_explanation": "Let's approach this from a different angle with a simple everyday comparison.",
            "new_example": "Consider a simple, concrete situation that isolates just this one idea.",
        }
    return result


async def plan_visual(topic: str, subject_hint: str, concept: str) -> dict:
    """
    Decides WHAT KIND of visual fits the concept before any rendering happens
    — mirrors the assessment's requirement to demonstrate subject-aware
    visual selection rather than "just generate an image".
    """
    prompt = f"""
Topic/subject: {topic} ({subject_hint})
Concept being taught right now: {concept}

Decide the single most appropriate visual type from this fixed set:
["graph", "equation", "force_diagram", "labeled_diagram", "timeline", "map",
 "code_flow", "architecture_diagram", "flowchart", "plain_illustration"]

Return ONLY JSON:
{{"visual_type": "...", "subject": "math|physics|biology|history|programming|general", "concept": "{concept}", "title": "short chart/diagram title"}}
"""
    result = await llm_service.generate_json(prompt)
    if "visual_type" not in result:
        result = {"visual_type": "plain_illustration", "subject": "general", "concept": concept, "title": concept}
    return result


async def generate_assessment_report(topic: str, qa_log: list[dict], language: str) -> dict:
    """
    qa_log: [{"question": ..., "answer": ..., "is_correct": bool}, ...]
    Score is computed programmatically (per the assessment's explicit
    recommendation) — the LLM only synthesizes the qualitative summary.
    """
    total = len(qa_log) or 1
    correct = sum(1 for q in qa_log if q.get("is_correct"))
    score = round(100 * correct / total, 1)

    prompt = f"""
Topic: {topic}
Here is the record of questions asked during the lesson and whether the
student answered correctly:
{qa_log}

Based ONLY on this record, in {language}, return ONLY JSON:
{{"strong_areas": ["..."], "weak_areas": ["..."], "misconceptions": ["..."],
  "recommended_revision": ["...", "..."], "next_topic": "a sensible next topic to study"}}
"""
    qualitative = await llm_service.generate_json(prompt)
    return {
        "score_percent": score,
        "strong_areas": qualitative.get("strong_areas", []),
        "weak_areas": qualitative.get("weak_areas", []),
        "misconceptions": qualitative.get("misconceptions", []),
        "recommended_revision": qualitative.get("recommended_revision", []),
        "next_topic": qualitative.get("next_topic", ""),
        "raw_questions": qa_log,
    }


async def generate_learning_path(topic: str, level: str) -> dict:
    prompt = f"""
Create a structured learning path (ordered list of steps/subtopics) to
learn "{topic}" from the beginning for a {level} learner. 6-10 steps.
Return ONLY JSON: {{"steps": [{{"step": 1, "title": "..."}}, ...]}}
"""
    result = await llm_service.generate_json(prompt)
    if "steps" not in result:
        result = {"steps": [{"step": 1, "title": f"Introduction to {topic}"}]}
    return result