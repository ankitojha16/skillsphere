# SkillSphere Opportunity Hub — Recruiter Portal Integration

## 1. Overview & Recruiter Capabilities

The **Recruiter Integration Suite** empowers authorized hiring managers, talent partners, and educational sponsors to manage listings, discover candidates based on verified skills, and progress applicants through recruitment stages while rigorously respecting student privacy and minor-safety policies.

```
+----------------------------------------------------------------------------------+
|                              RECRUITER WORKFLOW                                  |
+----------------------------------------------------------------------------------+
|  1. Publish Listing      2. Review Applicants    3. Update Candidate Stage       |
|  /opportunities/recruiter/post/   Verified Skills, Match %,   Advance stage with automatic |
|  Organization ownership  Shielded Contact Info   student notifications           |
+----------------------------------------------------------------------------------+
```

---

## 2. Authorization & Permission Model

Access to all recruiter management endpoints is enforced by the `@recruiter_required` decorator (`accounts/decorators.py`):

```python
is_authorized = (
    request.user.is_staff or
    request.user.is_superuser or
    (hasattr(request.user, 'profile') and request.user.profile.role == 'recruiter')
)
```

- **Anonymous Users**: Redirected to `/accounts/login/` (or HTTP 401 for JSON API requests).
- **Non-Recruiter Students**: Redirected to `/dashboard/` with an informational warning (or HTTP 403 for API requests).
- **Authorized Recruiters**: Granted access strictly scoped to their assigned listings and candidate applicants.

---

## 3. Organization Ownership Isolation

To prevent cross-tenant data leakage between competing hiring organizations:
- Opportunities record `posted_by = request.user` and optionally link `organization_ref`.
- When accessing the edit route (`/opportunities/recruiter/listings/<pk>/edit/`) or applicants route (`/opportunities/recruiter/listings/<pk>/applicants/`), the controller validates:

```python
if not (request.user.is_staff or request.user.is_superuser or opp.posted_by == request.user):
    return HttpResponseForbidden("Permission denied to modify or view this listing.")
```

---

## 4. Student Privacy & Contact Shielding

1. **Private by Default**:
   - Recruiters reviewing applicants at `/opportunities/recruiter/listings/<pk>/applicants/` see candidate usernames, educational level, demonstrated match percentages, and submitted `ResumeVersion` snapshots.
   - Raw personal email addresses and telephone numbers are **shielded by default** to prevent unsolicited scraping and harassment.

2. **Minor Protection Safeguards**:
   - High school and minor students (`education_level='high_school'`) are protected from direct unmoderated recruiter messages.
   - If a recruiter attempts to dispatch a direct interview invitation to a minor student via `/talent/candidate/<username>/invite/`, the system rejects the request:

```python
if candidate_profile and candidate_profile.education_level == 'high_school':
    return JsonResponse({
        'status': 'error',
        'message': 'Direct recruiter invitations to minor students are prohibited by safety policy.'
    }, status=403)
```

---

## 5. Recruiter Rate Limiting

To eliminate recruitment spam and automated bot scraping:
- Direct candidate interview invitations are rate-limited to **15 requests per hour** per recruiter using distributed cache tracking (`recruiter_invitations_<user_id>`).
- Exceeding the threshold triggers an HTTP 429 Too Many Requests response.
