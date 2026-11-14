# SkillSphere Phase 18.2 — Database & Network Capacity Analysis

## 1. Concurrency Model & Connection Sizing Recalculation

At peak scale targeting 10,000 concurrently active users, SkillSphere scales dynamically between minimum baseline and maximum capacity:

### 1.1 Compute Fleet Sizing & Client Connections

| Component | Min Tasks | Max Tasks | Processes & Threads per Task | Client Connections (Min) | Client Connections (Max) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Web Service (Fargate)** | 2 | 20 | 4 Gunicorn workers $\times$ 4 threads | $2 \times 16 = 32$ | $20 \times 16 = 320$ |
| **Worker Daemons (Fargate)** | 2 | 10 | 1 process $\times$ 2 DB threads | $2 \times 2 = 4$ | $10 \times 2 = 20$ |
| **Administrative & Migration**| 1 | 2 | Ad-hoc CLI / Management jobs | 2 | 5 |
| **Prometheus / Health Exporters**| 1 | 2 | Metrics scrapers querying pg_stat | 2 | 3 |
| **AGGREGATE TOTAL CLIENTS** | **6** | **34** | — | **40** | **348** |

---

## 2. PgBouncer Multiplexing & Safety Headroom

Allowing 348 raw client connections directly into PostgreSQL would exhaust database memory, degrade query planner throughput, and trigger connection rejection errors.

```
       Application Fleet (Up to 348 Concurrent Client Connections)
                                    │
                                    ▼
       ===========================================================
                   PgBouncer Connection Pooler
         - Pooling Mode:         TRANSACTION
         - max_client_conn:      500
         - default_pool_size:    40
         - reserve_pool_size:    10
         - max_db_connections:  80
       ===========================================================
                                    │
                                    ▼ Multiplexed into <= 80 connections
       ===========================================================
                   PostgreSQL 17 Database Server
         - max_connections:     100
         - Active Pooled:        80 max
         - Reserved Headroom:    20 (20% for superusers, autovacuum)
       ===========================================================
```

### 2.1 Transaction Pooling Mechanics
Because SkillSphere utilizes standard Django stateless request cycles:
- Connections are acquired from PgBouncer only for the duration of a transaction or single query, and returned immediately.
- A physical pool of 40–80 connections comfortably services 348 active client threads with $0$ queue wait under normal request distributions.
- The 20 reserved server connections guarantee that administrative sessions, schema migrations, and autovacuum processes never fail due to pool saturation.

---

## 3. Network Latency & Inter-Service Budget

In a distributed multi-instance cloud topology across independent Availability Zones:

| Network Link | Protocol | Expected Latency | Potential Bottleneck | Mitigation Implemented |
| :--- | :--- | :--- | :--- | :--- |
| **ALB $\rightarrow$ Web Node** | HTTP/1.1 | 0.5 – 1.5 ms | Slow connection handshakes | Keep-alive connections enabled (`keepalive 32`). |
| **Web Node $\rightarrow$ Redis** | TCP / RESP | 0.8 – 2.0 ms | Serialization overhead | Redis connection pooling with socket timeouts (3s connect, 5s read). |
| **Web Node $\rightarrow$ PgBouncer** | TCP (PostgreSQL) | 0.5 – 1.5 ms | High connection churn | Transaction-level connection pooling. |
| **PgBouncer $\rightarrow$ PostgreSQL** | TCP (Same VPC) | 0.3 – 1.0 ms | Cross-AZ hops | Colocated in private data subnets. |
| **Web/Worker $\rightarrow$ S3 / R2** | HTTPS (SigV4) | 10 – 35 ms | Large payload memory buffering | Streaming chunked uploads/downloads (`save_file_stream`, `get_file_chunks`). |

### 3.1 Network Failure & Partition Protections
1. **Redis Down**: `RedisService` and `DistributedBulkhead` degrade to process-local semaphores, preventing cascade failure of web requests.
2. **Object Storage Down**: Storage service catches endpoint errors and logs structured alerts without crashing Django workers.
3. **Database Slowdown**: PgBouncer query cancellation triggers after bounded wait timeouts, terminating runaway queries.
