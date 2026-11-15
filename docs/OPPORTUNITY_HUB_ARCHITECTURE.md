# SkillSphere Opportunity Hub — Architecture Specification

## 1. Overview & Vision

The **SkillSphere Opportunity Hub** bridges verified student learning and project accomplishments with legitimate, vetted career pathways. Rather than acting as a static job bulletin board or an unvetted scraping aggregate, the Opportunity Hub functions as an intelligent career gateway grounded directly in SkillSphere's **Skill Evidence Engine**, **Career Studio**, and **ATS Resume Engine**.

```
+-----------------------------------------------------------------------------------+
|                            STUDENT CAREER LIFECYCLE                               |
+-----------------------------------------------------------------------------------+
|  1. Learn & Build       2. Demonstrate           3. Match & Discover  4. Track &  |
|  Courses, Challenges,   Skill Evidence Engine,   Opportunity Matcher  Prepare     |
|  Certificates, Goals    Portfolio Projects       Transparent 0-100%   8-Stage     |
|                         Resume Versions          Eligibility, Types   Pipeline    |
+-----------------------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------------------+
|                            RECRUITER & PARTNER PORTAL                             |
|  - Verified Partner Profiles (OpportunityOrganization)                            |
|  - Listing Publication & Stage Progression Management                             |
|  - Privacy Shielding: Zero raw PII exposure; Minor-Safe Protections               |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Components

### 2.1 Domain Models (`opportunities/models.py`)

1. **`OpportunityOrganization`**:
   - Represents verified employers, open-source foundations, academic institutions, and student organizations.
   - Enforces brand integrity via the `is_verified` partner badge and official website URL.

2. **`Opportunity`**:
   - Central listing entity supporting 8 distinct opportunity types:
     - `internship`: Vetted corporate or open-source internships (e.g., GSoC, Outreachy).
     - `job`: Full-time entry-level and junior software engineering roles.
     - `remote`: Distributed positions with explicit timezone and work arrangement parameters.
     - `hackathon`: Collaborative build events with prize pools (e.g., Imagine Cup).
     - `competition`: Algorithmic and data science contests (e.g., NASA Space Apps).
     - `scholarship`: Need- and merit-based academic grants (e.g., Generation Google Scholarship).
     - `challenge`: Practical student challenges with open licensing.
     - `mentorship`: Structured one-on-one guidance initiatives (e.g., LFX Mentorship).
   - Relational attributes: `organization_ref`, `posted_by`, `required_skills`, `preferred_skills`, `eligibility`, `funding_amount`, `min_age`, `is_minor_safe`, `deadline`, and `is_archived`.

3. **`SavedOpportunity` (Pipeline Tracker)**:
   - Tracks a student's personal progression through 8 standardized stages:
     `saved` -> `preparing` -> `applied` -> `assessment` -> `interview` -> `selected` -> `rejected` -> `withdrawn`.
   - Links the exact immutable `ResumeVersion` snapshot submitted.
   - Records private follow-up dates and external portal reference identifiers.

4. **`ApplicationStatusHistory`**:
   - Immutable audit trail capturing every stage transition, timestamp, actor (`changed_by`), and contextual transition notes.

5. **`OpportunityReport`**:
   - Student-driven listing integrity mechanism allowing reports on fraudulent listings, broken URLs, expired programs, or minor safety violations.

6. **`CandidateShortlist` & `InterviewInvitation`**:
   - Recruiter candidate discovery pipeline with hourly rate limiting and minor safety shielding.

---

## 3. Services & Integration Architecture

| Service Component | Module | Responsibilities |
|---|---|---|
| **Intelligent Matcher** | `services/opportunity_matcher.py` | Calculates transparent $0\text{--}100\%$ match scores against verified student evidence (`StudentSkillEvidence`) and active career goals. |
| **Evidence Engine** | `services/skill_evidence_engine.py` | Audits course certificates, passed assessments, and accepted challenge submissions. |
| **Interview Prep** | `services/interview_prep_service.py` | Generates role-specific technical deep-dives, STAR behavioral scenarios, and interactive response evaluations with offline fallback. |
| **Notification Engine** | `notifications/models.py` | Dispatches automated notifications for stage updates, interview invitations, and follow-up reminders. |

---

## 4. Security & Minor Protection Architecture

1. **Role-Based Access Control**:
   - Recruiters are strictly gated by `@recruiter_required`, verifying `profile.role == 'recruiter'`, `is_staff`, or `is_superuser`.
   - Ownership isolation prevents recruiters from viewing or editing listings owned by other organizations.

2. **Minor Student Safety Guardrails**:
   - High school students (`education_level='high_school'`) are automatically filtered out from viewing or applying to adult-only roles (`min_age > 17` or `is_minor_safe=False`).
   - Direct, unmoderated recruiter invitations to minor students are blocked at the controller layer with an HTTP 403 safety rejection.

3. **Privacy by Default**:
   - Personal contact information (email, phone, physical address) is never exposed to recruiters in candidate dossiers or applicant review tables.
   - Communications occur through official platform stage transitions and invitations.
