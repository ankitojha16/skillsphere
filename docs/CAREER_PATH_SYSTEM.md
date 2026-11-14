# SkillSphere Career Path System

## 1. Overview

The **Career Path System** provides students with 11 curated, industry-aligned engineering tracks. Each track defines a comprehensive roadmap of skills, recommended projects, benchmark descriptions, and interview topics.

---

## 2. The 11 Curated Career Tracks

| # | Track Name | Slug | Difficulty Tier | Market Demand | Benchmark Salary | Icon |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Frontend Developer** | `frontend-developer` | Intermediate | High | ₹6L - ₹18L / $85k - $135k | `layout` |
| 2 | **Backend Developer** | `backend-developer` | Intermediate | Surging | ₹8L - ₹22L / $95k - $155k | `server` |
| 3 | **Full Stack Developer** | `fullstack-developer` | Advanced | Very High | ₹9L - ₹25L / $100k - $165k | `layers` |
| 4 | **Python Developer** | `python-developer` | Beginner Friendly | High | ₹6L - ₹19L / $80k - $140k | `terminal` |
| 5 | **Data Analyst** | `data-analyst` | Beginner Friendly | High | ₹5L - ₹15L / $75k - $120k | `bar-chart-2` |
| 6 | **Data Scientist** | `data-scientist` | Advanced | High | ₹10L - ₹28L / $110k - $175k | `pie-chart` |
| 7 | **AI/ML Engineer** | `ai-ml-engineer` | Specialized | Surging | ₹12L - ₹32L / $125k - $195k | `cpu` |
| 8 | **Cybersecurity Analyst**| `cybersecurity-analyst` | Intermediate | High | ₹7L - ₹20L / $90k - $150k | `shield-check` |
| 9 | **Cloud Engineer** | `cloud-engineer` | Intermediate | Surging | ₹9L - ₹24L / $105k - $165k | `cloud` |
| 10 | **UI/UX Designer** | `ui-ux-designer` | Beginner Friendly | Stable | ₹5L - ₹16L / $70k - $125k | `palette` |
| 11 | **FinTech Analyst** | `fintech-analyst` | Intermediate | High | ₹8L - ₹24L / $95k - $160k | `trending-up` |

---

## 3. Career Track Data Schema

Each `CareerTrack` entity contains structured, queryable configuration:

```json
{
  "slug": "backend-developer",
  "title": "Backend Developer",
  "icon": "server",
  "badge": "Core Architecture",
  "summary": "Architect high-throughput server backends, microservices, databases, authentication, and security.",
  "difficulty_level": "Intermediate",
  "average_salary_range": "₹8L - ₹22L",
  "market_demand": "Surging",
  "primary_skills": [
    "Python", "Django", "PostgreSQL", "REST APIs", "Redis", "Docker"
  ],
  "tools_and_technologies": [
    "Docker", "PostgreSQL", "Redis", "Postman", "Nginx", "Git"
  ],
  "suggested_projects": [
    {
      "title": "High-Throughput Payment Processing API",
      "difficulty": "Intermediate",
      "stack": "Python, Django, PostgreSQL, Redis",
      "description": "Idempotent payment webhook consumer with distributed transaction isolation."
    }
  ],
  "learning_milestones": [
    {
      "title": "Phase 1: RESTful API Design & HTTP Protocols",
      "weeks": 3,
      "topics": ["REST Standards", "Status Codes", "Authentication", "Validation"],
      "mini_project": "RESTful Gateway"
    }
  ],
  "interview_topics": [
    "Database indexing (B-Tree vs Hash)",
    "CAP theorem & consistency models",
    "Rate limiting algorithms",
    "ACID transaction isolation levels"
  ]
}
```

---

## 4. Seeding & Database Synchronization

The track catalog is managed via Django management commands:
```bash
python manage.py seed_career_tracks
```
The command is idempotent: it uses `update_or_create` keyed on `slug`, ensuring that existing student links (`StudentCareerGoal`, `SkillGapReport`) are maintained without primary key mutation.
