# SkillSphere – Online Learning & Career Development Platform
> **Tagline:** *"Learn Skills. Build Projects. Track Your Growth."*

SkillSphere is a full-stack, database-driven web application built with **Python 3.12+, Django 4.2 LTS, Bootstrap 5, Chart.js, Lucide Icons, and PostgreSQL**. Designed specifically for students, college learners, and aspiring software engineers, SkillSphere bridges the gap between structured technical curricula and practical career progression.

---

## 🌟 Key Features

### 1. 🔐 Complete Authentication & Onboarding
- **Student Registration**: Unique email validation, password security validation, and terms agreement.
- **Auto Profile Setup**: Newly registered students configure their education level, college/institution, technical skill level, learning interests, and target career goals.
- **Secure Authentication**: Django session authentication, password hashing, and "Remember Me" support.
- **Password Recovery**: Complete token-based password reset flow with email notification templates.

### 2. 📊 Personalized Student Dashboard
- **Welcome Banner**: Dynamic greetings, current date, profile avatar, and rotating engineering motivational quotes.
- **Computed Real-Time Statistics**:
  - Total Enrolled Courses
  - Completed Courses (100% finished)
  - Total Completed Lessons
  - Overall Learning Progress Percentage
- **Weekly Learning Activity (Chart.js)**: Interactive bar chart plotting daily completed lessons over the past 7 days based on real database timestamps.
- **Continue Learning**: Quick-access cards with calculated progress bars linking directly to the next unfinished lesson.
- **Active Learning Goals & Activity Feed**: Real-time audit log of enrollments, lesson completions, and goal achievements.

### 3. 📚 Dynamic Course Library & Discovery
- **8 Core Technical Categories**:
  1. Programming
  2. Web Development
  3. Data Structures & Algorithms
  4. Database Management
  5. Artificial Intelligence
  6. Data Science
  7. Computer Science Fundamentals
  8. Career Development
- **Live Search & Filtering**: Instant search across titles, descriptions, and instructors, with category chips, difficulty filters (Beginner, Intermediate, Advanced), and popularity/recency sorting.
- **Course Detail & Syllabus Breakdown**: Detailed curriculum overview, learning objectives checklist, and instructor credentials.
- **Enrollment Management**: One-click enrollment and unenrollment with protection against duplicate enrollments.

### 4. 📖 Dedicated Distraction-Free Learning Interface
- **Left Syllabus Sidebar**: Structured module and chapter lists with real-time completion checkmarks and progress percentage indicators.
- **Rich Lesson Content**: Formatted tutorials with code blocks, key takeaways, diagrams, and external reference links.
- **Navigation & Interactive Progress**:
  - `[Previous Lesson]` and `[Complete & Next Lesson]` controls.
  - Interactive AJAX completion button that updates course progress and dashboard statistics instantly without page reloads.
  - Strict security: Only enrolled students can access protected lesson material.

### 5. 🎯 Personal Learning Goals
- **Milestone Management**: Create, edit, delete, and toggle personal study milestones with target dates.
- **Status Indicators**: Tracks "In Progress", "Achieved", and "Overdue" milestones with a completion rate percentage.
- **Data Isolation**: Strict user-level isolation ensures students only ever view and edit their own goals.

### 6. 🤖 AI Study Assistant (`/ai-assistant/`)
- **5 Pedagogical Modes**: Simple / Beginner-Friendly, Detailed Architectural, Code Implementation, Real-World Example / Analogy, and Quick Revision Cheat Sheet.
- **Persistent Sessions**: Multiple study conversations saved in PostgreSQL, with ability to switch, delete, or clear history.
- **Resilient AI Backend**: Integrates with Google Gemini / OpenAI via environment variables with intelligent educational fallbacks.

### 7. 🗺️ AI Personalized Learning Roadmaps (`/learning-roadmap/`)
- **Custom Curriculum Generator**: Architected based on skill, current level, career goal, available time, and target duration.
- **Structured Phases**: Sequential milestones, key technical subtopics, and practical mini-project challenges.
- **Progress Tracking**: Interactive milestone checkmarks with real-time percentage progress updates.

### 8. 📝 Technical Skill Assessments (`/skill-assessment/`)
- **10 Core Subject Areas**: Python, C, C++, Java, HTML/CSS, JavaScript, SQL, DSA, Django, and CS Fundamentals.
- **Interactive Quiz Player**: Multiple-choice questions, timed tests, instant grading, and percentage scoring.
- **Diagnostic Feedback**: AI evaluation of strengths, areas needing improvement, and smart links to relevant SkillSphere courses.

### 9. 💼 AI Technical Mock Interviews (`/mock-interview/`)
- **7 Interview Tracks**: Python Developer, Django Developer, Frontend, Backend, SQL, General Programming, and HR/Behavioral.
- **Multi-Turn Evaluation**: AI provides rating (1-10) and constructive feedback on technical correctness and communication clarity per question.
- **Executive Final Report**: Comprehensive performance review, strong areas, improvement areas, and question transcripts.

### 10. 💡 AI Practical Project Generator (`/project-generator/`)
- **Architecture Blueprints**: Generates problem statements, objectives, tech stacks, core features, database schema requirements, and development phases.
- **Saved Collection**: Save and organize portfolio ideas with category filtering.

### 11. 🏆 Gamification & Consistency (`/achievements/`)
- **Experience Points (XP)**: Earned through lessons (+25), quizzes (+50), roadmap milestones (+40), interviews (+75), and courses (+150).
- **6 Developer Tiers**: Beginner (0+) -> Explorer (100+) -> Learner (300+) -> Developer (600+) -> Advanced Learner (1000+) -> Skill Master (1500+).
- **Badges & Daily Streaks**: Unlocked achievements and consecutive daily activity tracking.

### 12. 💼 Career Hub & Analytics (`/career-hub/`, `/career-analytics/`)
- **Career Readiness Index (CRI)**: Proprietary 0-100 score weighted across course completions, assessments, mock interviews, projects, and portfolio status.
- **Career Tracks**: In-depth role breakdowns (Full Stack, Backend, Data Science, AI Engineer) mapping required courses, roadmaps, recommended projects, and industry interview tracks.
- **Interactive Readiness Radar**: Visual multi-dimensional spider/radar chart displaying technical proficiency across categories.

### 13. 🌐 Professional Student Portfolio Builder (`/portfolio/`)
- **Public Showcase URLs**: Shareable URLs (`/u/<username>/`) with 3 switchable designer themes:
  - `Minimalist Dev` (clean typography, crisp grid, code-first)
  - `Modern Creative` (vibrant dark glassmorphism, accent glow badges)
  - `Executive Professional` (high-contrast structured layout for corporate hiring)
- **Automatic Sync**: Syncs user GitHub, LinkedIn, bio, completed certifications, verified projects, and top skills.

### 14. 📄 AI Resume Builder & ATS Checker (`/resume-builder/`)
- **Targeted ATS Scoring**: Evaluates readability, action verb density, quantifiable metrics, and skills alignment (0-100 score with targeted advice).
- **AI Enhancement**: Rewrites project bullets with STAR methodology ("Engineered...", "Implemented...", "Reduced latency by...").
- **Pure-Python PDF Export**: Generates professional, ATS-formatted PDF documents using ReportLab.

### 15. 🎯 Internship & Opportunity Portal (`/opportunities/`)
- **Verified Listings**: Curated software engineering internships, graduate fellowships, open-source programs, and research opportunities.
- **Kanban Application Tracker (`/opportunities/tracker/`)**: Tracks job search pipelines across `Interested`, `Applied`, `Interviewing`, `Offer`, and `Archived` with notes.

### 16. 💬 Student Community & Moderation (`/community/`)
- **Peer Discussions**: Discussion categories (Code Help, Career Advice, Project Showcases, Study Groups).
- **Engagement & Moderation**: Upvoting, nested comments, reporting workflow, and admin moderation queue.

### 17. 🤝 Project Collaboration Hub (`/collaboration/`)
- **Student Team Formation**: Post project concepts, list open engineering roles (e.g., Frontend, Backend, UI/UX), and recruit teammates.
- **Join Requests Pipeline**: Team leads accept or decline applicant requests with real-time notifications.

### 18. 🎪 Hackathons & Events Hub (`/events/`)
- **Curated Events Calendar**: Collegiate hackathons, tech webinars, campus hiring summits, and workshops.
- **One-Click Reminders**: Save events to your personal calendar and receive in-app notifications.

### 19. 📜 Certificate Center & Public Verification (`/certificates/`)
- **Automated Issuance**: Automatically unlocks upon 100% course completion.
- **Tamper-Evident Verification (`/verify/<certificate_id>/`)**: Public QR-ready verification page confirming student identity, issue date, credential ID, and course mastery without exposing private personal information.
- **Official PDF Generation**: ReportLab-generated high-resolution certificate with decorative borders and cryptographic verification hashes.

### 20. 🔔 Notification Center (`/notifications/`)
- **Real-Time In-App Alerts**: Global unread badge in navigation for application updates, team join decisions, community replies, and certificate claims.

### 21. 🛡️ Django Admin Panel Upgrades
- Full administration controls across all 21 models with inline editing, batch verification, moderation queues, and status filtering.

---

## 🎨 Design System & Color Palette

SkillSphere features a modern, dark SaaS aesthetic:

| Token | Hex Code | Description |
|---|---|---|
| **Primary Background** | `#0B1020` | Deep dark cosmic background |
| **Secondary Background** | `#11182B` | Sidebar and navigation surface |
| **Surface / Card** | `#161F37` | Content card background |
| **Surface Hover** | `#1C2646` | Interactive hover card state |
| **Primary Accent** | `#8B5CF6` | Vibrant violet / purple |
| **Secondary Accent** | `#06B6D4` | High-tech cyan |
| **Success** | `#22C55E` | Emerald green (progress & achievements) |
| **Main Text** | `#F8FAFC` | Bright crisp foreground typography |
| **Secondary Text** | `#94A3B8` | Subdued secondary labels |

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12+ / Django 4.2 LTS / Django REST Framework
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Lucide Icons, Chart.js
- **PDF Engine**: ReportLab 5.1
- **Database**: PostgreSQL (with graceful automatic local SQLite fallback for offline sandbox testing)
- **Static Asset Pipeline**: WhiteNoise 6.11 with compressed storage
- **Application Server**: Gunicorn 23.0

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+ (Python 3.12 recommended)
- `pip` and `virtualenv`
- (Optional) PostgreSQL server installed and running

### 2. Installation
```bash
# Clone or navigate to repository
cd "skill sphare"

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Template configuration (safe placeholders):
```ini
SECRET_KEY=<your-secure-random-secret-key>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (PostgreSQL / Supabase)
DATABASE_URL=postgresql://<db_user>:<db_password>@<db_host>:5432/<db_name>

# Discrete PostgreSQL Settings:
DB_ENGINE=django.db.backends.postgresql
DB_NAME=<db_name>
DB_USER=<db_user>
DB_PASSWORD=<db_password>
DB_HOST=localhost
DB_PORT=5432

# Set to True to allow automatic fallback to SQLite when PostgreSQL service is offline
USE_SQLITE_FALLBACK=True
```

### 4. Database Setup & Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed Initial Curriculum
Populates structured modules, lessons, exercises, assessments, and sample tracks:
```bash
python manage.py seed_data
```

### 6. Run Development Server
```bash
python manage.py runserver
```
Visit **http://127.0.0.1:8000/** in your browser.

---

## 🔑 Account Access & Administration

Create your own personalized student account by navigating to `/accounts/signup/`.
Follow the onboarding flow to set up your profile, institution, skill interests, and career goals.

To access the Django Admin panel:
```bash
python manage.py createsuperuser
```
Then visit **/admin/** to manage courses, modules, lessons, assessments, certificates, and opportunities.

---

## 🧪 Automated Testing

Run the comprehensive automated test suite covering all authentication, courses, video progress, notes, assessments, certificates, gamification, and security modules:

```bash
python manage.py test
```

All 90 automated tests run with 0 failures:
```
Found 90 test(s).
Creating test database for alias 'default'...
..........................................................................................
----------------------------------------------------------------------
Ran 90 tests in 22.987s

OK
```

---

## 📦 Production Deployment Architecture

SkillSphere is architected for production-grade, highly scalable deployment:

1. **Edge Hosting (Vercel Serverless)**:
   - Python 3.12 WSGI application bundled through `vercel.json`.
   - Reverse-proxy SSL terminates at edge (`SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`).
   - Production URL: `https://skillsphere-cyan.vercel.app`.

2. **Managed Database (Supabase PostgreSQL)**:
   - High-performance PostgreSQL database connected over SSL via `DATABASE_URL`.
   - Continuous connection health checks and automatic pooling (`conn_max_age=600`).

3. **Stateless Media & Document Storage**:
   - In-memory processing for avatars, converting uploaded images into compact Base64 Data URIs persisted directly in database profiles.
   - Dynamic ReportLab PDF rendering directly to HTTP response byte buffers without relying on ephemeral server disk.

4. **Static Files**:
   - Optimized WhiteNoise static file caching with gzip/Brotli compression:
   ```bash
   python manage.py collectstatic --noinput
   ```

5. **Security Hardening**:
   - Brute-force login rate limiting (5 failed attempts locks for 15 minutes).
   - Strict password strength validation via Django validators.
   - HTTPS redirect, HSTS preload (31536000s), secure cookies, and CSRF protection.
   - Custom dark glassmorphism 400, 403, 404, 500 error handlers.

---

## 📄 License
Educational Open-Source License. Developed for software engineering internships and student portfolios.
