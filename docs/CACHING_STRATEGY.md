# SkillSphere Distributed Caching & Cache Safety Strategy

## 1. Multi-Tier Caching Architecture

SkillSphere implements a 3-tier caching topology:
1. **Edge CDN Layer**: Static assets, stylesheets, scripts, fonts, and images cached for 1 year immutable (`public, max-age=31536000, immutable`).
2. **Distributed Redis Layer**: Shared across all application instances using `FaultTolerantRedisCache` with automatic fallback to `LocMemCache`.
3. **Application Query & Session Cache**: Cached database session backend (`django.contrib.sessions.backends.cached_db`).

---

## 2. Public vs. Private Cache Isolation

| Scope | Cached Resources | Cache Headers | Key Prefix / Structure |
|---|---|---|---|
| **Public** | Course catalogue, categories, search suggestions, public profiles, sitemap | `Cache-Control: public, max-age=0, must-revalidate` | `skillsphere_cat_v{ver}_{cat}_{deg}_{diff}_{sort}_{q}_p{page}` |
| **Private** | Learner dashboard, lesson progress, certificates, notes, resumes, assessments | `Cache-Control: private, no-cache, no-store, must-revalidate, max-age=0` | User-scoped only (e.g. `cert_pdf_{id}_v{ver}`, `user_prog_{user_id}_{course_id}`) |

> [!CAUTION]
> Private data, session credentials, assessment answers, and personalized dashboards are **NEVER** placed in shared public cache keys.

---

## 3. Parameterized Catalogue Caching with $O(1)$ Atomic Version Invalidation

### The Problem with Wildcard Invalidation
When courses, categories, or lessons change, invalidating hundreds of combinations of filtered, sorted, and paginated cache keys via Redis `KEYS skillsphere_cat_*` causes server-wide stop-the-world latency spikes ($O(N)$ scanning).

### The Solution: Global Monotonic Versioning
Every catalogue cache key embeds an atomic version counter:
```python
cache_key = f"skillsphere_cat_v{version}_{category}_{degree}_{difficulty}_{sort_by}_{query_hash}_p{page}"
```
When an instructor creates, updates, or deletes a course, category, or lesson, an atomic post-commit signal executes:
```python
cache.set('skillsphere_catalogue_version', curr_version + 1)
```
- **Cost**: Exactly 1 atomic Redis write ($O(1)$).
- **Result**: Instantly renders all hundreds of existing variant cache keys obsolete without deleting them iteratively. Redis automatically evicts stale keys via TTL or LRU policy.

---

## 4. PDF Document Cache Versioning & Safety

### Certificate PDFs
- **Key Pattern**: `cert_pdf_{cert_id}_v{updated_at_timestamp}`
- **Security**: Strict ownership checks before returning cached bytes. If an administrator revokes a certificate or a student updates their recipient name, `updated_at` increments, guaranteeing zero delivery of stale or revoked certificates.

### Resume PDFs
- **Key Pattern**: `resume_pdf_{resume_id}_v{updated_at_timestamp}`
- **Security**: Resume downloads require authentication and verify `resume.user == request.user`. Document versioning ensures changes made in the ATS resume editor immediately invalidate previous PDF builds.
