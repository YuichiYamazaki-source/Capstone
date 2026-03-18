"""Learning Path Designer — builds structured multi-step learning plans.

Searches courses at multiple levels, checks prerequisites,
and designs an ordered learning path personalized to the user's current skills.
"""

from agents import Agent, ModelSettings

from app.agent.course_retrieval import retrieve_courses
from app.config import settings
from app.prompts import get_prompt
from app.tools.get_course_details import get_course_details
from app.tools.get_user_profile import get_user_profile

_FALLBACK_PROMPT = """\
You are Learning Path Designer, a specialist in creating structured, \
progressive learning plans.
"""

learning_path_agent = Agent(
    name="Learning Path Designer",
    handoff_description="Designs structured, multi-step learning paths "  # LLM-facing: changes affect model behavior
    "from beginner to advanced with prerequisite ordering.",
    instructions=get_prompt("learning-path-designer", _FALLBACK_PROMPT),
    model=settings.openai_model,
    model_settings=ModelSettings(temperature=0, max_tokens=4096),
    tools=[retrieve_courses, get_course_details, get_user_profile],
)
