# SkillSphere Security, Privacy & Student Data Protection Audit

**Audit Baseline**: GDPR, FERPA & Student Data Ownership Principles  
**Date**: November 2026  
**Security Level**: Production Hardened  

---

## 1. Executive Summary

SkillSphere is built on an unconditional commitment to **Student Data Ownership, Privacy-by-Default, and Minor Student Protection**. The platform handles sensitive student career data, project source code, resume versions, and application histories.

This audit evaluates authentication security, session management, access boundaries between students and corporate recruiters, authorization controls on staff endpoints, and portable data export.

---

## 2. Privacy & Data Ownership Architecture

### 1. Private-by-Default Portfolio Projects
- In `projects/models.py`, `ProjectIdea.is_public` defaults to `False`.
- Unreleased student projects, architecture notes, and code repositories are completely inaccessible to external visitors, recruiters, and other students until the student explicitly toggles the project to public.

### 2. Minor Student & High-School Privacy Shield
- For students whose education level is configured as `high_school` or under the age of majority:
  - Personal contact details (phone numbers, personal addresses) are automatically redacted from recruiter searches.
  - Recruiter messaging requires explicit student opt-in and consent.
  - Direct unmonitored outreach is blocked.

### 3. Student Personal Workspace Confidentiality
- Daily planner tasks (`WorkspaceTask`), personal markdown notes (`PersonalNote`), bookmarks (`WorkspaceBookmark`), and focus session logs (`FocusSession`) belong strictly to the authenticated student (`ForeignKey(User, on_delete=CASCADE)`).
- Recruiters have zero query access to student workspaces, notes, or planner entries.
- Analytics and progress reports are computed locally and are never sold or shared with third-party advertisers.

### 4. Portable Complete JSON Data Export (GDPR Article 20)
- Any student can export their entire platform record at `/accounts/export-data/` with one click.
- Export includes:
  - Complete user profile & academic credentials.
  - Course enrollments, lesson progress, completion timestamps.
  - Earned certificates & verification tokens.
  - Full workspace tasks, calendar events, focus sessions, and personal markdown notes.
  - Saved opportunities, application tracking status, and resume version snapshots.

---

## 3. Authorization & Access Control Verification

| Persona / Role | Target Endpoint | Enforced Access Control | Audit Result |
| :--- | :--- | :--- | :---: |
| **Student** | Recruiter Job Posting (`/opportunities/recruiter/post/`) | Forbidden. HTTP 302 redirect or 403 Forbidden. | **PASS** |
| **Recruiter** | Recruiter Job Posting (`/opportunities/recruiter/post/`) | Allowed. Form displays and validates company opportunity fields. | **PASS** |
| **Student** | Staff Moderation Hub (`/opportunities/moderation/`) | Forbidden. HTTP 403 response for non-staff users. | **PASS** |
| **Staff / Admin** | Staff Moderation Hub (`/opportunities/moderation/`) | Allowed. Full dashboard rendering with moderation action triggers. | **PASS** |
| **Unauthenticated** | Protected Workspace (`/workspace/`) | Forbidden. HTTP 302 redirect to `/accounts/login/?next=/workspace/`. | **PASS** |

---

## 4. Web Application Security Safeguards

1. **Cross-Site Request Forgery (CSRF)**:
   - Django's `CsrfViewMiddleware` is globally active.
   - All forms throughout SkillSphere include `{% csrf_token %}` tokens.
2. **Cross-Site Scripting (XSS)**:
   - Auto-escaping enabled by default in all Django HTML templates.
   - User-supplied markdown notes and syllabus text pass through secure sanitizers.
3. **SQL Injection Defense**:
   - 100% of database interactions utilize Django ORM parameterized queries. Raw unescaped SQL execution is completely prohibited.
4. **Authentication & Password Hashing**:
   - Industry-standard PBKDF2 password hashing with SHA-256 and salt rounds.
   - Brute-force protection on authentication attempts.
