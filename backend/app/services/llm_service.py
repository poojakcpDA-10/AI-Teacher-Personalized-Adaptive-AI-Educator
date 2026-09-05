
import json
import re
import httpx
from app.config import settings


SYSTEM_PROMPT = (
    "You are an expert, patient human-like teacher. You explain concepts "
    "clearly, use simple analogies appropriate to the learner's level, "
    "and always ground your answers in any provided context. When asked "
    "to output JSON, output ONLY valid JSON with no markdown fences and "
    "no commentary."
)


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER

    async def _call_ollama(self, prompt: str, system: str = SYSTEM_PROMPT) -> str:
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }
        # connect timeout stays short (fails fast if Ollama isn't running at all);
        # read timeout is generous because a cold model load + generation on
        # CPU-only hardware can legitimately take several minutes.
        timeout = httpx.Timeout(connect=5.0, read=300.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")

    async def _call_openai_compatible(self, prompt: str, system: str = SYSTEM_PROMPT) -> str:
        url = f"{settings.OPENAI_COMPATIBLE_BASE_URL}/chat/completions"
        headers = {"Authorization": f"Bearer {settings.OPENAI_COMPATIBLE_API_KEY}"}
        payload = {
            "model": settings.OPENAI_COMPATIBLE_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _mock(self, prompt: str) -> str:
        """Very small heuristic responder so the demo works with zero setup."""
        return _mock_response(prompt)

    async def generate(self, prompt: str, system: str = SYSTEM_PROMPT, json_mode: bool = False) -> str:
        try:
            if self.provider == "ollama":
                text = await self._call_ollama(prompt, system)
            elif self.provider == "openai_compatible":
                text = await self._call_openai_compatible(prompt, system)
            else:
                text = self._mock(prompt)
        except Exception:
            # Backend unreachable (e.g. Ollama not running) -> fall back to mock
            # so the product still functions end-to-end for demo purposes.
            text = self._mock(prompt)

        if json_mode:
            text = _extract_json(text)
        return text

    async def generate_json(self, prompt: str, system: str = SYSTEM_PROMPT) -> dict:
        raw = await self.generate(prompt, system, json_mode=True)
        try:
            return json.loads(raw)
        except Exception:
            return {}


def _extract_json(text: str) -> str:
    """Strip markdown fences / prose around a JSON blob."""
    text = text.strip()
    text = re.sub(r"^```json\s*|^```\s*|```$", "", text, flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
    return match.group(0) if match else text


# ---------------------------------------------------------------------------
# Mock provider — deterministic fallback (no external calls)
# ---------------------------------------------------------------------------
def _mock_response(prompt: str) -> str:
    p = prompt.lower()

    if "lesson plan" in p or "structured lesson" in p:
        return json.dumps({
            "sections": [
                {"title": "Introduction", "duration_minutes": 3, "type": "introduction",
                 "content": "Introduce the topic, connect it to something the student already knows."},
                {"title": "Core Concept 1", "duration_minutes": 5, "type": "concept",
                 "content": "Explain the first key concept with a simple analogy."},
                {"title": "Worked Example", "duration_minutes": 4, "type": "example",
                 "content": "Walk through one concrete example step by step."},
                {"title": "Check Understanding", "duration_minutes": 3, "type": "question",
                 "content": "Ask a conceptual question to check understanding."},
                {"title": "Core Concept 2", "duration_minutes": 3, "type": "concept",
                 "content": "Build on concept 1 with a related idea."},
                {"title": "Final Assessment", "duration_minutes": 2, "type": "assessment",
                 "content": "Ask 2-3 questions covering the whole lesson."},
            ]
        })

    if "visual_type" in p or "visual planner" in p:
        return json.dumps({"visual_type": "diagram", "subject": "general", "concept": "overview"})

    if "misconception" in p:
        return json.dumps({
            "misconception": "The student may be conflating two related quantities.",
            "alternative_explanation": "Let's use a simple analogy: think of it like water flowing through a pipe.",
            "new_example": "If you widen the pipe (reduce resistance), more water (current) flows for the same pressure (voltage)."
        })

    if "evaluate" in p and "answer" in p:
        return json.dumps({"is_correct": False, "feedback": "Not quite — let's look at this differently.",
                            "confidence": 0.5})

    if "learning path" in p or "learning_path" in p:
        return json.dumps({"steps": [
            {"step": 1, "title": "Fundamentals"},
            {"step": 2, "title": "Core Concepts"},
            {"step": 3, "title": "Practice"},
            {"step": 4, "title": "Advanced Topics"},
            {"step": 5, "title": "Assessment"},
        ]})

    if "assessment" in p and "report" in p:
        return json.dumps({
            "score_percent": 70,
            "strong_areas": ["Basic definitions"],
            "weak_areas": ["Applied problems"],
            "misconceptions": ["Confusing related terms"],
            "recommended_revision": ["Revise the core formula", "Solve 2 more practice problems"],
            "next_topic": "Next topic in the sequence"
        })

    return ("This is a locally-generated placeholder response because no LLM "
            "backend (Ollama/Qwen3) is currently reachable. Connect Ollama "
            "(see README) to get real, grounded teaching content.")


llm_service = LLMService()