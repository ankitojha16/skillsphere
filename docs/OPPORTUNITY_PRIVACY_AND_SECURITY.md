# SkillSphere Opportunity Hub — Privacy, Student Safety & Security

## 1. Safety & Privacy Principles

Student safety and data privacy are paramount in SkillSphere. The Opportunity Hub enforces a **private-by-default** posture across all interactions:

1. **Zero Unmoderated Minor Contact**:
   - High school and minor students cannot receive direct, unmoderated outreach from recruiters.
   - Minor students apply exclusively through official, public, verified opportunities.

2. **Age-Appropriate Filtering**:
   - Adult-only roles (`min_age > 17` or `is_minor_safe=False`) are automatically suppressed from search results, discovery pages, and detail views for minor accounts.

3. **Zero Fabrication Policy**:
   - SkillSphere never scrapes websites against their terms of service or fabricates opportunity listings.
   - All opportunities stem from verified partner organizations (`OpportunityOrganization.is_verified=True`) or authenticated recruiters with administrative review.

4. **Contact Shielding & PII Protection**:
   - Personal phone numbers and raw email addresses are strictly shielded.
   - Recruiters interface with candidates via verified platform stage updates, official meeting links, and structured notifications.

---

## 2. Listing Reporting & Content Moderation

Students have access to an integrated listing reporting flow on every opportunity detail page (`/opportunities/<pk>/report/`):

### Supported Reporting Categories:
- **`scam`**: Fraudulent or suspicious listings attempting to collect unauthorized fees.
- **`expired`**: Opportunities where the external deadline has expired or the portal is closed.
- **`broken_link`**: Dead or invalid external application URLs.
- **`inaccurate_info`**: Misleading compensation, location, or prerequisite descriptions.
- **`minor_safety`**: Content deemed unsafe or inappropriate for secondary school students.
- **`other`**: General moderation inquiries.

Reports populate the `OpportunityReport` model with status tracking (`pending`, `investigating`, `resolved`, `dismissed`) for staff audit and action.

---

## 3. Data Ownership & Private Resume Sharing

- **Resume Versioning**: When a student applies, only the specific `ResumeVersion` selected by the student is shared with that specific recruiter.
- **Student Sovereignty**: Students retain total ownership of their application data. They can withdraw applications (`withdrawn` status) or delete tracked records at any time.
- **Deletion Safeguards**: Removing an application cascade-cleans private notes and reminders while preserving database referential integrity.
