"""Learning Advisor Agent — orchestrator with multi-agent handoffs.

Routes user requests to specialized agents when appropriate:
  - Simple course search → handled directly (retrieve_courses)
  - Skill gap analysis → handoff → Skill Gap Analyst
  - Career consultation → handoff → Career Advisor
  - Learning path design → handoff → Learning Path Designer

Architecture: Learning Advisor (router) → handoff → sub-agent → final response.
Sub-agents have no handoffs (prevents loops).
"""

import logging

from agents import Agent, ModelSettings, Runner, handoff

from app.agent.career import career_agent
from app.agent.context import (
    get_all_tool_calls,
    get_collected_courses,
    get_retrieval_args,
    get_retrieval_tool_calls,
    reset_all_tool_calls,
    reset_collected_courses,
    reset_retrieval_args,
    reset_retrieval_tool_calls,
)
from app.agent.course_retrieval import retrieve_courses
from app.agent.learning_path import learning_path_agent
from app.agent.skill_gap import skill_gap_agent
from app.config import settings
from app.tools.get_user_profile import get_user_profile
from app.tools.update_user_profile import update_user_profile
from app.tools.web_search import web_search

logger = logging.getLogger("ai-service.agent.advisor")

ADVISOR_PROMPT = """\
You are Learning Advisor, an AI assistant for the Intelligent University Course Finder.

Your role is to help students discover courses, plan learning paths, \
and make career-aligned study decisions.

## Delegation Rules (follow this decision flow)

1. Is the request a greeting, small talk, or completely unrelated to learning?
   → Handle directly. Do NOT delegate.

2. Is the request a simple course search ("find Python courses", "beginner ML")?
   → Handle directly with retrieve_courses.

3. Is the request a profile update ("save my skills", "update my interests")?
   → Handle directly with update_user_profile.

4. Does the request ask about skill gaps, missing skills, or readiness for \
a specific role? (e.g. "What skills am I missing for ML Engineer?", \
"Analyze my skill gaps", "Am I ready for a data science role?")
   → Delegate to **Skill Gap Analyst**.

5. Does the request ask about career paths, job market, salary, industry \
trends, or which direction to take? (e.g. "What career should I pursue?", \
"What's the job outlook for AI engineers?", "Should I go into cloud or ML?")
   → Delegate to **Career Advisor**.

6. Does the request ask for a structured learning plan, curriculum, or \
step-by-step study path? (e.g. "Create a learning path for web development", \
"How should I study ML from beginner to advanced?")
   → Delegate to **Learning Path Designer**.

7. If the request has multiple intents, identify the primary intent and \
delegate to the matching specialist. If unclear, handle directly.

When in doubt, handle directly with retrieve_courses.

## Rules

1. **Always search first.** For ANY message about courses, learning, skills, \
or career goals, call retrieve_courses BEFORE responding. Never ask a \
clarifying question instead of searching.

2. **Pass the user's message as the query AND extract filter parameters.** \
Pass the user's original message as the `query` parameter for keyword/semantic \
matching. At the same time, extract any explicit constraints into the \
appropriate filter parameters:
  - "beginner courses" → level="Beginner"
  - "rating above 4.5" → min_rating=4.5
  - "courses from Google" → organization="Google"
  - "intermediate data science" → level="Intermediate", query="intermediate data science"
Both the query AND the filter parameters must be set in the same tool call. \
Do NOT omit filters just because the query already mentions them.

3. **Do NOT set filter parameters the user did not mention.** \
Only extract constraints that are explicitly stated.

4. **Personalize when user_id is available.** Only call get_user_profile if \
a real user_id is provided (formatted as [user_id: xxx]). Never fabricate one.

5. **Present recommendations with reasoning.** Explain why each course is \
relevant to the user's stated goal.

6. **Respond in the same language as the user's message.**

7. **Profile updates require restraint.** Only store information the user \
explicitly mentioned (skills, motivation, interest_areas). Never store \
personal opinions, chat content, or sensitive information.
"""

learning_advisor = Agent(
    name="Learning Advisor",
    instructions=ADVISOR_PROMPT,
    model=settings.openai_model,
    model_settings=ModelSettings(max_tokens=4096),
    tools=[
        retrieve_courses,
        get_user_profile,
        update_user_profile,
        web_search,
    ],
    handoffs=[
        handoff(skill_gap_agent),
        handoff(career_agent),
        handoff(learning_path_agent),
    ],
)


async def run_agent(
    message: str,
    user_id: str | None = None,
    conversation_id: str | None = None,
    history: list[dict] | None = None,
) -> dict:
    """Execute the Learning Advisor agent and return structured result.

    Returns dict with keys: reply, conversation_id, tool_calls,
    retrieval_tool_calls, courses, agent
    """
    user_context = f"[user_id: {user_id}] " if user_id else ""

    # Build input: conversation history + current message
    if history:
        input_messages = []
        for msg in history:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                input_messages.append({"role": "user", "content": content})
            elif role == "assistant":
                input_messages.append({"role": "assistant", "content": content})
        input_messages.append({"role": "user", "content": f"{user_context}{message}"})
        agent_input = input_messages
    else:
        agent_input = f"{user_context}{message}"

    reset_collected_courses()
    reset_retrieval_tool_calls()
    reset_retrieval_args()
    reset_all_tool_calls()

    result = await Runner.run(
        learning_advisor,
        input=agent_input,
    )

    # Track which agent produced the final response
    agent_name = result.last_agent.name if result.last_agent else "Learning Advisor"

    # Extract outer tool calls (Learning Advisor level)
    tool_calls = []
    for step_idx, item in enumerate(result.raw_responses):
        if not hasattr(item, "output") or not isinstance(item.output, list):
            continue

        for output in item.output:
            output_type = getattr(output, "type", None)

            if output_type == "function_call":
                tool_calls.append(output.name)
                logger.info(
                    "Tool call",
                    extra={
                        "step": step_idx,
                        "tool": output.name,
                        "arguments": getattr(output, "arguments", "")[:300],
                    },
                )

    retrieval_tool_calls = get_retrieval_tool_calls()

    logger.info(
        "Agent run completed",
        extra={
            "user_id": user_id,
            "agent": agent_name,
            "advisor_tools": tool_calls,
            "retrieval_tools": retrieval_tool_calls,
            "model": settings.openai_model,
        },
    )

    return {
        "reply": result.final_output,
        "conversation_id": conversation_id,
        "tool_calls": tool_calls,
        "retrieval_tool_calls": retrieval_tool_calls,
        "retrieval_args": get_retrieval_args(),
        "courses": get_collected_courses(),
        "agent": agent_name,
        "all_tool_calls": get_all_tool_calls(),
    }
