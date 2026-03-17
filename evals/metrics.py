"""Custom IR metrics for course search evaluation.

These metrics compare search results against ground truth
expected courses (by title matching) and filter satisfaction.
"""


def hit_rate(retrieved_titles: list[str], expected_titles: list[str]) -> float:
    """Binary: did at least one expected course appear in results?

    Returns 1.0 if any expected title is found, 0.0 otherwise.
    """
    retrieved_lower = {t.lower() for t in retrieved_titles}
    for expected in expected_titles:
        if expected.lower() in retrieved_lower:
            return 1.0
    return 0.0


def precision_at_k(
    retrieved_titles: list[str], expected_titles: list[str], k: int = 5
) -> float:
    """Fraction of top-K results that are relevant.

    Returns value between 0.0 and 1.0.
    """
    top_k = retrieved_titles[:k]
    if not top_k:
        return 0.0

    expected_lower = {t.lower() for t in expected_titles}
    relevant = sum(1 for t in top_k if t.lower() in expected_lower)
    return relevant / len(top_k)


def recall_at_k(
    retrieved_titles: list[str], expected_titles: list[str], k: int = 5
) -> float:
    """Fraction of expected courses that appear in top-K results.

    Returns value between 0.0 and 1.0.
    """
    if not expected_titles:
        return 1.0

    top_k_lower = {t.lower() for t in retrieved_titles[:k]}
    found = sum(1 for t in expected_titles if t.lower() in top_k_lower)
    return found / len(expected_titles)


def filter_satisfaction(
    courses: list[dict],
    filter_check: dict,
) -> float:
    """Fraction of returned courses that satisfy ALL filter constraints.

    Args:
        courses: List of course dicts with level, rating, organization, etc.
        filter_check: Dict of field->expected_value constraints.
            - level: exact match (e.g. "Beginner level")
            - min_rating: courses must have rating >= this value
            - organization: substring match (case-insensitive)

    Returns 1.0 if all courses pass, 0.0 if none pass.
    """
    if not courses:
        return 0.0

    satisfied = 0
    for course in courses:
        passes = True

        if "level" in filter_check:
            expected_level = filter_check["level"].lower()
            actual_level = (course.get("level") or "").lower()
            if expected_level not in actual_level:
                passes = False

        if "min_rating" in filter_check:
            rating = course.get("rating")
            if rating is None or rating < filter_check["min_rating"]:
                passes = False

        if "organization" in filter_check:
            expected_org = filter_check["organization"].lower()
            actual_org = (course.get("organization") or "").lower()
            if expected_org not in actual_org:
                passes = False

        if passes:
            satisfied += 1

    return satisfied / len(courses)


def filter_param_accuracy(
    actual_args: dict,
    expected_params: dict,
) -> dict:
    """Check if the LLM extracted filter parameters correctly.

    Returns dict with per-param match results and overall accuracy.
    """
    if not expected_params:
        return {"accuracy": 1.0, "details": {}}

    matches = {}
    for param, expected_value in expected_params.items():
        actual_value = actual_args.get(
            param, "" if isinstance(expected_value, str) else 0.0
        )

        if param == "min_rating":
            matches[param] = (
                abs(float(actual_value or 0) - float(expected_value)) < 0.01
            )
        elif param == "level" or param == "organization":
            matches[param] = expected_value.lower() in str(actual_value).lower()
        else:
            matches[param] = str(actual_value).lower() == str(expected_value).lower()

    correct = sum(1 for v in matches.values() if v)
    return {
        "accuracy": correct / len(matches) if matches else 1.0,
        "details": matches,
    }
