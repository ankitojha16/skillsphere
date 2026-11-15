# SkillSphere Opportunity Hub — Application Tracker Specification

## 1. Overview

The **Application Tracker** (`/opportunities/my-applications/`) provides students with a visual Kanban pipeline to organize their internship, job, scholarship, and hackathon applications from initial bookmark through final offer.

---

## 2. The 8 Pipeline Stages

Students categorize opportunities into eight standardized lifecycle phases:

```
[ 1. Saved ] ──> [ 2. Preparing ] ──> [ 3. Applied ] ──> [ 4. Assessment ]
                                                                   │
                                                                   ▼
[ 8. Withdrawn ] <── [ 7. Rejected ] <── [ 6. Selected 🎉 ] <── [ 5. Interview ]
```

1. **`saved` (Saved / Wishlist)**:
   - Initial bookmarking stage. Allows students to evaluate requirements and run skill matching before starting an application.
2. **`preparing` (Preparing Application)**:
   - Active drafting phase: tailoring resumes with the **ATS Resume Studio**, preparing portfolio project links, and requesting recommendations.
3. **`applied` (Applied)**:
   - Formal submission completed. Records application timestamp (`applied_at`), frozen `ResumeVersion`, and confirmation tracking codes.
4. **`assessment` (Assessment / Coding Test)**:
   - Online assessment, take-home challenge, or Hackerrank test in progress.
5. **`interview` (Interview)**:
   - Screening, technical round, or hiring manager interview scheduled. Links directly to **AI Interview Prep**.
6. **`selected` (Selected / Offer Extended 🎉)**:
   - Successful outcome or formal offer received.
7. **`rejected` (Rejected / Not Selected)**:
   - Archived application for historical reflection and post-mortem learning.
8. **`withdrawn` (Withdrawn)**:
   - Candidate proactively withdrew from the selection process.

---

## 3. Resume Version Snapshot Linkage

To ensure absolute auditability, applications link directly to an immutable `ResumeVersion` rather than a live, mutable resume.
- When an application record is created or updated, the student selects their tailored `ResumeVersion` (e.g., `Resume v2 - Acme Cloud Backend`).
- If the student later updates their master resume in the Resume Studio, the application record preserves the exact snapshot submitted to that specific employer.

---

## 4. Duplicate Prevention & Integrity

```python
class SavedOpportunity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_opportunities')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='saves')
    ...
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'opportunity'], name='unique_user_saved_opportunity')
        ]
```

- Database-level `UniqueConstraint` prevents a student from creating multiple competing application records for the same opportunity.
- Re-submitting from the opportunity detail page smoothly updates the existing application record rather than duplicating entries.

---

## 5. Audit Trail: `ApplicationStatusHistory`

Every stage change generates an immutable audit record:

| Field | Description |
|---|---|
| `application` | ForeignKey linking to the `SavedOpportunity`. |
| `from_status` | Pre-transition status (e.g., `applied`). |
| `to_status` | Post-transition status (e.g., `interview`). |
| `changed_by` | User initiating change (student or authorized recruiter). |
| `notes` | Contextual notes or recruiter comments. |
| `created_at` | Timestamp of the event. |

---

## 6. Follow-Up Reminders

- Students can assign a `follow_up_date` to any application.
- The dashboard highlights upcoming actions due within the next 7 days in an alert banner, eliminating missed deadlines without sending spam notifications.
