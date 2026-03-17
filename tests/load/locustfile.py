"""Load tests for the Intelligent University Course Finder.

Usage:
    locust -f tests/load/locustfile.py --headless \
        -u 10 -r 2 -t 60s --host http://localhost:8000

Scenarios:
  - ChatUser: Sends varied chat queries to /api/v1/chat
  - SearchUser: Tests course search with filters
  - AnalyzeUser: Tests full analysis endpoint
"""

import random

from locust import HttpUser, between, task

# Sample queries for realistic load patterns
CHAT_QUERIES = [
    "I want to learn Python programming",
    "What courses are available for machine learning beginners?",
    "Show me advanced data science courses",
    "I need courses about cloud computing on AWS",
    "Recommend cybersecurity courses with high ratings",
    "What are the best courses for React development?",
    "Find me intermediate level business analytics courses",
    "I want to transition from backend to full-stack development",
    "Show courses about artificial intelligence from Coursera",
    "What should I learn for a career in data engineering?",
]

SKILL_GAP_QUERIES = [
    "I know Python and SQL, what skills do I need for data science?",
    "I'm a frontend developer wanting to learn DevOps, what's missing?",
    "What skills gap do I have for a machine learning engineer role?",
]

CAREER_QUERIES = [
    "What career paths can I pursue with Python and data analysis skills?",
    "How do I become a cloud architect?",
    "What's the job market like for AI engineers?",
]

LEARNING_PATH_QUERIES = [
    "Create a learning path for becoming a full-stack developer",
    "Design a 3-month plan to learn data science from scratch",
    "What's the best sequence of courses for cybersecurity?",
]


class ChatUser(HttpUser):
    """Simulates users chatting with the Learning Advisor."""

    weight = 5
    wait_time = between(2, 5)

    @task(3)
    def chat_general(self):
        """Send a general course search query."""
        query = random.choice(CHAT_QUERIES)
        self.client.post(
            "/api/v1/chat",
            json={"message": query},
            timeout=120,
            name="/api/v1/chat [general]",
        )

    @task(1)
    def chat_skill_gap(self):
        """Send a skill gap analysis query."""
        query = random.choice(SKILL_GAP_QUERIES)
        self.client.post(
            "/api/v1/chat",
            json={"message": query},
            timeout=120,
            name="/api/v1/chat [skill-gap]",
        )

    @task(1)
    def chat_career(self):
        """Send a career advice query."""
        query = random.choice(CAREER_QUERIES)
        self.client.post(
            "/api/v1/chat",
            json={"message": query},
            timeout=120,
            name="/api/v1/chat [career]",
        )


class AnalyzeUser(HttpUser):
    """Simulates users running full analysis."""

    weight = 1
    wait_time = between(5, 10)

    @task
    def analyze_learning_path(self):
        """Request a learning path analysis."""
        query = random.choice(LEARNING_PATH_QUERIES)
        self.client.post(
            "/api/v1/chat",
            json={"message": query},
            timeout=180,
            name="/api/v1/chat [learning-path]",
        )
