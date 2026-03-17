# UI Design — Intelligent University Course Finder

**Tags**: #type/reference #domain/ui #domain/ux

---

## Design Principles

- **User profiling first**: Understand the user before recommending
- **Hub-based navigation**: After profiling, users freely choose features that fit their needs
- **Two modes**: Exploration (consulting) and Search (directed lookup)

---

## Personas (derived from data analysis)

### Persona A: "Don't know where to start" (Beginner)
- **Data basis**: Beginner 54%, Data/Programming/Business top domains
- **Pain Points**: #1 (keyword search fails), #4 (no learning path), #5 (career alignment unclear), #6 (technical jargon)

### Persona B: "What should I learn next?" (Intermediate)
- **Data basis**: AI&ML Intermediate 50.7%, Cloud&Infra Intermediate 42.1%
- **Pain Points**: #2 (prerequisites unclear), #3 (knowledge gap invisible), #4 (no structured path)

### Persona C: "Want a structured plan toward career goal" (Planner)
- **Data basis**: 1,023 Specializations, cross-domain skill relationships
- **Pain Points**: #4 (no structured path), #5 (career alignment), #7 (info scattered)

---

## Pain Points (from PDF)

1. Keyword search doesn't convey learning intent
2. Prerequisite relationships unclear
3. Knowledge gaps invisible to the learner
4. No structured learning paths
5. Can't find courses matching career goals
6. Technical/domain-specific language barrier
7. Information scattered across formats

---

## UX Flow

```
[Onboarding (skippable)] → [Home (Hub)] → Freely navigate features
                                │
                          ┌─────┼─────┬──────────┐
                          │     │     │          │
                        Explore Search Learning  Profile
                        Consult Filter  Path     Update
```

---

## Pages

### 1. Onboarding (first visit only, skippable)

Gather user profile:
- Existing knowledge/skills (multi-select or free text)
- Learning motivation (career change / skill-up / hobby / certification)
- Learning scope (intro only / specialization / undecided)
- Learning style (intensive / weekend pace / flexible)
- **Skip button**: proceeds to Home with a default (generic) profile

### 2. Home (Hub)

Personalized dashboard based on profile:
- Profile summary card ("Your Profile")
- Feature tiles/cards for navigation
- Highlighted recommendations based on user mode:
  - Exploration-type user → "Start with a consultation" prominent
  - Search-type user → "Find courses" prominent
- Quick stats (e.g., "6,645 courses available across 12 domains")

### 3. Explore / Consult (Consultation Mode)

- Chat UI for conversational exploration
- AI-driven dialogue to uncover interests and direction
- Output: direction suggestions + links to relevant courses
- **Primary for**: Persona A (Pain #1, #5, #6)

### 4. Course Search (Search Mode)

- Search bar (semantic search)
- Filters: Level, Skills/Domain, Organization
- Result cards with recommendation reasons
- Course detail page (full description, skills, level, organization, rating, modules, schedule)
- **Primary for**: Persona B, C (Pain #1, #2, #7)

### 5. Learning Path (Path Mode)

- Skill gap analysis visualization
- Recommended learning path (Beginner → Advanced sequence)
- Career path mapping
- Specialization utilization
- **Primary for**: Persona B, C (Pain #3, #4, #5)

### 6. Profile

- View/edit profile
- Update onboarding answers
- Learning history (future)

---

## Feature × Persona × Pain Point Matrix

| Feature | Persona A (Beginner) | Persona B (Intermediate) | Persona C (Planner) | Pain Points |
|---------|:---:|:---:|:---:|---|
| Onboarding | **Required** | **Required** | **Required** | Prerequisite |
| Home (Hub) | **Required** | **Required** | **Required** | #7 |
| Explore/Consult | **Primary** | Secondary | Secondary | #1 #5 #6 |
| Course Search | Secondary | **Primary** | **Primary** | #1 #2 #7 |
| Learning Path | — | **Primary** | **Primary** | #3 #4 #5 |
| Profile | Required | Required | Required | Prerequisite |

---

## Tech

- **Design System**: MUI (Material UI)
- **Framework**: React + JavaScript + Vite
- **Routing**: React Router

---

## Data Limitations to Communicate in UI

- Advanced courses are only 3.8% of catalog
- 29.4% of courses have no skill labels
- Rating mean 4.62 with low variance (weak differentiator)
- Satisfaction Rate 66.9% missing
