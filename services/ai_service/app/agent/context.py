"""Request-scoped context for collecting structured data from tool calls.

Uses contextvars.ContextVar for async-safe per-request isolation.
Each agent run resets before starting and reads after completion.
"""

from contextvars import ContextVar

_collected_courses: ContextVar[list[dict]] = ContextVar("_collected_courses")
_retrieval_tool_calls: ContextVar[list[str]] = ContextVar("_retrieval_tool_calls")
_retrieval_args: ContextVar[dict] = ContextVar("_retrieval_args")
_all_tool_calls: ContextVar[list[str]] = ContextVar("_all_tool_calls")


def reset_collected_courses() -> None:
    """Reset the collected courses list for a new request."""
    _collected_courses.set([])


def add_collected_courses(courses: list[dict]) -> None:
    """Append courses to the current request's collected courses.

    Args:
        courses: List of course dictionaries to add.
    """
    _collected_courses.get([]).extend(courses)


def get_collected_courses() -> list[dict]:
    """Return deduplicated collected courses for the current request.

    Returns:
        List of unique course dictionaries, deduplicated by title.
    """
    seen: set[str] = set()
    unique: list[dict] = []
    for course in _collected_courses.get([]):
        title = course.get("title", "")
        if title not in seen:
            seen.add(title)
            unique.append(course)
    return unique


def reset_retrieval_tool_calls() -> None:
    """Reset the retrieval tool calls list for a new request."""
    _retrieval_tool_calls.set([])


def add_retrieval_tool_calls(tool_names: list[str]) -> None:
    """Append tool names to the current request's retrieval tool call list.

    Args:
        tool_names: List of retrieval tool names that were invoked.
    """
    _retrieval_tool_calls.get([]).extend(tool_names)


def get_retrieval_tool_calls() -> list[str]:
    """Return a copy of the retrieval tool calls for the current request."""
    return list(_retrieval_tool_calls.get([]))


def reset_retrieval_args() -> None:
    """Reset the retrieval arguments for a new request."""
    _retrieval_args.set({})


def set_retrieval_args(args: dict) -> None:
    """Store retrieval arguments for the current request.

    Args:
        args: Dictionary of retrieval parameters used by the agent.
    """
    _retrieval_args.set(args)


def get_retrieval_args() -> dict:
    """Return a copy of the retrieval arguments for the current request."""
    return dict(_retrieval_args.get({}))


def reset_all_tool_calls() -> None:
    """Reset the all-tool-calls list for a new request."""
    _all_tool_calls.set([])


def add_tool_call(tool_name: str) -> None:
    """Record that a tool was invoked during this request.

    Args:
        tool_name: Name of the tool function that was called.
    """
    _all_tool_calls.get([]).append(tool_name)


def get_all_tool_calls() -> list[str]:
    """Return all tool calls recorded during this request."""
    return list(_all_tool_calls.get([]))
