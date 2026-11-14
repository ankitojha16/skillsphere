# SkillSphere Distributed Load Testing Guide

## 1. Load Testing Architecture & Tools

SkillSphere includes two automated load testing tools:
1. `load_tests/locustfile.py`: Distributed, multi-persona Locust suite for horizontal worker testing.
2. `load_tests/benchmark_runner.py`: Progressive standalone Python benchmark for concurrency ramp testing (100 to 12,000 virtual users).

---

## 2. Safe Execution Rules

> [!CAUTION]
> **Production Protection**:
> - Never run uncontrolled high-concurrency benchmarks against live production without explicit coordination.
> - High concurrency tests ($>500\text{ RPS}$) must be executed against an isolated staging environment.
> - The synthetic data generator `generate_synthetic_load_data` will **refuse to run** in production unless `ALLOW_SYNTHETIC_DATA=True` and `--confirm-synthetic-danger` are provided.

---

## 3. Running the Progressive Benchmark Runner

### Basic Execution (Single Instance)
```bash
./.venv/bin/python load_tests/benchmark_runner.py https://skillsphere-cyan.vercel.app
```

### Stages Executed
1. **Stage 1**: 100 Virtual Users (~10 dynamic RPS)
2. **Stage 2**: 500 Virtual Users (~25 dynamic RPS)
3. **Stage 3**: 1,000 Virtual Users (~50 dynamic RPS)
4. **Stage 4**: 2,500 Virtual Users (~125 dynamic RPS)
5. **Stage 5**: 5,000 Virtual Users (~250 dynamic RPS)
6. **Stage 6**: 7,500 Virtual Users (~375 dynamic RPS)
7. **Stage 7**: 10,000 Virtual Users (~500 dynamic RPS)
8. **Stage 8**: 12,000 Virtual Users (Burst Stress Test, ~600 dynamic RPS)

---

## 4. Running Distributed Locust Tests (Cluster Mode)

### Master Node:
```bash
locust -f load_tests/locustfile.py --master --host=https://skillsphere-staging.internal
```

### Worker Nodes (Run across 3+ test machines):
```bash
locust -f load_tests/locustfile.py --worker --master-host=10.0.1.100
```

### Headless CLI Execution:
```bash
locust -f load_tests/locustfile.py --headless -u 10000 -r 250 --run-time 30m --host=https://skillsphere-staging.internal --html=load_report.html
```
