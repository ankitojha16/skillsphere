# SkillSphere Resilience & Fault-Tolerance Architecture

## 1. Resilience Principles & Patterns

In a platform serving 10,000 active learners, downstream dependencies (external AI models, email providers, third-party CDNs) will periodically fail. SkillSphere implements strict failure isolation patterns to ensure downstream outages never degrade core learning funnels.

---

## 2. Distributed Circuit Breaker Pattern

The `CircuitBreaker` class in `services/resilience.py` manages state across all application instances using Redis/cache:
- **`CLOSED`**: Normal execution. Successes reset consecutive failure counters.
- **`OPEN`**: Tripped when 3 consecutive calls fail within a window. Requests fast-fail immediately ($<1\text{ms}$) directly to the fallback function without executing expensive network sockets.
- **`HALF_OPEN`**: After 45–60 seconds, a single test probe request is permitted through. If the probe succeeds, the circuit returns to `CLOSED`. If it fails, the circuit re-trips to `OPEN`.

### AI Integration Fast-Fail Circuit
In `services/ai_service.py`:
- Gemini 3.8 Flash cascade calls are wrapped by `CircuitBreaker(name='gemini_api')`.
- When the circuit trips to `OPEN`, student requests in the Study Assistant, Project Generator, and Mock Interviewer are instantly served from the **Offline Knowledge Engine** without experiencing 25-second timeouts.

---

## 3. Bulkhead Pattern
Bulkhead concurrency limits isolate shared application memory and thread pools:
- **AI Integration**: Max 20 concurrent outgoing API calls. Excess requests receive immediate cached knowledge responses.
- **Durable Task Queue**: Bounded thread pool preventing background processing from starving web workers of CPU.

---

## 4. Timeouts & Graceful Degradation Matrix

| Component | Timeout | On-Failure Behavior | User Impact |
|---|---|---|---|
| **Database Queries** | 10 seconds (`statement_timeout=10000`) | Query killed automatically | Clean error message; connection pool protected |
| **Database Connect** | 5 seconds (`connect_timeout=5`) | Fast 503 response | Prevents thread freezing on network partition |
| **External AI Calls** | 1.5s per model, 25s deadline | Immediate fallback to offline Knowledge Engine | Student continues studying uninterrupted |
| **Redis Cache Ping** | 2 seconds (`socket_timeout=2.0`) | Silent fallback to `LocMemCache` | Zero 500 errors; transparent fallback |
| **Certificate PDF Download** | 5 seconds | Render error screen with Retry button | Core dashboard remains fully responsive |
