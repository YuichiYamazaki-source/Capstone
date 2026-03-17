import logging
import re
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.agent.learning_advisor import run_agent
from app.guardrails import sanitize_output, validate_input
from app.monitoring import record_request_metrics
from app.observability import observe_function

router = APIRouter(tags=["chat"])
logger = logging.getLogger("ai-service.chat")

MAX_HISTORY_MESSAGES = 20

# ObjectId: 24 hex characters
_OBJECT_ID_RE = re.compile(r"^[0-9a-fA-F]{24}$")


class HistoryMessage(BaseModel):
    """A single message in the conversation history."""

    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Incoming chat request with message and optional context."""

    message: str = Field(..., min_length=1, max_length=2000)
    user_id: str | None = None
    conversation_id: str | None = None
    history: list[HistoryMessage] = []

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str | None) -> str | None:
        """Ensure user_id is a valid MongoDB ObjectId format."""
        if v is not None and not _OBJECT_ID_RE.match(v):
            raise ValueError(
                "user_id must be a 24-character hex string (MongoDB ObjectId)"
            )
        return v


class CourseData(BaseModel):
    """Structured course data returned in chat responses."""

    id: str = ""
    title: str = ""
    organization: str = ""
    level: str = ""
    rating: float | None = None
    skills: list[str] = []
    url: str | None = None


class ChatResponse(BaseModel):
    """Chat response containing the agent reply and metadata."""

    reply: str
    conversation_id: str | None = None
    agent: str = "Learning Advisor"
    tool_calls: list[str] = []
    retrieval_tool_calls: list[str] = []
    retrieval_args: dict = {}
    all_tool_calls: list[str] = []
    latency_ms: float = 0.0
    courses: list[CourseData] = []


@router.post("/chat", response_model=ChatResponse)
@observe_function(name="chat_request")
async def chat(request: ChatRequest):
    """Process a chat message through the learning advisor agent.

    Args:
        request: Chat request with user message and optional history.

    Returns:
        ChatResponse with agent reply, tool calls, and course data.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Input guardrails
    sanitized_message, guardrail_error = await validate_input(request.message)
    if guardrail_error:
        return ChatResponse(reply=guardrail_error)

    start = time.perf_counter()

    # Truncate history to prevent context overflow and cost explosion
    recent_history = request.history[-MAX_HISTORY_MESSAGES:]
    history = [{"role": msg.role, "content": msg.content} for msg in recent_history]

    try:
        result = await run_agent(
            message=sanitized_message,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            history=history,
        )
    except Exception as e:
        logger.error("Agent execution failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail="Something went wrong. Please try again.",
        ) from e

    latency_ms = (time.perf_counter() - start) * 1000

    record_request_metrics(
        query=sanitized_message,
        result=result,
        user_id=request.user_id,
        latency_ms=latency_ms,
    )

    # Output guardrails
    reply = sanitize_output(result["reply"])

    return ChatResponse(
        reply=reply,
        conversation_id=result.get("conversation_id"),
        agent=result.get("agent", "Learning Advisor"),
        tool_calls=result.get("tool_calls", []),
        retrieval_tool_calls=result.get("retrieval_tool_calls", []),
        retrieval_args=result.get("retrieval_args", {}),
        all_tool_calls=result.get("all_tool_calls", []),
        latency_ms=round(latency_ms, 2),
        courses=result.get("courses", []),
    )
