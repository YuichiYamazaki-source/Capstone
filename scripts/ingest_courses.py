"""Ingest courses from Coursera CSV into MongoDB.

Usage:
    python scripts/ingest_courses.py [--sample N] [--all] [--stratified]

Default: ingest 100 random courses.
Use --stratified for proportional sampling by Level x Domain.
"""

import argparse
import ast
import csv
import logging
import math
import random
import sys
from collections import defaultdict

from pymongo import MongoClient

# Structured logging for CLI scripts
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ingest")


CSV_PATH = "data/coursera_course_2024.csv"
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "course_finder"
COLLECTION = "courses"


def parse_skills(raw: str) -> list[str]:
    """Parse skills from CSV string representation of Python list."""
    if not raw or raw.strip() == "[]":
        return []
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, list):
            return [str(s).strip() for s in parsed if s]
        return []
    except (ValueError, SyntaxError):
        return []


def parse_rating(raw: str) -> float | None:
    """Convert rating string to float, handling placeholder values."""
    if not raw or raw == "Rating not found" or raw == "nan":
        return None
    try:
        val = float(raw)
        if math.isnan(val):
            return None
        return val
    except (ValueError, TypeError):
        return None


def parse_num_reviews(raw: str) -> int | None:
    """Convert num_reviews to int."""
    if not raw or raw == "nan":
        return None
    try:
        val = float(raw)
        if math.isnan(val):
            return None
        return int(val)
    except (ValueError, TypeError):
        return None


def parse_enrolled(raw: str) -> str | None:
    """Clean enrolled field."""
    if not raw or raw == "Enrollment number not found":
        return None
    return raw.strip()


def parse_satisfaction(raw: str) -> str | None:
    """Clean satisfaction rate field."""
    if not raw or raw == "nan":
        return None
    return raw.strip()


SKILL_DOMAINS = {
    "Programming & Dev": {
        "python",
        "programming",
        "javascript",
        "java",
        "c++",
        "c programming",
        "react",
        "angular",
        "node",
        "web development",
        "html",
        "css",
        "software development",
        "software engineering",
        "object-oriented",
        "git",
        "github",
        "coding",
        "django",
        "mongodb",
        "mysql",
        "algorithm",
        "data structure",
        "computer science",
        "web application",
        "software architecture",
        "mobile development",
        "php",
        "full stack",
        "android",
        "spring",
        "computer architecture",
        "shell script",
        "bash",
        "json",
        "computer language",
        "computer software",
        "debugging",
        "software testing",
        "agile",
        "prototyping",
        "api",
        "microservices",
    },
    "Data & Analytics": {
        "data analysis",
        "data visualization",
        "sql",
        "statistics",
        "excel",
        "tableau",
        "power bi",
        "r programming",
        "rstudio",
        "big data",
        "data management",
        "data science",
        "analytics",
        "exploratory data",
        "data cleansing",
        "data collection",
        "data warehousing",
        "data modeling",
        "etl",
        "hadoop",
        "spark",
        "pandas",
        "spreadsheet",
        "regression",
        "hypothesis testing",
        "probability",
        "predictive",
        "business intelligence",
        "database",
        "matlab",
        "data mining",
        "data pipeline",
        "pivot table",
        "forecasting",
        "time series",
        "data quality",
        "querying",
        "bayesian",
        "scikit-learn",
        "scipy",
    },
    "AI & ML": {
        "machine learning",
        "deep learning",
        "generative ai",
        "artificial intelligence",
        "neural network",
        "nlp",
        "natural language",
        "computer vision",
        "tensorflow",
        "pytorch",
        "chatgpt",
        "prompt engineering",
        "llm",
        "large language",
        "reinforcement learning",
        "supervised learning",
        "keras",
        "image classification",
        "transformer",
        "sentiment analysis",
        "anomaly detection",
        "chatbot",
        "responsible ai",
        "vertex ai",
    },
    "Cloud & Infra": {
        "cloud computing",
        "aws",
        "azure",
        "gcp",
        "google cloud",
        "docker",
        "kubernetes",
        "devops",
        "linux",
        "operating system",
        "network",
        "automation",
        "iot",
        "internet of things",
        "blockchain",
        "cloud storage",
        "cloud architecture",
        "ci/cd",
        "virtualization",
        "container",
        "cloud application",
        "cloud platform",
        "information technology",
        "system administration",
    },
    "Cybersecurity": {
        "cybersecurity",
        "security",
        "encryption",
        "cryptography",
        "incident management",
        "threat",
        "vulnerability",
        "infosec",
        "ethical hacking",
        "penetration test",
        "privacy",
        "compliance",
        "authentication",
        "governance",
    },
    "Business & Management": {
        "project management",
        "leadership",
        "management",
        "strategy",
        "entrepreneurship",
        "decision-making",
        "innovation",
        "planning",
        "strategic",
        "change management",
        "stakeholder",
        "six sigma",
        "supply chain",
        "product management",
        "human resources",
        "organizational",
        "business process",
        "logistics",
        "business analysis",
        "scrum",
        "kanban",
        "budget",
        "procurement",
        "risk assessment",
        "quality improvement",
    },
    "Marketing & Communication": {
        "marketing",
        "communication",
        "social media",
        "branding",
        "content creation",
        "storytelling",
        "sales",
        "digital marketing",
        "seo",
        "brand",
        "presentation",
        "writing",
        "public relation",
        "negotiation",
        "e-commerce",
        "customer",
        "advertising",
    },
    "Health & Life Sciences": {
        "health",
        "biology",
        "nutrition",
        "healthcare",
        "medical",
        "clinical",
        "bioinformatics",
        "public health",
        "anatomy",
        "disease",
        "epidemiology",
        "medicine",
        "nursing",
        "pharmacology",
        "neuroscience",
        "genetics",
        "patient",
    },
    "Arts & Humanities": {
        "music",
        "art",
        "philosophy",
        "history",
        "psychology",
        "education",
        "teaching",
        "english",
        "grammar",
        "literature",
        "graphic design",
        "design thinking",
        "photography",
        "film",
        "user experience",
        "user interface",
        "ux research",
        "instructional design",
        "game design",
    },
    "Science & Engineering": {
        "physics",
        "engineering",
        "renewable energy",
        "thermodynamics",
        "circuit",
        "semiconductor",
        "energy",
        "climate",
        "ecology",
        "sustainability",
        "robotics",
        "quantum",
        "chemistry",
        "astronomy",
        "materials",
        "computer-aided design",
    },
}


def classify_domain(skills_str: str) -> str:
    """Classify a course into a domain based on its skills."""
    try:
        parsed = ast.literal_eval(skills_str)
        if not isinstance(parsed, list) or len(parsed) == 0:
            return "No Skills"
    except (ValueError, SyntaxError):
        return "No Skills"

    domain_hits: dict[str, int] = {}
    for skill in parsed:
        s = skill.strip().lower()
        for domain, keywords in SKILL_DOMAINS.items():
            if any(kw in s for kw in keywords):
                domain_hits[domain] = domain_hits.get(domain, 0) + 1
                break

    if not domain_hits:
        return "Other"
    return max(domain_hits, key=domain_hits.get)


def stratified_sample(rows: list[dict], sample_size: int) -> list[dict]:
    """Stratified sampling by Level x Domain, preserving original proportions.

    Deduplicates by title to prevent duplicate courses.
    """
    # Deduplicate by title first
    seen_titles: set[str] = set()
    unique_rows: list[dict] = []
    for row in rows:
        title = row.get("title", "").strip()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_rows.append(row)

    logger.info("Deduplicated: %d -> %d unique rows", len(rows), len(unique_rows))

    # Group by Level x Domain
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in unique_rows:
        level = row.get("Level", "").strip() or "Unknown"
        domain = classify_domain(row.get("Skills", "[]"))
        groups[(level, domain)].append(row)

    total = len(unique_rows)
    sample_size = min(sample_size, total)

    # Allocate proportionally
    sampled: list[dict] = []
    group_keys = sorted(groups.keys())

    allocations: list[tuple[tuple[str, str], int]] = []
    for key in group_keys:
        proportion = len(groups[key]) / total
        alloc = int(sample_size * proportion)
        allocations.append((key, alloc))

    # Distribute rounding remainder
    allocated_so_far = sum(a for _, a in allocations)
    remainder = sample_size - allocated_so_far
    # Give remainder to the largest groups first
    sorted_by_size = sorted(
        range(len(allocations)),
        key=lambda i: len(groups[allocations[i][0]]),
        reverse=True,
    )
    for i in range(remainder):
        key, alloc = allocations[sorted_by_size[i]]
        allocations[sorted_by_size[i]] = (key, alloc + 1)

    # Sample from each group
    sampled_titles: set[str] = set()
    for key, alloc in allocations:
        group = groups[key]
        actual = min(alloc, len(group))
        picked = random.sample(group, actual)
        for row in picked:
            title = row.get("title", "").strip()
            if title not in sampled_titles:
                sampled_titles.add(title)
                sampled.append(row)

    # Log distribution
    level_counts: dict[str, int] = defaultdict(int)
    domain_counts: dict[str, int] = defaultdict(int)
    for key, alloc in allocations:
        level, domain = key
        actual = min(alloc, len(groups[key]))
        level_counts[level] += actual
        domain_counts[domain] += actual

    logger.info("Stratified sample: %d courses", len(sampled))
    logger.info("  Level distribution: %s", dict(level_counts))
    logger.info("  Domain distribution: %s", dict(domain_counts))

    return sampled


def csv_row_to_doc(row: dict) -> dict:
    """Convert a CSV row to a MongoDB document."""
    skills = parse_skills(row.get("Skills", ""))

    return {
        "title": row.get("title", "").strip(),
        "description": row.get("Description", "").strip(),
        "organization": row.get("Organization", "").strip(),
        "instructor": row.get("Instructor", "").strip(),
        "level": row.get("Level", "").strip() or "Unknown",
        "rating": parse_rating(row.get("rating", "")),
        "num_reviews": parse_num_reviews(row.get("num_reviews", "")),
        "enrolled": parse_enrolled(row.get("enrolled", "")),
        "skills": skills,
        "skills_lower": [s.lower() for s in skills],
        "modules": row.get("Modules/Courses", "").strip(),
        "schedule": row.get("Schedule", "").strip() or None,
        "url": row.get("URL", "").strip(),
        "satisfaction_rate": parse_satisfaction(row.get("Satisfaction Rate", "")),
    }


def main():
    """CLI entry point for ingesting courses from CSV to MongoDB."""
    parser = argparse.ArgumentParser(description="Ingest Coursera CSV into MongoDB")
    parser.add_argument(
        "--sample",
        type=int,
        default=100,
        help="Number of courses to ingest (default: 100)",
    )
    parser.add_argument("--all", action="store_true", help="Ingest all courses")
    parser.add_argument(
        "--stratified",
        action="store_true",
        help="Use stratified sampling by Level x Domain",
    )
    parser.add_argument("--mongo-uri", default=MONGO_URI, help="MongoDB URI")
    parser.add_argument("--mongo-db", default=MONGO_DB, help="MongoDB database name")
    parser.add_argument("--csv", default=CSV_PATH, help="Path to CSV file")
    args = parser.parse_args()

    # Read CSV
    logger.info("Reading CSV: %s", args.csv)
    with open(args.csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    logger.info("CSV loaded: %d total rows", len(rows))

    # Sample if not --all
    if not args.all:
        if args.stratified:
            rows = stratified_sample(rows, args.sample)
        else:
            sample_size = min(args.sample, len(rows))
            rows = random.sample(rows, sample_size)
            logger.info("Random sampled %d courses", sample_size)

    # Convert to MongoDB documents (deduplicate by title)
    docs = []
    seen_titles: set[str] = set()
    for row in rows:
        doc = csv_row_to_doc(row)
        if doc["title"] and doc["title"] not in seen_titles:
            seen_titles.add(doc["title"])
            docs.append(doc)

    logger.info("Prepared %d documents", len(docs))

    # Connect to MongoDB
    client = MongoClient(args.mongo_uri)
    db = client[args.mongo_db]
    collection = db[COLLECTION]

    # Clear existing courses
    deleted = collection.delete_many({})
    logger.info("Cleared %d existing courses", deleted.deleted_count)

    # Insert
    if docs:
        result = collection.insert_many(docs)
        logger.info(
            "Inserted %d courses into %s.%s",
            len(result.inserted_ids),
            args.mongo_db,
            COLLECTION,
        )

    # Verify
    count = collection.count_documents({})
    levels = collection.distinct("level")
    orgs = collection.distinct("organization")
    skills = collection.distinct("skills")
    logger.info(
        "Ingestion complete: %d courses, %d orgs, %d skills",
        count,
        len(orgs),
        len(skills),
    )
    logger.info("Levels: %s", levels)

    client.close()


if __name__ == "__main__":
    main()
