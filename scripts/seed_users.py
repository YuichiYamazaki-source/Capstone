"""Seed test users into MongoDB for multi-agent evaluation.

Usage (from project root):
    python scripts/seed_users.py
    python scripts/seed_users.py --mongo-uri mongodb://localhost:27017
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv("local/.env")

TEST_USERS = [
    {
        "name": "Alice",
        "email": "alice@test.com",
        "profile": {
            "skills": ["Python", "SQL", "Statistics", "Pandas"],
            "motivation": "Transition from data analyst to ML engineer",
            "learning_scope": "Full-time learner",
            "learning_style": "Project-based",
            "interest_areas": ["Machine Learning", "Deep Learning", "MLOps"],
        },
    },
    {
        "name": "Bob",
        "email": "bob@test.com",
        "profile": {
            "skills": ["JavaScript", "React", "Node.js", "HTML/CSS"],
            "motivation": "Become a full-stack developer with cloud skills",
            "learning_scope": "Part-time (evenings)",
            "learning_style": "Video lectures + exercises",
            "interest_areas": ["Cloud Computing", "DevOps", "Backend Development"],
        },
    },
    {
        "name": "Carol",
        "email": "carol@test.com",
        "profile": {
            "skills": ["Excel", "PowerPoint", "Basic SQL"],
            "motivation": "Career change from business analyst to data analytics",
            "learning_scope": "Weekend learner",
            "learning_style": "Guided courses with certificates",
            "interest_areas": ["Data Analytics", "Data Visualization", "Python"],
        },
    },
]


def seed(mongo_uri: str, db_name: str):
    """Seed test users into MongoDB.

    Args:
        mongo_uri: MongoDB connection URI.
        db_name: Target database name.
    """
    from pymongo import MongoClient

    client = MongoClient(mongo_uri)
    db = client[db_name]

    for user in TEST_USERS:
        result = db.users.update_one(
            {"email": user["email"]},
            {"$set": user},
            upsert=True,
        )
        action = "updated" if result.matched_count else "created"
        doc = db.users.find_one({"email": user["email"]})
        print(f"  {action} {user['name']} (id={doc['_id']})")

    client.close()
    print(f"\nSeeded {len(TEST_USERS)} test users.")


def main():
    """CLI entry point for seeding test users."""
    parser = argparse.ArgumentParser(description="Seed test users")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017")
    parser.add_argument("--mongo-db", default="course_finder")
    args = parser.parse_args()

    seed(args.mongo_uri, args.mongo_db)


if __name__ == "__main__":
    main()
