# SkillSphere Smart Resume System

## 1. Overview & Zero-Fabrication Policy

The **Smart Resume System** (`services/resume_service.py`) automates tech resume creation backed strictly by authentic student achievements.

### Strict Zero-Fabrication Policy
- **No Unearned GPA**: SkillSphere never generates fake grade point averages. If a student has not entered academic metrics, the field is cleanly omitted.
- **No Phantom Work History**: The generator never injects fictitious companies, fabricated internship titles, or unverified claims.
- **Verified Platform Badges**: Certifications and projects shown on the resume map directly to signed verification records (`Certificate` IDs and `ProjectIdea` references).

---

## 2. Core Capabilities

### A. Dynamic Section Reordering
Students can customize the sequence of their resume sections to highlight their strongest assets (e.g., prioritizing *Featured Projects* over *Work Experience* for fresh graduates):
- Supported sections: `summary`, `skills`, `projects`, `education`, `certifications`, `experience`.
- Reordering is saved in `Resume.section_order` and rendered dynamically both in the web preview and in the compiled PDF.

### B. Immutable Version Snapshots
Students can maintain multiple tailored versions (e.g., Frontend Specialist vs Full-Stack Generalist) using `ResumeVersion`. Each version captures:
- `version_number`
- `version_title`
- `template`
- `snapshot_data` (frozen JSON snapshot of contact, skills, projects, and education)

### C. ATS-Compliant PDF Generation with ReportLab
The PDF compiler in `services/pdf_service.py` outputs clean vector PDFs with selectable text:
- Single-column flow avoiding complex tables that trip automated Applicant Tracking Systems (ATS).
- Standard section headers (e.g. `TECHNICAL SKILLS`, `FEATURED PROJECTS`, `EDUCATION`).
- Template styling palettes: `ats` (slate), `modern` (indigo), `fresher` (emerald), and `minimal` (zinc).
- Deterministic document caching using SHA-256 fingerprinting.
