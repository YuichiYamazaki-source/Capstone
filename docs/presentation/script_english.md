# Presentation Script

15 min presentation + 5 min Q&A = 20 min total
Position: PoC complete + PoB partial

---

## Section 1: Opening — Why & Positioning (2-3 min)

### 1-1. Market Opportunity (30 sec)

Hello, everyone.
I'll do a presentation about College Course Finder.
The e-learning market was valued at 200 billion dollars in 2020, and it is projected to grow to 840 billion dollars by 2030. AI adoption and the expansion of remote work are the key drivers behind this growth. However, while the market is expanding, the learning experience itself still has significant challenges.

### 1-2. The Problem — 4 Pain Points (45 sec)
（Read the slide is better）

Let me explain what those challenges look like in practice. For example, when a student thinks "I want to learn machine learning," a beginner would bounce between ChatGPT and multiple resources, searching for the right courses. Figuring out which skills you lack and what knowledge you need — while having no prior knowledge — and then building a study plan and selecting courses is a high barrier for beginners. On the other hand, for advanced learners, spending time on lectures covering material they already know is a waste of time.
To solve these challenges, I built an AI-powered course discovery system.

### 1-3. Positioning — PoC + PoB Declaration (45 sec)

Before I continue, let me share my interpretation of the requirements document and clarify the project's positioning. This project is positioned as "PoC complete, PoB partially implemented."

There are three reasons why we haven't reached full PoB.

First, data quality gaps in the course data. Course descriptions are only a few lines long, and many entries are missing skill descriptions entirely. This makes precise skill-to-course matching difficult.

Second, the ground truth problem. Who defines the "right answer" for a given query? Even as the developer, I can't confidently say which courses are the correct match because the descriptions are too short. Preparing a reliable ground truth dataset is extremely challenging.

Third, there is no real user data. As a solo developer, my sample size is one.

So my strategy was to build the measurement infrastructure first. I set up LangFuse for online tracing and DeepEval as an evaluation harness, so that when real users start using the system — and after they use it — we can immediately start running improvement loops. I believe we need an opportunity to demo this system with real users after the PoC.

Now, let me show you the system in action.

---

## Section 2: Demo (5-6 min)

### 2-1. User Registration & Onboarding (1 min)

For this demo, I'll use the persona of a business professional who wants to learn machine learning.

First, I'll register a new user. I enter a name and email address to create an account. Next, during onboarding, I input my skills, areas of interest, and learning goals. There's room for LLM integration here as well, but for now, users search and select from skills extracted from the dataset. You can also register skills that don't exist in the dataset.

The information entered here becomes the foundation for personalization by the agents. Once registration is complete, the profile accumulates this information.

### 2-2. Chat — Natural Language Course Discovery (1.5 min)

Next is the chat screen. When you type a question in natural language, the Learning Advisor interprets your intent and returns relevant courses.

For example, let me try: "I want to learn machine learning for finance."

As you can see, courses are recommended taking your profile information into account.

Chat is designed for conversational exploration. For deeper analysis, we have individual agents.

### 2-3. Analyze — Individual Agent Execution (1.5 min)

This is the Analysis page. Here you can independently run gap analysis between your current skills and your target skills, get career path suggestions based on your personal information, and generate learning path recommendations.

Let me run the Skill Gap Agent. It analyzes the skills you're currently missing based on your profile information and market data retrieved via web search.

The Career Agent and Learning Path Agent work similarly, each returning structured output. Rather than free-form chat text, results come in an organized format — that's a key feature.

Note that the other features on this page are still at the mockup stage, but I believe there's room to implement them in the future.

Now, let's take a look at what's happening behind the scenes.

### 2-4. LangFuse — Tracing & Cost Visibility (1 min)

Let me open the LangFuse dashboard. The trace from the request we just made is recorded here.

When I expand this trace, you can see which agent called which tool, and the token count, cost, and latency for each step.

The key point is that this wasn't manually instrumented. Through the integration of OpenAI Agents SDK and LangFuse, all LLM calls are automatically traced. The current accuracy may not be perfect, but I believe this is extremely valuable for continuous improvement.

[Metrics (LLM-as-a-Judge) and Prompt Versioning will be explained using the actual screen]

### 2-5. LangFuse — LLM-as-a-Judge & Prompt Versioning (1 min)

Next is evaluation and prompt management. We use a framework called DeepEval for LLM-as-a-Judge evaluation, and scores like Relevancy and Faithfulness are linked to each trace for review.

We also use LangFuse's prompt management feature to version-control our prompts. When a prompt is changed, we can track which version produced which results through the traces.

That covers both the user-facing and operations-facing sides. Now, let me move on to the architecture.

[To be revised based on actual screen]

---

## Section 3: Architecture (5-6 min)

### 3-1. Agent Design — Design Decisions (1.5 min)

Let me start with the overall agent design. This system is composed of 4 LLMs and 5 shared tools, built on the OpenAI Agents SDK.

User queries are first received by the Learning Advisor. The Learning Advisor determines the intent of the query and hands off to the appropriate specialist agent — Skill Gap, Career, or Learning Path — as needed.

One important design decision: the requirements specified a fifth agent called the Course Retrieval Agent, but I implemented it as a tool rather than an agent. The reason is that course retrieval is "search execution," not "reasoning." There's no need to involve an LLM, so implementing it as a tool reduces both cost and latency.

Additionally, the Skill Gap and Career agents are assigned a Web Search tool, enabling them to retrieve real-time market data.

Among these agent components, the part that most significantly affects quality is the RAG layer that handles course retrieval. Let me explain this in detail.

### 3-2. RAG — Indexing Pipeline (1 min)

This is the RAG indexing pipeline. The source data is a CSV of 6,645 Coursera courses. First, we ingest this into MongoDB, and then we generate two types of vectors and store them in Qdrant.

These "two types of vectors" are important, so let me explain.

The first is a Dense Vector — essentially an embedding. We use OpenAI's text-embedding-3-small to generate 1,536-dimensional vectors. The philosophy behind Dense Vectors is "semantic similarity." Text is converted into high-dimensional numerical vectors, and semantically similar content ends up close together in vector space. For example, "machine learning" and "deep learning" are different strings, but in the embedding space, they're placed near each other. The input is the course title and description — capturing "what this course is about" semantically. However, as I mentioned earlier, descriptions are sparse, so the feature representation is somewhat limited.

The second is a BM25 Sparse Vector. This vectorizes the traditional keyword search approach. The philosophy behind BM25 is "word importance." It quantifies how frequently a word appears in a document relative to how rare it is across the entire corpus. Common words get low weight; distinctive words get high weight. It's called "sparse" because only words that actually appear in the document have non-zero values — most of the vector is zeros. The BM25 input includes title, description, and skills. We include skills because specific skill names like "Python" or "TensorFlow" are sometimes not captured well by embeddings alone.

We don't perform chunking. In typical RAG systems, documents are split into chunks, but course descriptions are only a few lines long, so one course equals one document — that's sufficient.

### 3-3. RAG — Query Pipeline & Hybrid Search (1.5 min)

Next, the query-time pipeline. When a user query comes in, it's processed with the same logic as indexing. The query is converted into a 1,536-dimensional Dense Vector via OpenAI Embedding, and simultaneously, a BM25 Sparse Vector is generated.

We then run searches against the two types of vectors created during indexing. Dense Search looks for "semantically similar courses" with a weight of 1.5. BM25 Search looks for "keyword-matching courses" with a weight of 1.2. The two result sets are merged using RRF — Reciprocal Rank Fusion. RRF merges results based on rank position, which allows it to fairly combine two search results that operate on different score scales.

Additionally, Payload Filters for level, min_rating, and organization are applied to both search types.

We've also designed a fallback chain. If Hybrid Search fails, we fall back to BM25-only. If that also fails, we fall back to MongoDB text search. As a last resort, we return an error message.

The reason we chose Qdrant as our vector DB is that it natively supports Hybrid Search, provides Payload Filters, and runs easily in Docker.

### 3-4. Data Analysis — Why Hybrid Search (if time permits) (1 min)

Now, let me explain why we chose the Hybrid Search design, based on data analysis results.

We embedded 1,000 courses and visualized them with t-SNE. This clearly revealed what embeddings can and cannot capture.

What embeddings capture well is topic and subject area. The t-SNE visualization showed clear clusters for data science, business, programming, and so on. What embeddings do not capture is difficulty level, organization, skills, and rating. These showed no separation in the vector space at all. I could have tried including skills in the embedding input, but since I didn't have time to review the actual course content, I wanted to first see how far title plus description alone could take us.

These analysis results determined our design approach. "What the course is about" is handled by Dense Vector semantic search. Specific skill names like "Python" and "TensorFlow" are handled by BM25 keyword search. Level, organization, and rating are handled by Payload Filters.

In other words, Hybrid Search is not an arbitrary choice — it's a design decision grounded in data analysis.

---

## Section 4: Closing — Strong Points & Next (1-2 min)

### 4-1. Strong Points of This Capstone (30 sec)

Finally, let me highlight three strong points of this Capstone.

First, it's an end-to-end working PoC. Hybrid Search, Multi-Agent, and Frontend all work together as an integrated system.

Second, measurement-first design. By building the LangFuse tracing and DeepEval evaluation framework first, we established a foundation for running improvement loops. This makes it much easier to address the items deferred to PoB.

Third, scope discipline. We defined the boundaries between PoC, PoB, and Prd, and documented "what we didn't do and why."

### 4-2. Challenges & Lessons (30 sec)

The biggest challenge is constructing ground truth. We currently have 38 test cases, but these were mechanically generated from database queries — they are not human-validated correct answers. Course descriptions are too short for even the developer to confidently say "this is the right answer."

The lesson I took from this is: build observability and evaluation infrastructure before expanding features. If you can't measure it, you can't improve it.

### 4-3. Next Actions — PoB & Prd Roadmap (30 sec)

Here are the next actions. In the PoB phase, we'll define KPIs, estimate ROI, and build ground truth from real user feedback. We also plan to introduce model routing for cost optimization.

In the Prd phase, we're looking at Azure zero-trust deployment, a learning analytics dashboard, and A2A communication for collaborative filtering.

The PoC has proven technology feasibility. The next step is proving business value.

That concludes my presentation. I'm happy to take your questions.

---

## Appendix: Q&A Preparation

| Question | Key Answer |
|----------|-----------|
| Why both MongoDB and Qdrant? | MongoDB for CRUD, auth, and text fallback. Qdrant for native hybrid search. Separation of concerns. |
| Why no chunking? | Course descriptions are only a few sentences. One course = one document is sufficient. |
| Why was the reranker disabled? | Evaluated with cross-encoder — no quality improvement because course descriptions are too short and similar. Data-driven decision. |
| How do you handle OpenAI outages? | Circuit breaker (3 failures → 30s open), fallback to local MiniLM-L6-v2 (384 dims), then BM25-only, then MongoDB $text. |
| What's the cost per query? | Tracked via LangFuse. (Show actual numbers from dashboard) |
| Why OpenAI Agents SDK over LangChain? | Lightweight, less abstraction overhead, direct control over handoff logic. |
| How did you build ground truth? | DB queries for expected courses + manual routing labels. 38 cases. Limitation acknowledged — needs human validation. |
| Why did IR metrics drop so much from 1K to 6.6K? | Two issues compounding. First, the metric methodology: Precision@K/Recall@K use exact title matching against GT, so relevant courses not in the GT list score as false positives. When the dataset expanded, new relevant courses entered top-K but were absent from GT, causing apparent collapse (Precision@5: 0.61 → 0.16). Second and more fundamental: the GT itself lacks validity — it was constructed from DB queries, not from human judgment of "what's actually a good recommendation." LLM-as-Judge (DeepEval ContextualPrecision/ContextualRecall) would give more accurate measurement, and I should have used it. But even with LLM-as-Judge, if the GT basis is weak, a high score doesn't guarantee good UX. The real validation requires real users evaluating whether the recommendations actually helped them. |
| Why not use DeepEval's ContextualPrecision/ContextualRecall? | Should have — exact title matching is too brittle for course recommendation where multiple courses are valid answers. However, this is only half the problem. Even with LLM-as-Judge, the deeper issue remains: the GT itself was not built from human-validated "correct answers." So better metrics would produce more accurate numbers, but those numbers still wouldn't tell us whether users find the recommendations useful. The full solution is: (1) migrate to LLM-as-Judge for more honest measurement, AND (2) build GT from real user feedback so that metric improvements correlate with actual UX improvement. Both are PoB priorities. |
| RRF weights [BM25=1.2, Dense=1.5] — how were these chosen? | Dense gets slightly higher weight because semantic search better captures user intent for topic discovery. BM25 complements with exact skill name matching. These are empirical initial values, not systematically tuned. Grid search over weight combinations is a PoB optimization task. |
| Why is the DeepEval threshold set to 0.5? | At PoC stage, the threshold serves as a baseline to detect catastrophically bad responses. With incomplete GT, a higher threshold would produce false negatives (good responses marked as failures). The threshold will be raised incrementally as GT quality improves with real user data. |
| Why microservices instead of monolith for a PoC? | The evaluation checklist explicitly requires "Microservices Representation." Additionally, AI Service and Course Service have very different dependency profiles (AI: openai-agents, DeepEval / Course: Motor, pymongo), so separate containers yield faster builds. Gateway routing also reflects production scaling units. |
| Is 7 regex patterns enough for prompt injection? | Regex is the first defense line catching common patterns ("ignore previous instructions"). Topic relevance check (150+ keywords + LLM fallback) serves as the second line. For PoB/Prd, dedicated injection classifiers (Rebuff, Lakera Guard) should be evaluated. |
| What happens when you fall back to local MiniLM (384 dims)? | Quality degrades — dimensionally 1/4 of OpenAI embeddings. But the purpose of fallback is preventing total service outage, not maintaining quality. The fallback chain (Hybrid → BM25-only → MongoDB $text) progressively trades quality for availability. |
| Why all-in on OpenAI? Vendor lock-in risk? | PoC prioritizes ecosystem consistency (Agents SDK + Embedding + LLM). Lock-in risk is acknowledged. HuggingFace embedding fallback is already implemented. PoB Model Routing will introduce multi-vendor support for cost and resilience. |
| How does OpenAI Agents SDK handoff work technically? | `handoff()` terminates the current agent's execution and passes the conversation context to the target agent. The Runner (execution loop) switches to the new agent's prompt and tool set. This is an in-process function call, not HTTP communication between services. |
