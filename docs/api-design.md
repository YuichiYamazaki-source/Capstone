# API Design

## Base URL

- **PoC**: `http://localhost:8000/api/v1`
- **Production**: `https://{domain}/api/v1`

All endpoints below are prefixed with `/api/v1` via the Gateway.

## Authentication

Protected endpoints require `Authorization: Bearer <JWT>` header.
JWT is issued by User Service on login/register and forwarded by Gateway as `x-user-id` header to downstream services.

---

## Frontend → Gateway (Vite Proxy)

The React frontend uses Axios with `baseURL: /api/v1`. Vite dev server proxies `/api/*` to `http://gateway:8000`.

### Frontend API Modules

| Module | File | Endpoints Used |
|--------|------|----------------|
| Auth | `features/auth/api.js` | `POST /auth/register`, `POST /auth/login` |
| Courses | `features/courses/api.js` | `GET /courses`, `GET /courses/search`, `GET /filters/options` |
| Profile | `features/profile/api.js` | `GET /users/profile`, `PUT /users/profile` |
| Chat | `Explore.jsx` (direct) | `POST /chat` |
| Analysis | `Analysis.jsx` (direct) | `GET /analyze/results/{user_id}`, `POST /analyze/*` |

### Frontend Key Behaviors

- JWT stored in `localStorage`, auto-injected by Axios interceptor
- 401 response → auto-redirect to `/login` (except auth endpoints)
- Chat: sends `message`, `history` (max 20), `user_id`, `conversation_id`
- Analysis: loads saved results on mount, runs individual analyses on demand

---

## Gateway Endpoints

The Gateway proxies all requests to downstream services. No business logic.

### AI Endpoints → AI Service (:8003)

| Method | Path | Auth | Timeout | Description |
|--------|------|:----:|--------:|-------------|
| POST | `/chat` | JWT | 180s | Chat with Learning Advisor agent |
| POST | `/analyze` | JWT | 180s | Run all 3 analyses in parallel |
| POST | `/analyze/skill-gap` | JWT | 120s | Skill gap analysis only |
| POST | `/analyze/career` | JWT | 120s | Career path analysis only |
| POST | `/analyze/learning-path` | JWT | 120s | Learning path design only |
| GET | `/analyze/results/{user_id}` | JWT | 10s | Retrieve saved analysis results |

### Course Endpoints → Course Service (:8001)

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/courses` | Optional | List courses with filters and pagination |
| GET | `/courses/search` | Optional | Text search on courses |
| GET | `/courses/{course_id}` | Optional | Get single course by ObjectId |
| GET | `/filters/skills` | Optional | Search skills by prefix (ranked by frequency) |
| GET | `/filters/options` | Optional | Available filter values (levels, orgs, skills) |

### User Endpoints → User Service (:8002)

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| POST | `/auth/register` | No | Register new user, returns JWT |
| POST | `/auth/login` | No | Login, returns JWT |
| GET | `/users/profile` | JWT | Get authenticated user profile |
| PUT | `/users/profile` | JWT | Update user profile (partial) |

### Health Check

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/health` | No | Gateway health status |

---

## AI Service Endpoints

### POST /chat

Process a message through the Learning Advisor agent pipeline.

Request:
```json
{
  "message": "I want to learn ML for healthcare",
  "user_id": "507f1f77bcf86cd799439011",
  "conversation_id": "optional-session-id",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

| Field | Type | Required | Constraints |
|-------|------|:--------:|-------------|
| `message` | string | Yes | 1-2000 chars |
| `user_id` | string | No | Valid MongoDB ObjectId |
| `conversation_id` | string | No | Session tracking |
| `history` | HistoryMessage[] | No | Max 20 messages |

Response:
```json
{
  "reply": "Based on your background in...",
  "conversation_id": "...",
  "agent": "Learning Advisor",
  "tool_calls": ["retrieve_courses"],
  "retrieval_tool_calls": ["retrieve_courses"],
  "retrieval_args": {"query": "ML healthcare", "level": "Beginner"},
  "all_tool_calls": ["get_user_profile", "retrieve_courses"],
  "latency_ms": 3200.5,
  "courses": [{"title": "...", "url": "...", ...}]
}
```

### POST /analyze

Run all 3 sub-agents (Skill Gap, Career, Learning Path) in parallel.

Request:
```json
{
  "user_id": "507f1f77bcf86cd799439011"
}
```

Response (`AnalyzeResponse`):
```json
{
  "skill_gap": {"result": {...}, "evidence": "...", "latency_ms": 5200},
  "career": {"result": {...}, "evidence": "...", "latency_ms": 4800},
  "learning_path": {"result": {...}, "evidence": "...", "latency_ms": 6100}
}
```

### POST /analyze/skill-gap, /analyze/career, /analyze/learning-path

Run a single analysis agent.

Request: same as `/analyze`

Response (`SingleAnalyzeResponse`):
```json
{
  "result": {...},
  "evidence": "Human-readable explanation of the analysis",
  "latency_ms": 5200
}
```

### GET /analyze/results/{user_id}

Retrieve previously saved analysis results.

Response (`SavedAnalysisResponse`):
```json
{
  "skill_gap": {"result": {...}, "evidence": "...", "latency_ms": 0} | null,
  "career": {"result": {...}, "evidence": "...", "latency_ms": 0} | null,
  "learning_path": {"result": {...}, "evidence": "...", "latency_ms": 0} | null
}
```

### GET /health

Response:
```json
{
  "status": "ok | degraded",
  "service": "ai-service",
  "checks": {
    "mongodb": "ok",
    "qdrant": "ok (1 collections)"
  }
}
```

---

## Course Service Endpoints

### GET /courses

Query parameters:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `level` | string | — | Filter by difficulty level |
| `organization` | string | — | Filter by organization |
| `min_rating` | float | — | Minimum rating threshold |
| `skills` | string[] | — | Filter by skills (OR match) |
| `limit` | int | 20 | Results per page (1-100) |
| `offset` | int | 0 | Pagination offset |

Response (`CourseListResponse`):
```json
{
  "courses": [
    {
      "id": "507f1f77bcf86cd799439011",
      "title": "Machine Learning",
      "description": "...",
      "organization": "Stanford University",
      "instructor": "Andrew Ng",
      "level": "Intermediate level",
      "rating": 4.8,
      "num_reviews": 12345,
      "enrolled": "1.2M",
      "skills": ["Python", "TensorFlow"],
      "modules": "...",
      "schedule": "Flexible",
      "url": "https://coursera.org/...",
      "satisfaction_rate": "95%"
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

### GET /courses/search

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `q` | string | required | Search query (min 1 char) |
| `limit` | int | 20 | Results per page (1-100) |
| `offset` | int | 0 | Pagination offset |

Response: same as `GET /courses`

### GET /courses/{course_id}

Path parameter: MongoDB ObjectId. Returns 404 if not found.

### GET /filters/skills

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `q` | string | — | Prefix search |
| `limit` | int | 20 | Max results (1-100) |

Response:
```json
{
  "skills": ["Python Programming", "Python", "PyTorch"]
}
```

### GET /filters/options

Response:
```json
{
  "levels": ["Advanced level", "Beginner level", "Intermediate level"],
  "organizations": ["Google", "Stanford University", "..."],
  "skills": ["Python", "Machine Learning", "..."]
}
```

---

## User Service Endpoints

### POST /auth/register

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe"
}
```

Response (`TokenResponse`):
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### POST /auth/login

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

Response: same as register

### GET /users/profile

Requires `x-user-id` header (set by Gateway from JWT).

Response (`UserResponse`):
```json
{
  "id": "...",
  "email": "user@example.com",
  "name": "John Doe",
  "interests": ["AI", "Web Development"],
  "current_skills": ["Python", "JavaScript"],
  "education_level": "Bachelor",
  "career_goal": "Data Scientist"
}
```

### PUT /users/profile

Partial update of profile fields.

Request:
```json
{
  "interests": ["AI", "Cloud Computing"],
  "career_goal": "ML Engineer"
}
```

Response: updated `UserResponse`

---

## Error Responses

All errors follow a consistent format:
```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad request (invalid parameters) |
| 401 | Unauthorized (missing or invalid JWT) |
| 404 | Resource not found |
| 422 | Validation error (Pydantic) |
| 500 | Internal server error |
| 503 | Service unavailable (DB connection failure, AI service unreachable) |

## Design Principles

1. **RESTful**: Resource-oriented URLs, standard HTTP methods
2. **Stateless**: No server-side session; JWT carries auth state
3. **Pagination**: All list endpoints support limit/offset
4. **Graceful degradation**: AI endpoints fall back to keyword search if vector DB unavailable
5. **Consistent errors**: Uniform error response format across all services
6. **Timeout tiering**: Chat (180s) > Analysis (120s) > CRUD (10s default)
