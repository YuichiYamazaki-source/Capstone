"""Visualize Qdrant course embeddings with t-SNE + Plotly (standalone).

Usage:
    conda activate base
    python scripts/visualize_embeddings.py

Exports all dense vectors from Qdrant, reduces to 2D with t-SNE,
and creates interactive HTML visualizations colored by different axes.

Output:
    docs/evaluation/embedding_by_level.html
    docs/evaluation/embedding_by_organization.html
    docs/evaluation/embedding_by_topic.html
"""

import logging
import re
import sys
from collections import Counter

import numpy as np
import pandas as pd
import plotly.express as px
from qdrant_client import QdrantClient
from sklearn.manifold import TSNE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("visualize_embeddings")

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION = "courses"
OUTPUT_DIR = "docs/evaluation"


def export_qdrant_vectors() -> tuple[list, list[dict]]:
    """Scroll all points from Qdrant with dense vectors."""
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    info = client.get_collection(QDRANT_COLLECTION)
    logger.info("Collection '%s': %d points", QDRANT_COLLECTION, info.points_count)

    vectors = []
    payloads = []
    offset = None

    while True:
        results, next_offset = client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=100,
            offset=offset,
            with_vectors=["dense"],
            with_payload=True,
        )
        for point in results:
            vec = point.vector.get("dense", [])
            if vec:
                vectors.append(vec)
                payloads.append(point.payload)
        logger.info("Exported %d vectors", len(vectors))
        if next_offset is None:
            break
        offset = next_offset

    return vectors, payloads


def extract_topic(title: str) -> str:
    """Extract a broad topic category from course title using keywords."""
    title_lower = title.lower()

    topic_keywords = {
        "Machine Learning / AI": [
            "machine learning", "deep learning", "neural network",
            "artificial intelligence", " ai ", "reinforcement learning",
            "nlp", "natural language", "computer vision", "tensorflow",
            "pytorch", "generative ai",
        ],
        "Data Science": [
            "data science", "data analysis", "data analytics",
            "big data", "data engineering", "data visualization",
            "pandas", "statistics", "r programming",
        ],
        "Python": [
            "python",
        ],
        "Web Development": [
            "web development", "javascript", "react", "angular",
            "node.js", "html", "css", "full stack", "frontend",
            "backend", "django", "flask",
        ],
        "Cloud / DevOps": [
            "cloud", "aws", "azure", "gcp", "google cloud",
            "devops", "kubernetes", "docker", "terraform",
            "microservice",
        ],
        "Cybersecurity": [
            "security", "cybersecurity", "ethical hacking",
            "penetration", "cryptography",
        ],
        "Business / Management": [
            "business", "management", "leadership", "project management",
            "agile", "scrum", "marketing", "finance", "entrepreneurship",
        ],
        "Database / SQL": [
            "database", "sql", "mongodb", "nosql", "postgresql",
        ],
        "Mobile Development": [
            "android", "ios", "mobile", "swift", "kotlin", "flutter",
        ],
    }

    for topic, keywords in topic_keywords.items():
        for kw in keywords:
            if kw in title_lower:
                return topic

    return "Other"


def classify_primary_skill(skills: list[str], top_skills: set[str]) -> str:
    """Assign the first matching top skill, or 'Other'."""
    for s in skills:
        if s in top_skills:
            return s
    return "Other"


def build_dataframe(coords: np.ndarray, payloads: list[dict]) -> pd.DataFrame:
    """Build DataFrame with t-SNE coordinates and metadata."""
    # Extract topics
    titles = [p.get("title", "") for p in payloads]
    topics = [extract_topic(t) for t in titles]

    # Consolidate organizations (keep top N, rest as "Other")
    orgs = [p.get("organization", "Unknown") for p in payloads]
    org_counts = Counter(orgs)
    top_orgs = {org for org, count in org_counts.most_common(15)}
    orgs_grouped = [o if o in top_orgs else "Other" for o in orgs]

    # Primary skill: assign each course its first top-15 skill
    all_skills_flat = []
    skills_per_course = []
    for p in payloads:
        s = p.get("skills", [])
        skills_per_course.append(s)
        all_skills_flat.extend(s)
    skill_counts = Counter(all_skills_flat)
    top_skills = {s for s, _ in skill_counts.most_common(15)}
    primary_skills = [
        classify_primary_skill(s, top_skills) for s in skills_per_course
    ]

    return pd.DataFrame(
        {
            "x": coords[:, 0],
            "y": coords[:, 1],
            "title": titles,
            "level": [p.get("level", "Unknown") for p in payloads],
            "organization": orgs_grouped,
            "organization_raw": orgs,
            "rating": [p.get("rating") for p in payloads],
            "skills": [", ".join(p.get("skills", [])[:5]) for p in payloads],
            "topic": topics,
            "primary_skill": primary_skills,
        }
    )


def create_visualizations(df: pd.DataFrame) -> None:
    """Generate three HTML visualizations colored by different axes."""

    hover_cols = ["title", "organization_raw", "level", "rating", "skills", "topic"]
    common_layout = dict(width=1200, height=800)
    tsne_labels = {"x": "t-SNE 1", "y": "t-SNE 2"}

    # 1. By Level
    fig_level = px.scatter(
        df, x="x", y="y", color="level",
        hover_data=hover_cols,
        title="Embedding Space — colored by Level (t-SNE, 1000 courses)",
        labels=tsne_labels,
        color_discrete_map={
            "Beginner level": "#4CAF50",
            "Intermediate level": "#FF9800",
            "Advanced level": "#F44336",
            "Mixed level": "#9C27B0",
            "Unknown": "#9E9E9E",
        },
    )
    fig_level.update_layout(**common_layout)
    path_level = f"{OUTPUT_DIR}/embedding_by_level.html"
    fig_level.write_html(path_level)
    logger.info("Saved: %s", path_level)

    # 2. By Organization (top 15)
    fig_org = px.scatter(
        df, x="x", y="y", color="organization",
        hover_data=hover_cols,
        title="Embedding Space — colored by Organization (t-SNE, 1000 courses)",
        labels=tsne_labels,
    )
    fig_org.update_layout(**common_layout)
    path_org = f"{OUTPUT_DIR}/embedding_by_organization.html"
    fig_org.write_html(path_org)
    logger.info("Saved: %s", path_org)

    # 3. By Primary Skill (top 15)
    fig_skill = px.scatter(
        df, x="x", y="y", color="primary_skill",
        hover_data=hover_cols,
        title="Embedding Space — colored by Primary Skill (t-SNE, 1000 courses)",
        labels=tsne_labels,
    )
    fig_skill.update_layout(**common_layout)
    path_skill = f"{OUTPUT_DIR}/embedding_by_skill.html"
    fig_skill.write_html(path_skill)
    logger.info("Saved: %s", path_skill)

    # 4. By Topic
    fig_topic = px.scatter(
        df, x="x", y="y", color="topic",
        hover_data=hover_cols,
        title="Embedding Space — colored by Topic (t-SNE, 1000 courses)",
        labels=tsne_labels,
    )
    fig_topic.update_layout(**common_layout)
    path_topic = f"{OUTPUT_DIR}/embedding_by_topic.html"
    fig_topic.write_html(path_topic)
    logger.info("Saved: %s", path_topic)


def main():
    """Export Qdrant vectors and visualize with t-SNE."""
    vectors, payloads = export_qdrant_vectors()
    if not vectors:
        logger.error("No vectors found in Qdrant")
        return

    arr = np.array(vectors)
    logger.info("Running t-SNE on %d vectors (%d-dim)...", arr.shape[0], arr.shape[1])

    reducer = TSNE(n_components=2, random_state=42, perplexity=30, max_iter=1000)
    coords = reducer.fit_transform(arr)

    df = build_dataframe(coords, payloads)

    # Print distribution stats
    logger.info("Level distribution:\n%s", df["level"].value_counts().to_string())
    logger.info("Topic distribution:\n%s", df["topic"].value_counts().to_string())
    logger.info("Top 10 orgs:\n%s", df["organization"].value_counts().head(10).to_string())
    logger.info("Primary skill distribution:\n%s", df["primary_skill"].value_counts().to_string())

    create_visualizations(df)
    logger.info("Done! Open files in %s/", OUTPUT_DIR)


if __name__ == "__main__":
    main()
