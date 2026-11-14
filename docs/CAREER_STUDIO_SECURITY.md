# SkillSphere Career Studio Security & Privacy

## 1. Threat Modeling & Principles

Career Studio handles student educational records, project repositories, resumes, and career goals. Strict security policies are enforced across all layers.

---

## 2. Student Data Protection & Privacy

1. **Private by Default Portfolio Projects**:
   - `ProjectIdea.is_public` defaults strictly to `False`.
   - Projects cannot be viewed, indexed, or shared without explicit user opt-in.
   - Project IDs are augmented with non-sequential public references (`project_ref = SP-XXXXXXXX`) to prevent integer-enumeration scraping attacks.

2. **PII Masking**:
   - Student email addresses and contact phone numbers are never included in public project cards or unauthenticated endpoints.
   - Public resume views omit personal phone numbers unless verified student consent is granted.

3. **Multi-Tenant User Isolation**:
   - All write and read operations in `views_studio.py` enforce `user=request.user` query filtering.
   - Direct object references (e.g. `milestone_id`, `project_id`, `resume_id`) validate that the requesting user owns the parent entity.

---

## 3. Defense-in-Depth Mechanisms

| Threat | Guard Mechanism | Implementation Location |
| :--- | :--- | :--- |
| **Cross-Site Request Forgery (CSRF)** | All state-modifying requests require valid Django CSRF tokens. AJAX endpoints transmit tokens via `X-CSRFToken` request headers. | `views_studio.py`, `templates/careers/studio/*.html` |
| **SQL Injection** | Exclusively uses Django ORM parameterized queries. Raw SQL string formatting is strictly prohibited. | `services/skill_evidence_engine.py`, `services/resume_service.py` |
| **Cross-Site Scripting (XSS)** | Django auto-escaping is active on all templates. JSON data embedded in script tags is encoded safely. | `templates/careers/studio/*.html` |
| **API Denial of Service** | Sliding window rate limiting on AI mentorship queries (max 12 requests/minute). | `services/career_ai_assistant.py` |
| **Downstream LLM Failures** | In-memory and cached circuit breakers trip on repeated timeouts, fast-failing to deterministic fallback without blocking worker threads. | `services/resilience.py`, `services/ai_service.py` |
