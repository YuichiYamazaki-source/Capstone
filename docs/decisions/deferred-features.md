# ADR: Deferred Features

Features listed in Requirement 2 (Advanced) that were intentionally **not implemented** in the current PoC, with rationale for each decision.

## Multi-Modal Query (voice, uploaded docs)

**Decision**: Defer

Ground truth datasets for voice and document inputs are difficult to prepare at this stage. The evaluation framework (DeepEval, IR metrics) is built around text-based queries. Introducing multimodal inputs without a reliable evaluation methodology would make it impossible to measure quality. Text-based query evaluation must be established first before extending to other modalities.

## Token Optimization

**Decision**: Not required as a separate initiative

The system already uses **gpt-4o-mini** as the default model, which provides a strong cost-performance ratio. Explicit token reduction techniques (prompt compression, context truncation) would add complexity with marginal cost savings on an already cost-efficient model. The architecture also uses **local models** (fastembed) for embedding and reranking, avoiding LLM token costs entirely for those operations.

## Learning Analytics (popular courses, completion trends)

**Decision**: Defer

This feature requires accumulated user interaction data (course enrollments, completions, ratings) to produce meaningful analytics. In the current PoC stage, there is insufficient user data to derive statistically significant trends. External market trends are partially addressed through the **web_search** tool used by Career Advisor and Skill Gap agents, but internal analytics require production-scale user activity.

## Adaptive Difficulty Adjustment

**Decision**: Defer

Adaptive difficulty requires a history of completed courses per user to infer appropriate next-level recommendations. The PoC has no course completion tracking — users have a static skill profile but no learning progress timeline. The current approach uses **profile-based filtering** (skill level, interests) as a practical alternative. True adaptive adjustment is a production-phase feature dependent on user activity data accumulation.

## Agent-to-Agent (A2A) Communication

**Decision**: Not needed at current scale

The multi-agent system runs within a single AI service process, using **OpenAI Agents SDK handoff** for inter-agent communication. This is sufficient for the current architecture where all agents share the same runtime. A2A protocol (Google's inter-service agent communication standard) becomes relevant when agents are deployed as **separate microservices** across distributed infrastructure — a production-scale concern, not a PoC requirement.

## Skill Graph Mapping

**Decision**: Defer — insufficient data

Building a course dependency graph requires prerequisite relationship data between courses. The Coursera dataset does **not include prerequisite fields**, so relationships would need to be inferred by LLM — introducing both cost and accuracy concerns. The Learning Path agent already provides **level-ordered sequencing** (Beginner → Intermediate → Advanced) as a practical alternative. A full skill graph would be justified only with a dataset that includes explicit prerequisite metadata.
