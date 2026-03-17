# Phase 2 Development Reference — Intelligent University Course Finder

## 1. Project Overview

The **Intelligent University Course Finder** is an AI-powered course discovery and recommendation system that helps students explore university course offerings from the Coursera dataset. The project follows a microservices architecture with a React frontend and Python/FastAPI backend.

**Current Phase**: Phase 2 is complete. The frontend UI, backend API layer, authentication, and basic recommendation logic are implemented. Phase 3 will add VectorDB, RAG pipeline, and AI Agents.

**What Phase 2 delivered**:
- Full microservices backend (Gateway, Course Service, User Service)
- MongoDB-backed user management with JWT auth
- React SPA with 7 pages: Home, Login, Onboarding, Search, Profile, Explore, Analysis
- Client-side recommendation scoring (keyword-based `scoreMatch` algorithm)
- Docker Compose orchestration for all services
- Udemy-inspired UI design with MUI component library

---

## 2. Architecture

### Text-Based Architecture Diagram

```
                    Browser (localhost:5173)
                         |
                    [Vite Dev Server]
                    (Docker: frontend)
                         |
                   /api proxy (vite.config.js)
                         |
                   [API Gateway]
                   (Docker: gateway)
                   port 8000
                  /             \
                 /               \
    [Course Service]        [User Service]
    (Docker: course-service) (Docker: user-service)
    port 8001 (internal)    port 8002 (internal)
    (in-memory JSON)              |
                            [MongoDB 7]
                            (Docker: mongo)
                            port 27017 (internal)
                            volume: mongo-data
```

### Service Responsibilities

| Service | Responsibility |
|---------|---------------|
| **frontend** | React SPA. Serves UI, proxies `/api` requests to gateway |
| **gateway** | API Gateway (FastAPI). Routes requests, handles JWT validation, CORS |
| **course-service** | Course data API. Loads `courses.json` into memory on startup, provides search/filter/list |
| **user-service** | User management. Registration, login, profile CRUD. Connects to MongoDB |
| **mongo** | MongoDB 7. Stores user documents with profiles |

### Communication Flow

1. **Frontend** makes HTTP requests to `/api/v1/*` (via axios client)
2. **Vite proxy** forwards `/api` to `http://gateway:8000`
3. **Gateway** routes requests:
   - Course endpoints: proxied via `httpx` to `http://course-service:8001`
   - Auth endpoints: proxied to `http://user-service:8002`
   - Protected endpoints: JWT decoded in gateway middleware, `x-user-id` header forwarded
4. **Course Service** reads from in-memory course data (loaded from JSON at startup)
5. **User Service** reads/writes to MongoDB via Motor (async driver)

### Port Mappings

| Service | Container Port | Host Port | Exposed? |
|---------|---------------|-----------|----------|
| frontend | 5173 | 5173 | Yes (browser access) |
| gateway | 8000 | 8000 | Yes (direct API access) |
| course-service | 8001 | — | No (internal only via `expose`) |
| user-service | 8002 | — | No (internal only via `expose`) |
| mongo | 27017 | — | No (internal only via `expose`) |

---

## 3. Directory Structure

```
Capstone/
├── docker-compose.yml              # Orchestrates all services
├── requirements.txt                # Root-level Python dependencies (unused in Docker)
├── data/                           # Data analysis notebooks
│   └── explore.ipynb               # Dataset exploration notebook
├── mock/
│   └── index.html                  # Early HTML prototype/mockup
├── ref/                            # Design & reference documents
│   ├── Architecture.md             # Architecture design (stub)
│   ├── Requirements.md             # Project requirements
│   ├── Tech Stack.md               # Technology choices
│   ├── Discussion.md               # Development discussion log
│   ├── Dataset Analysis.md         # Dataset analysis notes
│   ├── Development Plan.md         # Development plan
│   ├── UI Design.md                # UI design notes
│   └── Phase2-Notes.md             # THIS FILE
│
├── frontend/                       # React SPA
│   ├── Dockerfile                  # Node 20 Alpine, npm install, vite dev
│   ├── package.json                # Dependencies: React 18, MUI 6, axios, react-router-dom 6
│   ├── vite.config.js              # Dev server config + /api proxy to gateway
│   └── src/
│       ├── main.jsx                # App entry: BrowserRouter + ThemeProvider + AuthProvider
│       ├── App.jsx                 # Route definitions (7 routes)
│       ├── theme.js                # MUI theme: Inter font, primary=#6c63ff, borderRadius=12
│       ├── api/
│       │   └── client.js           # Axios instance: baseURL=/api/v1, JWT interceptor, 401 redirect
│       ├── contexts/
│       │   └── AuthContext.jsx     # Auth state: user, token, login/logout/updateUser, localStorage persistence
│       ├── components/
│       │   ├── Layout.jsx          # Page layout wrapper (Navbar + Outlet + Footer)
│       │   ├── Navbar.jsx          # Top nav: logo, nav links, global search bar, user menu
│       │   └── Footer.jsx          # Footer component
│       └── features/
│           ├── auth/
│           │   ├── Login.jsx       # Login/Register tabs, form submission
│           │   └── api.js          # registerUser, loginUser API calls
│           ├── onboarding/
│           │   └── Onboarding.jsx  # 4-step profile setup wizard (skills, motivation, scope, style)
│           ├── home/
│           │   └── Home.jsx        # Hub: profile banner, enrolled courses (stub), recommendations, quick actions
│           ├── courses/
│           │   ├── Search.jsx      # Browse page: trending topics, filters (level/org/skills), grid, pagination
│           │   ├── CourseCard.jsx   # Reusable course card with "Why recommended" section
│           │   ├── RecommendedSection.jsx  # Standalone recommended courses widget (used in earlier iterations)
│           │   └── api.js          # getCourses, searchCourses, getFilterOptions API calls
│           ├── profile/
│           │   ├── Profile.jsx     # View/edit profile page with inline editing
│           │   └── api.js          # getProfile, updateProfile API calls
│           ├── explore/
│           │   └── Explore.jsx     # AI chat stub: model selector, message UI, suggestion chips
│           ├── analysis/
│           │   └── Analysis.jsx    # Personal analysis: domain coverage, career alignment, skill gaps, learning paths
│           └── learning-path/
│               └── LearningPath.jsx  # ORPHANED: route removed, functionality merged into Analysis
│
├── services/
│   ├── gateway/                    # API Gateway service
│   │   ├── Dockerfile
│   │   ├── requirements.txt        # fastapi, uvicorn, httpx, python-jose, pydantic-settings
│   │   └── app/
│   │       ├── __init__.py
│   │       ├── main.py             # FastAPI app: CORS middleware, includes course + user routers
│   │       ├── config.py           # Settings: service URLs, JWT config, frontend_origin
│   │       ├── middleware/
│   │       │   ├── __init__.py
│   │       │   └── auth.py         # JWT decode: require_auth (mandatory), optional_auth
│   │       └── routers/
│   │           ├── __init__.py
│   │           ├── courses.py      # Proxy routes: /courses, /courses/search, /filters/options, /courses/{id}
│   │           └── users.py        # Proxy routes: /auth/register, /auth/login, /users/profile (GET/PUT)
│   │
│   ├── course_service/             # Course data microservice
│   │   ├── Dockerfile
│   │   ├── requirements.txt        # fastapi, uvicorn, pydantic-settings
│   │   ├── data/
│   │   │   └── courses.json        # Coursera dataset (JSON format)
│   │   └── app/
│   │       ├── __init__.py
│   │       ├── main.py             # FastAPI app: loads courses on startup via lifespan
│   │       ├── config.py           # Settings: host, port=8001
│   │       ├── models/
│   │       │   ├── __init__.py
│   │       │   └── course.py       # Pydantic models: Course, CourseListResponse, FilterOptions
│   │       ├── routers/
│   │       │   ├── __init__.py
│   │       │   └── courses.py      # Endpoints: list, search, get by ID, filter options
│   │       └── services/
│   │           ├── __init__.py
│   │           └── course_service.py  # Business logic: in-memory filtering, keyword search, pagination
│   │
│   └── user_service/               # User management microservice
│       ├── Dockerfile
│       ├── requirements.txt        # fastapi, uvicorn, motor, pymongo, passlib, python-jose, pydantic-settings, email-validator
│       └── app/
│           ├── __init__.py
│           ├── main.py             # FastAPI app: MongoDB connect/disconnect via lifespan
│           ├── config.py           # Settings: mongo_uri, mongo_db, JWT config, expire=24h
│           ├── models/
│           │   ├── __init__.py
│           │   └── user.py         # Pydantic models: UserProfile, UserCreate, UserLogin, UserResponse, ProfileUpdate, TokenResponse
│           ├── routers/
│           │   ├── __init__.py
│           │   ├── auth.py         # POST /auth/register, POST /auth/login
│           │   └── profile.py      # GET /users/profile, PUT /users/profile (x-user-id header)
│           └── services/
│               ├── __init__.py
│               └── user_service.py # Business logic: bcrypt hashing, JWT creation, MongoDB CRUD
```

---

## 4. Tech Stack (Confirmed)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Frontend Framework** | React 18 + JavaScript | Simpler than TypeScript for rapid prototyping. No type overhead for a demo project. React chosen over vanilla for component reusability. |
| **Build Tool** | Vite 5 | Fast HMR, simple config, built-in proxy for CORS avoidance. Chosen over CRA (deprecated) and webpack (complex config). |
| **UI Library** | MUI 6 (Material UI) | Rich component set out of the box (Tabs, Chips, Pagination, etc.). Reduces custom CSS. Emotion-based styling for inline sx prop. |
| **HTTP Client** | Axios | Interceptors for JWT injection and 401 handling. Cleaner API than fetch for request/response transforms. |
| **Routing** | React Router DOM 6 | Standard for React SPAs. URL param support for search queries (`?q=...`). |
| **Backend Framework** | Python + FastAPI | Async support, auto-generated OpenAPI docs, Pydantic validation. Microservices pattern with separate FastAPI apps per service. |
| **API Gateway Pattern** | FastAPI + httpx | Gateway proxies requests to internal services. JWT validation at gateway level, forwarding user ID via headers. |
| **Database** | MongoDB 7 (via Motor async driver) | Schema-flexible for evolving user profiles. Under review for Phase 3 — may add VectorDB alongside. |
| **Auth** | JWT (HS256) | Token stored in localStorage. 24h expiry. Bcrypt password hashing via passlib. python-jose for JWT encode/decode. |
| **Infrastructure** | Docker Compose | All 5 services (frontend, gateway, course-service, user-service, mongo) in one stack. Bridge network for service discovery by container name. |
| **LLM Orchestration** | OpenAI Agents SDK | Confirmed for Phase 3. Agent SDK-based architecture for multi-agent pipeline. |
| **Evaluation** | DeepEval | Required by project requirements. For recommendation relevance and learning outcome evaluation. |
| **Observability** | LangFuse, Arize Phoenix | Tracing and monitoring for LLM calls (Phase 3). |

### Not Chosen (and Why)

| Alternative | Why Not |
|-------------|---------|
| TypeScript | Added complexity for a prototype. JavaScript sufficient for demo scope. |
| Next.js | SSR not needed. SPA with client-side routing is simpler for this use case. |
| PostgreSQL | Schema flexibility needed for evolving user profiles. MongoDB more natural fit for document-shaped profile data. |
| Local Node.js | Node.js is not installed on the host machine. Frontend runs entirely in Docker. |

---

## 5. API Reference

All frontend requests go through `/api/v1/*` (Vite proxy -> Gateway).

### Course Endpoints (No Auth Required)

#### `GET /api/v1/courses`
List courses with optional filters and pagination.

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| level | string | — | Filter by difficulty (Beginner, Intermediate, Advanced) |
| organization | string | — | Filter by organization (substring match) |
| min_rating | float | — | Minimum rating threshold |
| skills | string[] | — | Filter by skill tags (exact match) |
| limit | int | 20 | Page size (1-100) |
| offset | int | 0 | Pagination offset |

**Response** (`CourseListResponse`):
```json
{
  "courses": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "organization": "string",
      "instructor": "string",
      "level": "Beginner|Intermediate|Advanced",
      "rating": 4.7,
      "num_reviews": 1234,
      "enrolled": "100k",
      "skills": ["Python", "Data Analysis"],
      "modules": "string",
      "schedule": "string",
      "url": "https://...",
      "satisfaction_rate": "97%"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

#### `GET /api/v1/courses/search`
Keyword search across title, description, and skills.

**Query Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| q | string | Yes | Search query (min 1 char) |
| limit | int | No (20) | Page size |
| offset | int | No (0) | Pagination offset |

**Response**: Same as `CourseListResponse`.

#### `GET /api/v1/courses/{course_id}`
Get a single course by ID.

**Response**: Single `Course` object. 404 if not found.

#### `GET /api/v1/filters/options`
Get available filter values.

**Response** (`FilterOptions`):
```json
{
  "levels": ["Beginner", "Intermediate", "Advanced"],
  "organizations": ["Google Cloud", "IBM", "Stanford University", ...],
  "skills": ["Python", "Machine Learning", ...]
}
```

### Auth Endpoints (No Auth Required)

#### `POST /api/v1/auth/register`
Create a new user account.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "string",
  "name": "John Doe"
}
```

**Response** (`TokenResponse`):
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "ObjectId string",
    "email": "user@example.com",
    "name": "John Doe",
    "profile": {
      "skills": [],
      "motivation": null,
      "learning_scope": null,
      "learning_style": null,
      "interest_areas": []
    },
    "created_at": "2026-03-15T..."
  }
}
```

#### `POST /api/v1/auth/login`
Authenticate and receive a JWT token.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "string"
}
```

**Response**: Same as `TokenResponse`. 401 on invalid credentials.

### User Endpoints (Auth Required — Bearer Token)

#### `GET /api/v1/users/profile`
Get the authenticated user's profile.

**Headers**: `Authorization: Bearer <token>`

**Response**: `UserResponse` object (same structure as `user` in TokenResponse).

#### `PUT /api/v1/users/profile`
Update the authenticated user's learning profile.

**Headers**: `Authorization: Bearer <token>`

**Request Body** (`ProfileUpdate` — all fields optional):
```json
{
  "skills": ["Python", "SQL"],
  "motivation": "Career Change",
  "learning_scope": "Full Learning Path",
  "learning_style": "Hands-on Projects",
  "interest_areas": ["Data Science"]
}
```

**Response**: Updated `UserResponse` object.

### Health Check Endpoints (Internal)

| Endpoint | Service |
|----------|---------|
| `GET /health` | Gateway (port 8000) |
| `GET /health` | Course Service (port 8001) |
| `GET /health` | User Service (port 8002) |

---

## 6. Frontend Pages & Routes

| Route | Component | Auth Required | Description |
|-------|-----------|--------------|-------------|
| `/` | `Home` | No (enhanced with auth) | Hub page: profile banner, enrolled courses (stub), personalized recommendations, quick action cards |
| `/login` | `Login` | No | Login/Register tabs. After register, redirects to `/onboarding`. After login, redirects to `/`. |
| `/onboarding` | `Onboarding` | Implicit (post-register) | 4-step wizard: skills selection, motivation, learning scope, learning style. Saves to user profile via PUT. |
| `/search` | `Search` | No | Browse courses: trending topic chips, 3-column card grid, left sidebar filters (level, org with search, skills with search), pagination (12 per page). Reads `?q=` from URL params. |
| `/profile` | `Profile` | Yes (redirects) | View account info + learning profile. Inline edit mode for profile fields. |
| `/explore` | `Explore` | No | AI chat stub. Model selector (GPT-4o / GPT-4o mini), message bubbles, suggestion chips. All responses are hardcoded placeholder text. |
| `/analysis` | `Analysis` | Yes (redirects) | Personal analysis dashboard: skill domain coverage bars, career path alignment scores, skill gap identification with clickable chips (navigate to search), recommended learning paths (5 static paths with timeline visualization). |
| `*` | — | — | Catch-all redirects to `/` |

### Key Page Features

**Home (`/`)**:
- Welcome header with user name
- Profile banner (gradient, skills chips, motivation insight card)
- Enrolled courses section with progress bars (STUB DATA — `ENROLLED_STUB` array)
- Learning insight banner (schedule suggestion)
- Recommended/Popular courses (horizontal scroll cards)
- Quick action cards: Explore & Consult, Learning Path, Skill Coverage

**Search (`/search`)**:
- Global search from Navbar: Enter key triggers navigation to `/search?q=<query>`
- Trending topics bar (8 predefined topics: Machine Learning, Python, etc.)
- Left filter panel (sticky, 240px wide):
  - Level: chip toggle (Beginner/Intermediate/Advanced)
  - Organization: searchable list with chip selection
  - Skills: searchable list with chip selection
- Results grid: responsive 1/2/3 columns
- Each CourseCard shows: title, org, rating star chip, level badge, "Why recommended" reasons
- Pagination component at bottom

**Analysis (`/analysis`)**:
- Preview mode alert (keyword matching, not AI)
- Skill Domain Coverage: 6 domains (Data & Analytics, AI & ML, Cloud, Security, Business, Web Dev), progress bars, matched/unmatched skill chips
- Career Path Alignment: 4 careers (Data Scientist, Cloud Engineer, Product Manager, ML Engineer), percentage score bars
- Skills to Develop: clickable gap chips that navigate to `/search?q=<skill>`
- Recommended Learning Paths: 5 static paths (Data Scientist, Cloud Engineer, ML Engineer, Product Manager, Full-Stack), each with 3-step timeline visualization

---

## 7. Key Design Decisions & Lessons Learned

### Feature-Based Directory Structure
Files are organized by feature (`features/auth/`, `features/courses/`, etc.) rather than by type (`components/`, `pages/`, `hooks/`). Each feature folder contains its page component and API module together. This keeps related code co-located and makes it easy to find everything about a feature in one place.

### Udemy-Style UI Design Language
The UI follows Udemy's visual patterns: full-width layouts, horizontal scroll card rows, rounded chips for filters, sticky sidebar filter panel, and a dark navbar with integrated search. This was refined through multiple iterations based on user feedback. The primary accent color is `#6c63ff` (purple) consistently used across all components.

### Client-Side Recommendation Scoring (`scoreMatch` algorithm)
Recommendations use a client-side scoring function that evaluates courses against the user's profile:
- +2 points per overlapping skill (bidirectional substring match)
- +1 point per new skill the course teaches
- +1 point for rating >= 4.5
- +2 points for motivation-level alignment (e.g., "Career Change" + "Beginner")

This algorithm appears in three places: `Home.jsx`, `Search.jsx`, and `RecommendedSection.jsx`. In Phase 3, this will be replaced by AI Agent-based scoring.

### Global Search via URL Parameters
The Navbar search bar is a global entry point. On Enter, it navigates to `/search?q=<encoded_query>`. The Search page reads `?q=` from URL params via `useSearchParams()` and triggers `searchCourses()`. This decouples the search trigger (Navbar) from the search execution (Search page).

### Docker-Based Frontend Development
Since Node.js is not installed on the host machine, the frontend runs entirely in Docker. The Vite dev server runs inside the container with `host: "0.0.0.0"` to accept connections from the host browser. File changes on the host are mounted into the container, but a Docker rebuild (`docker compose up -d --build frontend`) is needed for dependency changes.

### Vite Proxy for CORS Avoidance
The frontend's `vite.config.js` proxies `/api` requests to `http://gateway:8000`. This means the browser only sees same-origin requests (all to `localhost:5173`), completely avoiding CORS issues during development. The gateway still has CORS middleware configured as a fallback for direct API access.

### Full-Width Layout
After removing the `maxWidth` constraint, pages use responsive horizontal padding: `px: { xs: 2, md: 6, lg: 10 }`. This gives the app a spacious, modern feel similar to Udemy rather than a cramped centered column.

### Learning Path Merged into Personal Analysis
The Learning Path page (`LearningPath.jsx`) was originally a separate route. Its content was merged into the Analysis page as the "Recommended Learning Paths" section, providing a single comprehensive dashboard. The `LearningPath.jsx` file still exists but its route was removed from `App.jsx`.

### RecommendedSection Component
`RecommendedSection.jsx` exists as a standalone widget with its own `scoreMatch` function. The Home page now has its own inline implementation using the same CourseCard style. The component could be consolidated in a future cleanup.

---

## 8. Development Notes for AI Coding Assistants

### Environment Constraints
- **Node.js is NOT installed on the host**. The frontend runs in a Docker container. Do not attempt `npm` commands directly.
- **Python (Miniconda)** is available at `/c/Users/yuila/miniconda3/python.exe` for running scripts.
- **Git Bash** is the shell. Use Unix-style paths and commands.

### Frontend Development Workflow
1. Edit source files in `frontend/src/` on the host
2. Rebuild: `docker compose up -d --build frontend`
3. Access at `http://localhost:5173`
4. For dependency changes, update `package.json` then rebuild

### Claude Code Tool Usage
- **Write tool** requires reading the file first (even a partial read works). Use Write for complete file rewrites.
- **Edit tool** requires exact string match including whitespace/indentation. Use Edit for small targeted changes.
- When writing JSX files, prefer Write for large changes and Edit for small modifications.
- The `docker-compose.yml` path uses underscores for service directories (`course_service`, `user_service`) but hyphens for container names (`course-service`, `user-service`).

### Service Rebuilding
```bash
# Rebuild a single service
docker compose up -d --build frontend
docker compose up -d --build gateway
docker compose up -d --build course-service
docker compose up -d --build user-service

# Rebuild everything
docker compose up -d --build

# View logs
docker compose logs -f frontend
docker compose logs -f gateway
```

### MongoDB
- Runs in Docker, data persists in `mongo-data` Docker volume
- Database name: `course_finder`
- Collection: `users`
- Unique index on `email` field
- To reset: `docker compose down -v` (destroys volume)

### API Proxy Chain
```
Browser request:  GET /api/v1/courses?limit=20
  -> Vite proxy:  GET http://gateway:8000/api/v1/courses?limit=20
  -> Gateway:     GET http://course-service:8001/courses?limit=20
  -> Course Svc:  Returns CourseListResponse
```

### JWT Auth Flow
1. Login/Register returns `{ access_token, user }`
2. Frontend stores `token` and `user` in localStorage
3. Axios interceptor adds `Authorization: Bearer <token>` to all requests
4. Gateway's `require_auth` dependency decodes JWT, extracts `sub` (user_id)
5. Gateway forwards `x-user-id` header to User Service
6. On 401 response, axios interceptor clears localStorage and redirects to `/login`

---

## 9. Known Issues & TODOs

### Active Issues
- **CORS configuration**: Gateway allows `http://localhost:5173` and `http://localhost:3000`. Production deployment will need environment-based origin configuration.
- **Enrolled courses**: `Home.jsx` uses hardcoded `ENROLLED_STUB` array. Needs real enrollment tracking (new collection in MongoDB + endpoints).
- **Explore chat**: Fully stubbed. Every user message gets a static placeholder response. Needs LLM API connection.
- **Analysis keyword matching**: `Analysis.jsx` uses simple substring matching against predefined `SKILL_DOMAINS` arrays. Will be replaced by AI Agent interpretation in Phase 3.
- **Recommended paths**: `RECOMMENDED_PATHS` in `Analysis.jsx` is a static array of 5 hardcoded paths. Needs AI-generated paths based on user profile and course catalog.
- **LearningPath.jsx**: Orphaned file. Route removed from `App.jsx` but file remains in `features/learning-path/`. Can be safely deleted.
- **scoreMatch duplication**: The `scoreMatch` function is duplicated across `Home.jsx`, `Search.jsx`, and `RecommendedSection.jsx`. Should be extracted to a shared utility.

### Minor Items
- **Error handling**: Several `catch(() => {})` blocks silently swallow errors. Should add user-visible error states.
- **Loading states**: Some pages lack loading indicators when fetching data.
- **Profile page layout**: Uses `maxWidth: 800` while other pages use full-width. May want to unify.
- **Search debouncing**: Filter panel searches (org/skills) filter on every keystroke. No debounce.
- **Course detail page**: No dedicated course detail page exists. Course cards open the external Coursera URL in a new tab.

---

## 10. Phase 3 Plan (Upcoming)

### VectorDB Selection (In Discussion)
Candidates: ChromaDB, Qdrant, Weaviate. Need to decide based on:
- Embedding model compatibility
- Hybrid search support (vector + keyword)
- Ease of Docker integration
- Cross-encoder reranking support

### RAG Pipeline
- Embed course descriptions using a selected embedding model
- Store embeddings in VectorDB
- Replace keyword-based `search_courses()` with semantic search
- Add hybrid retrieval (vector similarity + keyword matching)
- Cross-encoder reranking for result quality

### 5 AI Agents (OpenAI Agents SDK)
1. **Course Retrieval Agent** — Semantic course search and retrieval
2. **Skill Gap Analysis Agent** — Contextual skill gap identification (replaces keyword matching in Analysis)
3. **Learning Path Planning Agent** — Dynamic learning path generation (replaces static `RECOMMENDED_PATHS`)
4. **Career Alignment Agent** — Career path analysis with LLM reasoning
5. **Learning Advisor Agent** — Conversational course advisor (powers the Explore chat)

### LLM API Integration
- Connect Explore chat to OpenAI API (GPT-4o / GPT-4o mini)
- Model selector in UI already prepared
- Streaming response support
- Cost estimation per query

### AI-Powered Analysis
- Replace `SKILL_DOMAINS` keyword matching with Agent-based analysis
- Replace `CAREER_PATHS` static scoring with LLM-powered career alignment
- Replace `RECOMMENDED_PATHS` static data with dynamically generated paths
- Add DeepEval evaluation for recommendation quality

### Evaluation & Observability
- DeepEval integration for recommendation relevance scoring
- LangFuse/Arize Phoenix for LLM call tracing
- Performance benchmarks for real-time recommendations
