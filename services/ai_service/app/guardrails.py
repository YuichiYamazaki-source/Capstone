"""Input and output guardrails for the AI service.

Input guardrails:
  1. Topic relevance — keyword whitelist, then LLM fallback
  2. Prompt injection detection — regex patterns
  3. Input sanitization — strip control chars, normalize whitespace

Output guardrails:
  1. PII leakage check — email, phone, SSN patterns
  2. System info leakage — stack traces, internal URLs, env vars
  3. Response structure — no raw error dumps
"""

import logging
import os
import re

logger = logging.getLogger("ai-service.guardrails")

# LLM-as-Judge prompt — managed in LangFuse for version tracking
TOPIC_CLASSIFIER_PROMPT = (
    "You are a classifier. Determine if the user message is related to "
    "education, courses, learning, skills, career guidance, or professional "
    "development. Reply with ONLY 'yes' or 'no'."
)


def _fetch_topic_classifier_prompt() -> str:
    """Fetch topic classifier prompt from LangFuse, fall back to hardcoded."""
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        return TOPIC_CLASSIFIER_PROMPT
    try:
        from langfuse import get_client

        client = get_client()
        prompt = client.get_prompt("topic-classifier", label="latest")
        logger.info("Topic classifier prompt fetched from LangFuse (v%s)", prompt.version)
        return prompt.prompt
    except Exception as e:
        logger.warning("LangFuse prompt fetch failed, using hardcoded", extra={"error": str(e)})
        return TOPIC_CLASSIFIER_PROMPT

# --- Input Guardrails ---

# Keywords that indicate an on-topic message
_TOPIC_KEYWORDS = {
    "course",
    "courses",
    "learn",
    "learning",
    "skill",
    "skills",
    "career",
    "study",
    "training",
    "certificate",
    "certification",
    "degree",
    "education",
    "tutorial",
    "beginner",
    "intermediate",
    "advanced",
    "programming",
    "coding",
    "developer",
    "engineer",
    "data",
    "machine learning",
    "ai",
    "cloud",
    "web",
    "python",
    "javascript",
    "java",
    "sql",
    "analytics",
    "path",
    "recommend",
    "suggestion",
    "gap",
    "profile",
    "goal",
    "job",
    "resume",
    "portfolio",
    "mentor",
    "roadmap",
    "curriculum",
    "class",
    "classes",
    "module",
    "lesson",
    "teach",
    "homework",
    "assignment",
    "exam",
    "quiz",
    "project",
    "internship",
    "bootcamp",
    "online",
    "coursera",
    "udemy",
    "edx",
    "mooc",
    "university",
    "college",
    "specialization",
    "professional",
    "upskill",
    "reskill",
    "salary",
    "market",
    "industry",
    "trend",
    "demand",
    "hire",
    "hiring",
    "interview",
    "hello",
    "hi",
    "hey",
    "thanks",
    "thank",
}

# Prompt injection patterns
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)", re.I),
    re.compile(r"you\s+are\s+now\s+(a|an|the)\b", re.I),
    re.compile(r"(system\s+prompt|system\s+message|initial\s+prompt)", re.I),
    re.compile(r"(pretend|act\s+as\s+if)\s+you\s+(are|were)\b", re.I),
    re.compile(r"(reveal|show|display|print|output)\s+(your|the)\s+(system|initial|original)\s+(prompt|instructions?|message)", re.I),
    re.compile(r"new\s+instructions?\s*:", re.I),
    re.compile(r"override\s+(your|the|all)\s+(rules?|instructions?|constraints?)", re.I),
    re.compile(r"\bDAN\b.*mode", re.I),
    re.compile(r"jailbreak", re.I),
    re.compile(r"(forget|disregard|bypass)\s+(everything|all|your|the)\s+(above|rules?|instructions?)", re.I),
]

# Control characters to strip (keep newlines and tabs)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_input(text: str) -> str:
    """Strip control characters and normalize whitespace."""
    text = _CONTROL_CHAR_RE.sub("", text)
    # Collapse multiple whitespace (preserve single newlines)
    lines = text.split("\n")
    lines = [" ".join(line.split()) for line in lines]
    return "\n".join(lines).strip()


def check_prompt_injection(text: str) -> str | None:
    """Check for prompt injection patterns.

    Returns:
        Error message if injection detected, None if clean.
    """
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning(
                "Prompt injection detected",
                extra={"pattern": pattern.pattern, "input": text[:200]},
            )
            return (
                "I can only help with course recommendations, learning paths, "
                "and career guidance. Please rephrase your question."
            )
    return None


def check_topic_relevance(text: str) -> bool:
    """Check if the message is related to learning/courses/career.

    Returns:
        True if on-topic, False if off-topic.
    """
    lower = text.lower()
    return any(keyword in lower for keyword in _TOPIC_KEYWORDS)


async def classify_topic_llm(text: str) -> bool:
    """Use a short LLM call to classify topic relevance.

    Fallback when keyword matching fails.

    Returns:
        True if on-topic, False if off-topic.
    """
    from app.clients.openai_client import get_openai_client

    client = get_openai_client()
    try:
        classifier_prompt = _fetch_topic_classifier_prompt()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": classifier_prompt,
                },
                {"role": "user", "content": text[:500]},
            ],
            max_tokens=3,
            temperature=0,
        )
        answer = response.choices[0].message.content.strip().lower()
        return answer == "yes"
    except Exception as e:
        logger.warning("Topic classification failed, allowing message", extra={"error": str(e)})
        return True  # Fail open


def redact_input_pii(text: str) -> str:
    """Redact PII from user input before it reaches the LLM or logs."""
    original = text
    text = _EMAIL_RE.sub("[email redacted]", text)
    text = _PHONE_RE.sub("[phone redacted]", text)
    text = _SSN_RE.sub("[SSN redacted]", text)
    if text != original:
        logger.info("Input PII redacted")
    return text


async def validate_input(text: str) -> tuple[str, str | None]:
    """Run all input guardrails.

    Returns:
        Tuple of (sanitized_text, error_message_or_None).
    """
    sanitized = sanitize_input(text)

    if not sanitized:
        return sanitized, "Please enter a message."

    # Check prompt injection first
    injection_error = check_prompt_injection(sanitized)
    if injection_error:
        return sanitized, injection_error

    # Redact PII from input before it reaches the LLM
    sanitized = redact_input_pii(sanitized)

    # Check topic relevance
    if not check_topic_relevance(sanitized):
        is_on_topic = await classify_topic_llm(sanitized)
        if not is_on_topic:
            logger.info(
                "Off-topic message rejected",
                extra={"input": sanitized[:200]},
            )
            return sanitized, (
                "I'm specialized in course recommendations, learning paths, and career guidance. "
                "Could you ask something related to these topics?"
            )

    return sanitized, None


# --- Output Guardrails ---

# PII patterns
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# System info patterns
_STACK_TRACE_RE = re.compile(r"Traceback \(most recent call last\)", re.I)
_INTERNAL_URL_RE = re.compile(r"(localhost|127\.0\.0\.1|internal\.|\.local):\d+")
_ENV_VAR_RE = re.compile(r"(OPENAI_API_KEY|SECRET_KEY|PASSWORD|MONGO_URI|LANGFUSE_SECRET)\s*=\s*\S+", re.I)


def sanitize_output(text: str) -> str:
    """Remove PII and system information from agent output.

    Returns:
        Sanitized text with sensitive data redacted.
    """
    redacted = False

    # Redact PII
    if _EMAIL_RE.search(text):
        text = _EMAIL_RE.sub("[email redacted]", text)
        redacted = True
    if _PHONE_RE.search(text):
        text = _PHONE_RE.sub("[phone redacted]", text)
        redacted = True
    if _SSN_RE.search(text):
        text = _SSN_RE.sub("[SSN redacted]", text)
        redacted = True

    # Redact system info
    if _STACK_TRACE_RE.search(text):
        text = _STACK_TRACE_RE.split(text)[0].rstrip()
        if not text:
            text = "An error occurred while processing your request. Please try again."
        redacted = True
    if _INTERNAL_URL_RE.search(text):
        text = _INTERNAL_URL_RE.sub("[internal URL redacted]", text)
        redacted = True
    if _ENV_VAR_RE.search(text):
        text = _ENV_VAR_RE.sub("[credential redacted]", text)
        redacted = True

    if redacted:
        logger.warning("Output sanitization applied")

    return text
