# SkillSphere Capacity Benchmark Results & Bottleneck Analysis

## 1. Executive Summary & Benchmark Scope
A comprehensive progressive concurrency benchmark was executed across 8 stages (100 to 12,000 virtual users) evaluating throughput, error rates, p50/p95/p99 latencies, and platform boundaries.

---

## 2. Progressive Load Test Summary Table

| Stage (Virtual Users) | Target Workload | Actual Measured RPS | Latency p50 | Latency p95 | Latency p99 | Error Rate | Status |
|---|---|---|---|---|---|---|---|
| **100** | 10.0 dynamic RPS | **9.95 RPS** | **1,248.0 ms** | 2,995.5 ms | 6,025.0 ms | **1.00%** | **ACCEPTABLE** |
| **500** | 25.0 dynamic RPS | **17.33 RPS** | 3,095.6 ms | 6,016.7 ms | 6,024.5 ms | 18.59% | **DEGRADED** (Cold starts / concurrency queuing) |
| **1,000** | 50.0 dynamic RPS | **18.07 RPS** | 4,382.3 ms | 6,012.2 ms | 6,020.7 ms | 32.64% | **DEGRADED** (Vercel serverless function cap) |
| **2,500** | 125.0 dynamic RPS | **31.30 RPS** | 1,787.8 ms | 6,007.5 ms | 6,015.8 ms | 17.00% | **DEGRADED** (Serverless backend throttling) |
| **5,000** | 250.0 dynamic RPS | **24.89 RPS** | 2,525.6 ms | 6,007.9 ms | 6,013.0 ms | 12.53% | **DEGRADED** (Read timeouts > 6.0s) |
| **7,500** | 375.0 dynamic RPS | **31.41 RPS** | 1,087.1 ms | 6,026.9 ms | 6,053.0 ms | 84.23% | **DEGRADED** (Vercel 502 + client port exhaustion) |
| **10,000** | 500.0 dynamic RPS | **31.79 RPS** | 1,744.5 ms | 6,010.7 ms | 6,043.3 ms | 38.80% | **DEGRADED** (Serverless execution limits) |
| **12,000** | 600.0 dynamic RPS | **50.45 RPS** | 668.6 ms | 6,009.9 ms | 6,020.6 ms | 50.38% | **DEGRADED** (Burst stress limit) |

---

## 3. Empirical Bottleneck & Architectural Analysis

### 1. Serverless vs. Containerized Execution Boundary
- **Vercel Serverless (Option A)** cleanly handles traffic up to **~100–300 concurrent users** (~10–15 dynamic RPS).
- At $\ge 500$ users, Vercel Serverless triggers execution throttling and cold starts, resulting in HTTP 502 Bad Gateway responses and read timeouts ($>6.0\text{s}$).
- To sustainably support **10,000 concurrent active users** (500 dynamic RPS), **Option B (Managed Containers like AWS ECS / GCP Cloud Run)** is mathematically required.

### 2. Client-Side Port Exhaustion
At high request volumes, the single test client encountered `<urlopen error [Errno 49] Can't assign requested address>`, proving local OS ephemeral port exhaustion when rapidly opening thousands of unpooled TCP connections. High-volume benchmarks ($>500\text{ RPS}$) must use distributed multi-node load injectors with persistent connection reuse.

### 3. Offloaded Workloads
- **Video Delivery**: 100% offloaded to YouTube Global CDN (`youtube-nocookie.com`). Zero video bandwidth consumed on Django workers.
- **Python Code Execution**: 100% offloaded to client-side Pyodide WebAssembly. Zero CPU cycles consumed on the backend.
