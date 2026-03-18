"""Career Advisor — career consultation and course recommendations.

Researches career paths, maps required skills, and recommends
courses aligned with the user's career goals.
"""

from agents import Agent, ModelSettings

from app.agent.course_retrieval import retrieve_courses
from app.config import settings
from app.prompts import get_prompt
from app.tools.get_user_profile import get_user_profile
from app.tools.web_search import web_search

_FALLBACK_PROMPT = """\
You are Career Advisor, a specialist in tech career planning \
and educational guidance.
"""

career_agent = Agent(
    name="Career Advisor",
    handoff_description="Provides career path guidance, researches job market "  # LLM-facing: changes affect model behavior
    "requirements, and recommends courses aligned with career goals.",
    instructions=get_prompt("career-advisor", _FALLBACK_PROMPT),
    model=settings.openai_model,
    model_settings=ModelSettings(temperature=0, max_tokens=4096),
    tools=[get_user_profile, retrieve_courses, web_search],
)
