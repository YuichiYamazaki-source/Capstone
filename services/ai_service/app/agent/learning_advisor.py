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
from app.prompts import get_prompt
from app.tools.get_user_profile import get_user_profile
from app.tools.update_user_profile import update_user_profile
from app.tools.web_search import web_search

logger = logging.getLogger("ai-service.agent.advisor")

_FALLBACK_PROMPT = """\
You are Learning Advisor, an AI assistant for the Intelligent University Course Finder.
Your role is to help students discover courses, plan learning paths, \
and make career-aligned study decisions.
Always call retrieve_courses before responding to course-related queries.
"""

learning_advisor = Agent(
    name="Learning Advisor",
    instructions=get_prompt("learning-advisor", _FALLBACK_PROMPT),
    model=settings.openai_model,
    model_settings=ModelSettings(temperature=0, max_tokens=4096),
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
