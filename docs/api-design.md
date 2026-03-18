# API Design

## Base URL

- **PoC**: `http://localhost:8000/api/v1`
- **Production**: `https://{domain}/api/v1`

## Authentication

All protected endpoints require `Authorization: Bearer <JWT>` header.
JWT is issued by User Service on login/register and validated by Gateway middleware.

## Endpoints

### Course Service (via Gateway)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/courses` | Optional | List courses with filters |
| GET | `/courses/search` | Optional | Search courses by keyword |
| GET | `/courses/{id}` | Optional | Get course by ID |
| GET | `/filters/options` | No | Get available filter values |

#### GET /courses

Query parameters:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `level` | string | — | Filter by difficulty level |
| `organization` | string | — | Filter by organization |
| `min_rating` | float | — | Minimum rating threshold |
| `skills` | string[] | — | Filter by skills (OR match) |
| `limit` | int | 20 | Results per page |
| `offset` | int | 0 | Pagination offset |

Response: `CourseListResponse`
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

#### GET /courses/search

Query parameters:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `q` | string | required | Search query |
| `limit` | int | 20 | Results per page |
| `offset` | int | 0 | Pagination offset |

Response: `CourseListResponse` (same as above)

#### GET /filters/options

Response:
```json
{
  "levels": ["Advanced level", "Beginner level", "Intermediate level"],
  "organizations": ["Google", "Stanford University", "..."],
  "skills": ["Python", "Machine Learning", "..."]
}
```

### User Service (via Gateway)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Register new user |
| POST | `/auth/login` | No | Login and get JWT |
| GET | `/users/profile` | Yes | Get current user profile |
| PUT | `/users/profile` | Yes | Update user profile |

#### POST /auth/register

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe"
}
```

Response:
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

#### POST /auth/login

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

Response: same as register

#### GET /users/profile

Response:
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

#### PUT /users/profile

Request: partial update of profile fields
```json
{
  "interests": ["AI", "Cloud Computing"],
  "career_goal": "ML Engineer"
}
```

### AI Service (Phase 3 — Planned)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/chat` | Yes | AI consultation chat |
| POST | `/recommend` | Yes | Get personalized recommendations |
| GET | `/recommend/paths` | Yes | Get recommended learning paths |

#### POST /chat

Request:
```json
{
  "message": "I want to learn ML for healthcare",
  "conversation_id": "optional-session-id"
}
```

Response:
```json
{
  "reply": "Based on your background in...",
  "courses": [...],
  "conversation_id": "..."
}
```

#### POST /recommend

Request:
```json
{
  "limit": 10
}
```

Response:
```json
{
  "recommendations": [
    {
      "course": { ... },
      "score": 0.92,
      "reasons": ["Matches your interest in AI", "Fits your skill level"]
    }
  ]
}
```

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
| 503 | Service unavailable (DB connection failure) |

## Design Principles

1. **RESTful**: Resource-oriented URLs, standard HTTP methods
2. **Stateless**: No server-side session; JWT carries auth state
3. **Pagination**: All list endpoints support limit/offset
4. **Graceful degradation**: AI endpoints fall back to keyword search if vector DB unavailable
5. **Consistent errors**: Uniform error response format across all services
