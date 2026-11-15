# SkillSphere Feature Decisions: Keep, Improve, Merge, Hide & Remove

**Guiding Rule**: **LESS BUT BETTER**  
**Core Journey Framework**: **LEARN → PRACTICE → BUILD → SHOWCASE → GROW**  
**Date**: November 2026  

---

## 1. Decision Classifications Overview

Every capability across SkillSphere is categorized into one of five definitive product actions:

- **KEEP**: Essential, reliable, and foundational.
- **IMPROVE**: Highly valuable but requires UI cleanup, better integration, or performance polish.
- **MERGE**: High value, but duplicates another feature; consolidate into a single cohesive interface.
- **HIDE**: Useful for secondary workflows, but should NOT clutter the primary navigation sidebar.
- **REMOVE / DEPRECATE**: Low student value, high maintenance burden, or distracting from real learning outcomes.

---

## 2. Granular Decision Ledger

| Feature / Component | Category Pillar | Decision | Justification & Architectural Strategy |
| :--- | :---: | :---: | :--- |
| **Student Dashboard** | Home | **KEEP** | Central daily landing page with learning streak, enrolled courses, and onboarding launchpad. |
| **Course Catalog (69 Courses)** | Learn | **KEEP** | Complete accredited library of engineering, cloud, AI, and cybersecurity courses. |
| **LMS Lesson Engine (1,104 Lessons)**| Learn | **KEEP** | Core educational delivery. Robust markdown, code snippets, progress tracking. |
| **My Learning (Enrolled Courses)** | Learn | **KEEP** | Quick access to in-progress curricula and bookmarks. |
| **Learning Roadmaps** | Learn | **MERGE** | Merge disjointed `/roadmaps/` and `/career-studio/roadmap/` into one authoritative roadmap view under Learn. |
| **AI Study Planner** | Learn / AI | **MERGE** | Merge standalone `/workspace/study-planner/` into the Unified AI Assistant under **Study Mode** (`/assistant/?mode=study`). |
| **Flashcards (SM-2 Spaced Rep)** | Learn | **HIDE** | Remove from main sidebar. Keep accessible inside individual courses and lesson review tools. |
| **Skill Assessments** | Practice | **KEEP** | Structured quizzes, question banks, and objective score calculation. |
| **Code Challenges (Judge)** | Practice | **IMPROVE**| Integrate directly under the **Practice** pillar alongside assessments with clean difficulty filters. |
| **Mock Interview Simulator** | Practice / AI | **MERGE** | Consolidate `/mock-interview/` and `/resume-builder/mock-interview/` into the Unified AI Assistant under **Interview Prep Mode** (`/assistant/?mode=interview`). |
| **1v1 Ranked Code Arena** | Gamification | **REMOVE** | Decorative competitive feature with negligible student completion; maintenance distraction. |
| **Competitive Leagues** | Gamification | **HIDE** | Low-frequency weekly leaderboard. Accessible via user profile achievements; removed from primary sidebar. |
| **Project Portfolio Studio** | Build | **IMPROVE**| Centralize at `/portfolio/`. 5-stage pipeline with private-by-default safeguards for student IP. |
| **Project Generator** | Build | **MERGE** | Integrate as an "Inspiration & Generator" tab directly within the Projects Studio. |
| **Pair Programming Lounge** | Collaboration | **HIDE** | Niche live whiteboard feature. Accessible via direct project collaboration links rather than clogging the main sidebar. |
| **Curated Career Tracks (11 Paths)** | Grow | **KEEP** | Industry salary benchmarks, market demand ratings, and essential skills for engineering careers. |
| **Skill Evidence Engine** | Grow | **KEEP** | Transparent, mathematically grounded evidence linking real code and course completions to skills. |
| **Skill Gap Analyzer** | Grow | **IMPROVE**| Streamline visualization and direct students immediately to missing courses and roadmap milestones. |
| **Smart ATS Resume Studio** | Showcase | **KEEP** | Verified platform artifacts, ATS scoring, Platypus PDF compilation, and version control. |
| **Certificates Center** | Showcase | **KEEP** | Cryptographically verifiable credentials (SHA-256) with QR verification. |
| **Opportunity Hub** | Grow | **IMPROVE**| Real, verified partner listings with live freshness indicators and auto-expiry state machine. |
| **Application Tracker** | Grow | **MERGE** | Consolidate duplicate `/careers/tracker/` and `/opportunities/applications/` into one canonical application pipeline. |
| **Recruiter Portal & Moderation** | Grow / Staff | **KEEP** | Protected recruiter posting and staff abuse moderation (`/opportunities/moderation/`). |
| **Student Workspace Hub** | Productivity | **IMPROVE**| Keep as dedicated personal hub (`/workspace/`) for daily planner, calendar, notes, and focus timer. |
| **Study Lounge & Pomodoro (Dashboard)**| Productivity | **MERGE** | Consolidate into `/workspace/focus/`. Remove duplicate dashboard study-lounge sidebar link. |
| **Personal Notes & Bookmarks** | Productivity | **KEEP** | Markdown scratchpad and resource bookmarks organized by tags inside Workspace. |
| **Student Data Export (JSON)** | Privacy | **KEEP** | Full portable GDPR/FERPA compliant archive at `/accounts/export-data/`. |

---

## 3. Summary of Sidebar Streamlining

### Before (28 Cluttered Links):
- Dashboard, Workspace, Explore Courses, My Learning, Flashcards, Study Lounge & Pomodoro, AI Assistant, Learning Roadmap, Code Challenges, Skill Assessment, AI Voice Interview, Mock Interview, Project Generator, Career Studio, Career Hub, Job Tracker & AI Co-Pilot, Resume Builder, Portfolio, Opportunities, Recruiter Talent, Community, Collaboration, Pair Lounge & Board, Events & Hackathons, Certificates, Verify Credential, 1v1 Code Arena, Competitive Leagues, Achievements.

### After (5 Clean Core Pillars):
1. **Home** (`/dashboard/`)
2. **Learn** (`/courses/`) — Catalog, My Learning, Roadmap, AI Study Assistant
3. **Practice** (`/skill-assessment/`) — Assessments, Code Challenges, Mock Interview
4. **Projects** (`/portfolio/`) — Project Workspace, Portfolio Showcase, Project Generator
5. **Career** (`/career-studio/`) — Career Paths, Skill Gap Analyzer, Resume Studio, Opportunities, Application Tracker

*Secondary Utilities (Workspace, Certificates, Settings, Staff Moderation) are cleanly housed in the header/footer.*
