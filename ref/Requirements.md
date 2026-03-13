# Requirements — Intelligent University Course Finder

**Tags**: #type/reference #domain/rag #domain/agent #domain/evaluation #domain/llmops

## Overview
AI-powered multimodal course discovery and recommendation system that helps students explore university course offerings using natural and flexible inputs.

## Key Capabilities
- Multimodal Query Understanding (text, voice, uploaded docs)
- Semantic Course Retrieval
- Relevance Assistance
- Prerequisite Awareness
- Skill Gap Identification
- Learning Path Recommendations
- Career-Oriented Course Exploration

## Requirement 1 (Basic)
- Basic RAG for course discovery
- Intent-based semantic search
- Simple recommendation agent
- Skill gap identification
- Difficulty level filtering
- Learning objective validation guardrails
- Basic course sequencing
- Metadata filtering (organization, rating, difficulty)
- **Expose via API endpoint**

## Requirement 2 (Advanced)
- DeepEval for recommendation relevance and learning outcomes
- Rerank using learner preference models and success rate data
- LLM-as-judge for course quality and prerequisite validation
- Token optimization for personalized learning path generation
- Performance testing: real-time recommendations at scale
- Content appropriateness and prerequisite guardrails
- **Simple front-end interface**

### Hybrid Course Retrieval
- Hybrid search combining vector embeddings and keyword retrieval
- Dynamic filtering by difficulty level, rating, organization, skill category
- Cross-encoder reranking

### Learning Path Intelligence
- Automated generation of structured multi-course learning paths
- Identification of prerequisite courses
- Skill graph mapping between courses and learning outcomes

### Multi-Agent Learning Recommendation System
- Course Retrieval Agent
- Skill Gap Analysis Agent
- Learning Path Planning Agent
- Career Alignment Agent
- Learning Advisor Agent

### Additional Learning Intelligence
- Learning analytics (popular courses, completion trends)
- Personalized recommendations based on learner preferences
- Adaptive difficulty adjustment
- Agent handoff between learning domains
- Agent-to-Agent (A2A) communication

## Deliverables
1. Architecture Diagram (JPEG/PDF)
2. Design Document (trade-offs, decisions)
3. Full Executable Code (Microservice) + README
4. Panel Presentation (10 min: 8 demo + 2 Q&A)

## Dataset
- **Coursera Course Dataset** (CSV/JSON)
- Fields: course_name, description, skills, difficulty_level, rating, organization
- Sources: Kaggle, HuggingFace, GitHub
