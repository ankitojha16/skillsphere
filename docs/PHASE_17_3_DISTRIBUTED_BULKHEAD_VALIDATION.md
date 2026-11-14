# SkillSphere Phase 17.3 — Distributed Bulkhead Validation

## 1. Executive Overview

In a distributed multi-node architecture, resource-intensive operations (e.g., ReportLab PDF rendering, AI prompt evaluation, large report generation) cannot be bounded using process-local primitives like `threading.Semaphore`. A local semaphore only limits concurrency within a single Python worker process. If 10 container instances run 4 worker processes each, a local limit of 5 allows up to 200 concurrent tasks fleet-wide, easily exhausting database connection pools and saturating upstream APIs.

Phase 17.3 validates and hardens `services/resilience.py:DistributedBulkhead`, an enterprise-grade distributed concurrency limiter backed by Redis and atomic Lua scripting.

---

## 2. Distributed Architecture & Atomic Lua Scripting

To eliminate race conditions, double acquisitions, and desynchronized counters, all bulkhead state transitions execute inside atomic Redis Lua scripts. Bulkhead slots are stored in a Redis sorted set (`ZSET`), where:
- **Member**: Unique token format `{instance_id}:{uuid_hex}`.
- **Score**: Unix timestamp representing the absolute expiration time ($now + TTL$).

```
                      Worker 1 (Pod A)       Worker 2 (Pod B)
                             │                      │
                             ▼                      ▼
                     ┌──────────────────────────────────────┐
                     │          Redis Cluster / Node        │
                     │  Key: bulkhead:permits:<resource>    │
                     │  ZSET: [ {token_a: exp1}, ... ]      │
                     └──────────────────────────────────────┘
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
      [LUA_ACQUIRE]               [LUA_RENEW]                [LUA_RELEASE]
  - Purge expired slots       - Check token existence     - ZREM token
  - ZCARD < max_slots         - ZADD with new expiry      - Immediate capacity
  - ZADD new token + TTL      - Return 1 (OK) or 0 (lost)   restoration
```

### 2.1 Lua Script Definitions

#### 1. Atomic Acquisition (`LUA_ACQUIRE`)
```lua
-- KEYS[1]: bulkhead:permits:<name>
-- ARGV[1]: current_unix_timestamp
-- ARGV[2]: lease_expiration_timestamp
-- ARGV[3]: max_concurrent_permits
-- ARGV[4]: unique_token

redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1])
local current_count = redis.call('ZCARD', KEYS[1])
if current_count < tonumber(ARGV[3]) then
    redis.call('ZADD', KEYS[1], ARGV[2], ARGV[4])
    redis.call('EXPIRE', KEYS[1], 86400)
    return 1
else
    return 0
end
```
- **Automatic Garbage Collection**: Stale slots whose leases expired (e.g., from killed containers or segfaults) are purged on every acquire attempt via `ZREMRANGEBYSCORE`.
- **Zero Race Conditions**: Slot counting (`ZCARD`) and permit insertion (`ZADD`) happen atomically within the same Redis single-threaded execution context.

#### 2. Atomic Renewal (`LUA_RENEW`)
```lua
-- KEYS[1]: bulkhead:permits:<name>
-- ARGV[1]: current_unix_timestamp
-- ARGV[2]: new_expiration_timestamp
-- ARGV[3]: unique_token

local score = redis.call('ZSCORE', KEYS[1], ARGV[3])
if score and tonumber(score) > tonumber(ARGV[1]) then
    redis.call('ZADD', KEYS[1], ARGV[2], ARGV[3])
    return 1
else
    return 0
end
```
- **Ownership Guarantee**: A worker can only extend its lease if the token is currently registered and has not already expired and been reallocated.

#### 3. Atomic Release (`LUA_RELEASE`)
```lua
-- KEYS[1]: bulkhead:permits:<name>
-- ARGV[1]: unique_token

return redis.call('ZREM', KEYS[1], ARGV[1])
```
- Removes the specific permit token immediately, freeing up capacity for waiting instances.

---

## 3. Active Heartbeat & Long-Running Lease Renewal

For tasks with non-deterministic runtimes (e.g., generating multi-page certificate bundles or compiling student analytics), setting an excessively long static TTL risks locking slots for hours if an instance dies.

The `DistributedBulkhead` supports active lease renewal:
```python
bulkhead = DistributedBulkhead("pdf_generation", max_fleet_concurrent=10, lease_ttl_seconds=30)
token = bulkhead.acquire(timeout=5.0)

try:
    for page in generate_pages():
        render_page(page)
        # Extend lease by 30 seconds after completing each page
        bulkhead.renew_lease(token, extension_seconds=30)
finally:
    bulkhead.release(token)
```

If a worker experiences an unrecoverable failure, its heartbeat stops, and Redis automatically expires the slot within 30 seconds, restoring fleet capacity without manual operational intervention.

---

## 4. Fail-Open Degraded Mode & Observability

If the Redis connection drops, times out, or Redis is temporarily down:
- The `DistributedBulkhead` detects the connection failure and switches to **Degraded Process-Local Mode**.
- It falls back to a process-local `threading.BoundedSemaphore` with capacity `fallback_local_concurrent` (default: 2 permits).
- It emits a structured warning to notify operations:
  ```
  [WARNING] [skillsphere.resilience]: [DistributedBulkhead:pdf_generation] Redis unavailable; degraded to process-local Bulkhead (capacity=2). Fleet-wide enforcement is INACTIVE.
  ```
- Property `bulkhead.is_degraded` returns `True`, allowing health checks and metrics dashboards to alert on split-brain vulnerability.

---

## 5. Scope & Concurrency Guarantees

| Characteristic | Process-Local Semaphore | DistributedBulkhead (Redis Active) | DistributedBulkhead (Redis Degraded) |
| :--- | :--- | :--- | :--- |
| **Scope** | Single OS process | Fleet-wide across all pods/instances | Process-local |
| **Multi-instance Safe** | ❌ No (Limits multiplied by pod count) | ✅ Yes (Hard fleet-wide ceiling) | ⚠️ Degraded (Process-isolated) |
| **Dead-Worker Recovery** | ❌ Never releases if thread hangs | ✅ Automatic via TTL / GC | ❌ Process-bound |
| **Atomic Coordination** | In-memory GIL / Lock | Atomic Lua in Redis single-thread | Local Semaphore |
| **Performance Overhead** | < 1 µs | ~ 0.5 - 1.5 ms (Redis RTT) | < 1 µs |

---

## 6. Automated Test Verification

Hardening verified via `services/test_phase_17_3_hardening.py:test_distributed_bulkhead_atomic_lua_and_renewal`:
- Permits acquire cleanly.
- `renew_lease` returns `True` and extends expiration.
- `release` cleanly reclaims slot.
- Context manager pattern (`with bh.acquire_context(...)`) executes safely.
- Degraded mode fallback validated when Redis is absent.
