# SkillSphere Phase 18.2 — Progressive Distributed Load Benchmarks

## 1. Executive Summary & Benchmark Scope

During Phase 18.2, the SkillSphere application was subjected to progressive, multi-tier load testing using Locust (version `2.34.0`) to establish measured throughput, latency percentiles, and error rate boundaries.

Testing was conducted against a live Gunicorn instance running 4 worker processes and 4 threads per worker (16 concurrent request threads), backed by live PostgreSQL and Redis.

### Student Cohort Simulation Model
The load script ([`load_tests/locustfile_phase18.py`](file:///Users/ankitkumar/Desktop/wealthtrack/AnkitPortfolio/skill%20sphare/load_tests/locustfile_phase18.py)) realistically simulates 3 distinct student personas:
1. **Catalog Discovery Students (50% weight)**: Course browsing, API search autocomplete, syllabus detail views, and liveness pings.
2. **Active Enrolled Learners (35% weight)**: Dashboard loading, lesson views, quiz intro loading, and career roadmap exploration.
3. **Heavy Resource Students (15% weight)**: Certificate verification center, public cryptographic certificate verification, and deep readiness probes.

---

## 2. Multi-Tier Benchmark Results Summary

| Metric | Tier 1: 50 CCU | Tier 2: 100 CCU | Tier 3: 250 CCU | Tier 4: 500 CCU | Tier 5: 1,000 CCU |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Duration** | 30s | 30s | 30s | 30s | 30s |
| **Spawn Rate** | 10 users/s | 20 users/s | 50 users/s | 100 users/s | 200 users/s |
| **Total Requests** | 305 | 617 | 1,550 | 2,999 | **5,817** |
| **Total Failures** | **0** | **0** | **0** | **0** | **0** |
| **Failure Rate** | **0.00%** | **0.00%** | **0.00%** | **0.00%** | **0.00%** |
| **Throughput (RPS)**| **10.21** | **20.70** | **51.84** | **100.28** | **194.65** |
| **Median (p50)** | **16 ms** | **11 ms** | **8 ms** | **130 ms** | **180 ms** |
| **75th Percentile** | 170 ms | 170 ms | 170 ms | 230 ms | 470 ms |
| **90th Percentile** | 210 ms | 200 ms | 200 ms | 540 ms | 990 ms |
| **95th Percentile** | 460 ms | 210 ms | 230 ms | 950 ms | 1,500 ms |
| **99th Percentile** | 690 ms | 390 ms | 430 ms | 1,500 ms | 2,400 ms |
| **Max Latency** | 830 ms | 570 ms | 500 ms | 2,467 ms | 3,126 ms |
| **HTTP 429 Count** | 0 | 0 | 0 | 0 | 0 |
| **HTTP 5xx Count** | 0 | 0 | 0 | 0 | 0 |

---

## 3. Detailed Latency Breakdown by Endpoint (Tier 5: 1,000 CCU)

Under maximum 1,000 CCU stress load, the application sustained **194.65 requests/sec** with zero failed requests:

```
Endpoint Route                           Requests  Fails     p50      p90      p95      Max
---------------------------------------  --------  -----   -----    -----    -----    -----
GET /courses/ [Catalog Grid]                1,234      0   49 ms   580 ms  1000 ms  2035 ms
GET /courses/<slug>/ [Course Detail]        1,011      0  240 ms   800 ms  1300 ms  2217 ms
GET /courses/api/autocomplete/ [Search]       809      0   47 ms   600 ms   950 ms  1982 ms
GET /dashboard/ [Dashboard Home]              676      0  140 ms  1500 ms  2300 ms  3007 ms
GET /courses/<slug>/ [Study View]             498      0  260 ms   810 ms  1300 ms  1818 ms
GET /health/live/ [Liveness Ping]             405      0   52 ms   690 ms  1100 ms  2007 ms
GET /courses/<slug>/assessments/              364      0  150 ms  1800 ms  2300 ms  3009 ms
GET /learning-roadmap/ [Career Paths]         275      0  110 ms  1800 ms  2300 ms  2611 ms
GET /certificates/ [Certificate Center]       220      0  110 ms  1400 ms  2800 ms  3126 ms
GET /verify/<code/ [Public Cert Verify]       167      0  160 ms  1300 ms  1900 ms  2157 ms
GET /health/ready/ [Readiness Probe]          158      0  150 ms  1200 ms  2000 ms  2205 ms
---------------------------------------  --------  -----   -----    -----    -----    -----
AGGREGATED TOTALS                           5,817      0  180 ms   990 ms  1500 ms  3126 ms
```

---

## 4. Hardware Saturation & Scaling Thresholds

### 4.1 Observations & Bottlenecks
1. **CPU & Thread Contention**:
   Up to 250 CCU, median response time remained under 15 ms. At 500 and 1,000 CCU, queueing delay within the 16 Gunicorn worker threads caused median latencies to rise to 130 ms and 180 ms respectively.
2. **Database Multiplexing**:
   Zero connection pool exhaustion errors occurred because queries were short-lived and returned promptly.
3. **Physical Host Limit**:
   On a single development host (Apple M-series 8-core CPU), 1,000 concurrent simulated clients running Locust simultaneously with Gunicorn saturated host CPU to ~85%.
   **Conclusion**: To achieve 10,000 CCU, the application requires horizontal distribution across 10–20 ECS Fargate tasks behind an Application Load Balancer as modeled in Terraform.
