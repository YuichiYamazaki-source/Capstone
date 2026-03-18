"""Skill Gap Analyst — identifies gaps between current skills and target role.

Fetches user profile, researches required skills for the target role,
computes the gap, and recommends courses to fill it.
"""

from agents import Agent, ModelSettings

from app.agent.course_retrieval import retrieve_courses
from app.config import settings
from app.prompts import get_prompt
from app.tools.get_user_profile import get_user_profile
from app.tools.web_search import web_search

_FALLBACK_PROMPT = """\
You are Skill Gap Analyst, a specialist in identifying skill gaps \
and recommending targeted learning paths.
"""

skill_gap_agent = Agent(
    name="Skill Gap Analyst",
    handoff_description="Analyzes skill gaps between the user's current abilities "  # LLM-facing: changes affect model behavior
    "and their target role, then recommends courses to fill gaps.",
    instructions=get_prompt("skill-gap-analyst", _FALLBACK_PROMPT),
    model=settings.openai_model,
    model_settings=ModelSettings(temperature=0, max_tokens=4096),
    tools=[get_user_profile, retrieve_courses, web_search],
)
