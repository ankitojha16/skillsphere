# SkillSphere Phase 18 — Autoscaling Strategy & Safeguards

## 1. Executive Summary

This document specifies the autoscaling architecture for SkillSphere's Web and Background Worker fleets, defining target tracking metrics, scale-out/in cooldowns, and critical database connection saturation safeguards.

---

## 2. Fleet Sizing & Bounds

To prevent runaway costs and guarantee database connection safety, all autoscaling policies operate within strict hard bounds:

| Fleet Tier | Min Tasks (Baseline) | Max Tasks (Peak 10k CCU) | Target Sizing Metric | Primary Constraint |
| :--- | :---: | :---: | :--- | :--- |
| **Web Service** | 2 | 20 | CPU @ 70%, ALB Request Count | Database client connections $\le 320$ |
| **Worker Service**| 2 | 10 | Queue backlog depth | Database worker connections $\le 20$ |

---

## 3. Web Service Autoscaling Policies

### 3.1 Metric 1: CPU Utilization Target Tracking (Primary)
- **Target Value**: **$70\%$ average CPU utilization** across the ECS service.
- **Scale-Out Evaluation**:
  - Evaluation period: 3 consecutive 1-minute datapoints exceeding $70\%$.
  - Scale-out cooldown: **$60\text{ seconds}$**.
  - Adds tasks dynamically to absorb traffic spikes before CPU saturates.
- **Scale-In Evaluation**:
  - Evaluation period: 15 consecutive 1-minute datapoints below $45\%$.
  - Scale-in cooldown: **$300\text{ seconds}$** ($5\text{ minutes}$).
  - Gradual scale-in prevents flapping/thrashing during lulls between class sessions.

### 3.2 Metric 2: Application Load Balancer Request Count Per Target (Secondary)
- **Target Value**: **$75\text{ requests/target/minute}$**.
- Ensures the fleet scales out proactively during sudden traffic surges before CPU metrics register the spike.

---

## 4. Background Worker Fleet Autoscaling Policies

Workers do not process HTTP traffic; scaling based on CPU or ALB metrics would fail during queue backlogs.

### 4.1 Queue Depth Custom CloudWatch Metric
- Every minute, a lightweight Lambda or scheduled ECS task queries:
  ```sql
  SELECT COUNT(*) FROM analytics_durabletaskjob WHERE status IN ('pending', 'failed') AND scheduled_at <= NOW();
  ```
  and emits `SkillSphere/TaskQueue:BacklogDepth` to CloudWatch.

### 4.2 Worker Step Scaling Policy:
| Backlog Depth (Pending Jobs) | Action | Desired Worker Tasks |
| :---: | :---: | :---: |
| $0 \le \text{Depth} < 10$ | Maintain Baseline | 2 tasks |
| $10 \le \text{Depth} < 50$ | Scale Up +2 | 4 tasks |
| $50 \le \text{Depth} < 200$| Scale Up +4 | 8 tasks |
| $\text{Depth} \ge 200$ | Maximum Emergency Scale | 10 tasks (Hard Ceiling) |

---

## 5. Database Connection Exhaustion Safeguards

Autoscaling without database protection causes cascading failures: adding web tasks creates more database connections, which exhausts the pool, slows queries, increases CPU on web tasks, and triggers even more autoscaling until the database crashes.

### Protection Mechanisms:
1. **Hard Upper Bound**: Web service is capped at **20 tasks** ($20 \times 16\text{ client threads} = 320\text{ connections}$).
2. **PgBouncer Multiplexing**: All 320 client connections funnel into **80 physical PostgreSQL server connections**. The database server never sees connection spikes regardless of task scaling.
3. **Database Health Feedback Circuit**:
   - If PostgreSQL connection pool utilization exceeds $85\%$, the custom health metric triggers an alert and temporarily freezes autoscaling scale-out events.
