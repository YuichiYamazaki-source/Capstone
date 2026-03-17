import logging
import re
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.agent.learning_advisor import run_agent
from app.monitoring import record_request_metrics
from app.observability import observe_function

router = APIRouter(tags=["chat"])
logger = logging.getLogger("ai-service.chat")

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

    start = time.perf_counter()

    history = [{"role": msg.role, "content": msg.content} for msg in request.history]

    result = await run_agent(
        message=request.message,
        user_id=request.user_id,
        conversation_id=request.conversation_id,
        history=history,
    )

    latency_ms = (time.perf_counter() - start) * 1000

    record_request_metrics(
        query=request.message,
        result=result,
        user_id=request.user_id,
        latency_ms=latency_ms,
    )

    return ChatResponse(
        reply=result["reply"],
        conversation_id=result.get("conversation_id"),
        agent=result.get("agent", "Learning Advisor"),
        tool_calls=result.get("tool_calls", []),
        retrieval_tool_calls=result.get("retrieval_tool_calls", []),
        retrieval_args=result.get("retrieval_args", {}),
        latency_ms=round(latency_ms, 2),
        courses=result.get("courses", []),
    )
