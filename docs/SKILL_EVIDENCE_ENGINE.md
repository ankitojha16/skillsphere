# SkillSphere Skill Evidence Engine

## 1. Overview & Philosophy

The **Skill Evidence Engine** (`services/skill_evidence_engine.py`) provides transparent, auditable skill attribution for students.

### The Skill Attribution Principle
> **Taking a course alone does NOT prove professional engineering proficiency.**
> Theoretical familiarity must be substantiated through objective assessments and demonstrable, running code projects with clean version-control histories.

---

## 2. Mathematical Scoring Model

Readiness scores are computed relative to the student's chosen `CareerTrack`.

### A. Weighting by Importance

Every skill requirement in a track is categorized into one of three importance tiers:
- **Essential Core**: $W_i = 3$ (Non-negotiable foundational competence)
- **Recommended**: $W_i = 2$ (Differentiates candidates in technical rounds)
- **Bonus / Advanced**: $W_i = 1$ (Specialized tooling, cloud, or optimization)

### B. Credit Allocation by Verification Tier

For each requirement $i$, the engine evaluates the student's strongest matching evidence record:
- **Verified Evidence ($\ge 70\%$ confidence)**: $C_i = 1.0$ (100% of weight)
  - Signed platform certificate ($95\%$)
  - Verified completed/published portfolio project ($90\%$)
  - Skill assessment with score $\ge 70\%$ ($80\text{--}90\%$)
  - Passed coding challenge ($80\%$)
  - Course completion ($75\%$)
- **Improving / Self-Reported Evidence ($< 70\%$ confidence)**: $C_i = 0.4$ (40% partial credit)
  - Self-reported profile claim
  - In-progress course or planning-stage project
- **Missing / Zero Evidence**: $C_i = 0.0$ (0% credit)

### C. The Readiness Formula

The overall readiness percentage is calculated as:
$$\text{Readiness Match } (\%) = \text{round}\left( \frac{\sum_{i=1}^N (W_i \times C_i)}{\sum_{i=1}^N W_i} \times 100 \right)$$

---

## 3. Evidence Categories & Confidence Tiers

| Evidence Type | Verified Flag | Confidence Rating | Backing Platform Artifact |
| :--- | :--- | :--- | :--- |
| `certificate_earned` | `True` | **95%** | Signed digital certificate with unique ID (`SS-CERT-YYYY-...`) |
| `project_built` | `True` | **90%** | Project in `completed` or `published` workflow status |
| `assessment_score` | `True` | **80% - 90%** | `AssessmentAttempt` score $\ge 70\%$ |
| `coding_submission`| `True` | **80%** | `ChallengeSubmission` with status `'Accepted'` |
| `course_completion`| `True` | **75%** | `CourseCompletion` with `is_completed=True` |
| `self_reported` | `False` | **35%** | Student profile stated interest / skill claim |

---

## 4. Transparent Explanation Output

Every gap report includes an explicit human-readable and audit-ready explanation:

```text
"Your readiness score of 67% is computed across 6 benchmark requirements for Backend Developer.
Essential skills carry 3× weight, recommended skills carry 2× weight, and bonus skills carry 1× weight.
Verified platform evidence (certificates, completed projects, passed assessments) earns 100% of the
allocated skill weight, while self-reported or in-progress skills contribute 40%. Completed courses
demonstrate theoretical familiarity, but full professional readiness requires building demonstrable projects."
```
