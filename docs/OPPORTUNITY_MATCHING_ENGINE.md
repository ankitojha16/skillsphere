# SkillSphere Opportunity Hub — Intelligent Skill Matching Engine

## 1. Engine Mission & Principles

The **Skill Matching Engine** (`services/opportunity_matcher.py`) computes a mathematically rigorous, transparent $0\text{--}100\%$ compatibility score between a candidate and an opportunity listing.

### Core Tenets:
1. **Verified Evidence Only**: The engine strictly queries `StudentSkillEvidence` records validated through platform activities (signed course certificates, passed assessments, and accepted challenge submissions). Self-reported claims are never passed off as verified evidence.
2. **Transparent Rationale**: Every match score is accompanied by a plain-language summary detailing which required skills were satisfied, which are missing, and what platform evidence backed each match.
3. **No Milestone Penalties**: Students are never penalized or automatically rejected simply because they have incomplete learning roadmap milestones.

---

## 2. Mathematical Scoring Formula

$$\text{Total Match Score} = \min\left(100, \text{round}\left(S_{\text{req}} + S_{\text{pref}} + S_{\text{track}}\right)\right)$$

### 2.1 Required Skills Weight ($70\%$ max)

$$S_{\text{req}} = \left(\frac{N_{\text{matched\_required}}}{N_{\text{total\_required}}}\right) \times 70.0$$

- If an opportunity specifies zero required skills, $S_{\text{req}} = 70.0$.
- Each required skill is normalized (`SkillEvidenceEngine.normalize_skill_name`) and matched against the student's highest-confidence verified evidence record.

### 2.2 Preferred / Bonus Skills Weight ($20\%$ max)

$$S_{\text{pref}} = \left(\frac{N_{\text{matched\_preferred}}}{N_{\text{total\_preferred}}}\right) \times 20.0$$

- If no preferred skills are listed, full or proportional credit is awarded based on required skill coverage.

### 2.3 Career Track Alignment ($10\%$ max)

$$S_{\text{track}} = \begin{cases} 
10 & \text{if opportunity domain matches student's primary } \texttt{CareerTrack} \\
4 & \text{cross-discipline foundational technical alignment} \\
0 & \text{no target career goal selected}
\end{cases}$$

---

## 3. Match Tiers & UI Indicators

| Score Range | Tier Level | Badge Color | User Guidance |
|---|---|---|---|
| **$75\% - 100\%$** | **High Match** | Emerald | Candidate possesses core verified competencies; prime candidate for immediate application. |
| **$45\% - 74\%$** | **Moderate Match** | Violet | Candidate covers major requirements; minor gaps in secondary or preferred tools. |
| **$0\% - 44\%$** | **Growth Opportunity** | Amber | Significant skill gaps identified; actionable course and project recommendations provided. |

---

## 4. Auditable Match Evaluation Output

```json
{
  "match_percentage": 85,
  "match_level": "High Match",
  "badge_color": "emerald",
  "required_skills_summary": {
    "matched": [
      {
        "skill": "Python",
        "evidence": "Verified Certificate: Python Core Mastery",
        "evidence_type": "certificate_earned",
        "confidence": 95
      },
      {
        "skill": "Django",
        "evidence": "Published Project: E-Commerce API",
        "evidence_type": "project_published",
        "confidence": 90
      }
    ],
    "missing": ["PostgreSQL"],
    "match_ratio": 0.67,
    "total_required": 3
  },
  "preferred_skills_summary": {
    "matched": [
      {
        "skill": "Docker",
        "evidence": "Passed Assessment: DevOps Foundations (Score: 88%)",
        "evidence_type": "assessment_passed",
        "confidence": 88
      }
    ],
    "missing": ["Redis"],
    "match_ratio": 0.5,
    "total_preferred": 2
  },
  "track_alignment": {
    "is_aligned": true,
    "primary_track": "Python Backend Developer",
    "bonus_points": 10
  },
  "eligibility_status": {
    "is_eligible": true,
    "minor_restricted": false,
    "notes": []
  },
  "summary_explanation": "You have verified platform evidence for 2 required skill(s) (Python, Django). Missing verified evidence for: PostgreSQL. Bonus matches for preferred capabilities: Docker. Strong alignment with your primary career goal (Python Backend Developer)."
}
```
