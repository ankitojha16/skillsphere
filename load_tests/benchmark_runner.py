#!/usr/bin/env python3
"""
SkillSphere Progressive Concurrency & Capacity Benchmark Runner
Tests application performance, throughput, error rates, and p50/p90/p95/p99 latencies
across progressive concurrency stages:
  Stage 1: 100 virtual users
  Stage 2: 500 virtual users
  Stage 3: 1,000 virtual users
  Stage 4: 2,500 virtual users
  Stage 5: 5,000 virtual users
  Stage 6: 7,500 virtual users
  Stage 7: 10,000 virtual users
  Stage 8: 12,000 virtual users (burst stress test)
"""

import sys
import time
import math
import ssl
import random
import urllib.request
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

# Configure SSL context (handles macOS / system CA bundle environments)
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    try:
        SSL_CTX = ssl._create_unverified_context()
    except Exception:
        SSL_CTX = None

TARGET_ENDPOINTS = [
    # (weight, method, path, post_data)
    (30, 'GET', '/courses/', None),
    (15, 'GET', '/courses/?category=engineering-tech&page=2', None),
    (20, 'GET', '/courses/api/autocomplete/?q=python', None),
    (15, 'GET', '/courses/python-programming-from-scratch/', None),
    (10, 'GET', '/privacy/', None),
    (5, 'GET', '/terms/', None),
    (5, 'GET', '/feedback/', None),
]


def choose_endpoint():
    total_weight = sum(w for w, _, _, _ in TARGET_ENDPOINTS)
    r = random.uniform(0, total_weight)
    uptime = 0
    for w, method, path, data in TARGET_ENDPOINTS:
        uptime += w
        if r <= uptime:
            return method, path, data
    return TARGET_ENDPOINTS[0][1], TARGET_ENDPOINTS[0][2], TARGET_ENDPOINTS[0][3]


def execute_request(base_url, timeout=6.0):
    method, path, data = choose_endpoint()
    url = f"{base_url.rstrip('/')}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header('User-Agent', 'SkillSphere-Capacity-Benchmark/1.0')

    start_t = time.perf_counter()
    try:
        open_kwargs = {'timeout': timeout}
        if SSL_CTX is not None:
            open_kwargs['context'] = SSL_CTX
        with urllib.request.urlopen(req, **open_kwargs) as resp:
            dur = (time.perf_counter() - start_t) * 1000.0
            return True, resp.status, dur, None
    except urllib.error.HTTPError as e:
        dur = (time.perf_counter() - start_t) * 1000.0
        # 301/302 redirects are successful for auth guards and canonical URLs
        if e.code in (301, 302):
            return True, e.code, dur, None
        return False, e.code, dur, f"HTTP {e.code}"
    except Exception as ex:
        dur = (time.perf_counter() - start_t) * 1000.0
        return False, 0, dur, str(ex)[:60]


def worker_loop(base_url, stop_at, pacing_delay):
    latencies = []
    success = 0
    failed = 0
    errors = {}

    while time.perf_counter() < stop_at:
        req_start = time.perf_counter()
        ok, status, dur, err = execute_request(base_url)
        latencies.append(dur)
        if ok:
            success += 1
        else:
            failed += 1
            errors[err] = errors.get(err, 0) + 1

        elapsed = time.perf_counter() - req_start
        rem_sleep = pacing_delay - elapsed
        if rem_sleep > 0.001:
            time.sleep(rem_sleep)

    return latencies, success, failed, errors


def run_stage(base_url, virtual_users, duration_seconds=10, max_workers=120):
    """
    Simulates a given number of concurrent virtual users over a duration window.
    Calculates dynamic RPS using realistic think time (15s–25s average).
    """
    # At think time = 20s, requests per second = virtual_users / 20.0
    target_rps = max(10.0, virtual_users / 20.0)
    worker_pool_size = min(virtual_users, max_workers)
    pacing_delay = worker_pool_size / target_rps

    print(f"\n{'='*72}")
    print(f"STAGE: {virtual_users:,} Concurrent Active Users")
    print(f"Target Workload: ~{target_rps:.1f} dynamic RPS over {duration_seconds}s (Pool: {worker_pool_size} workers)")
    print(f"{'='*72}")

    stop_at = time.perf_counter() + duration_seconds
    start_bench = time.perf_counter()

    latencies = []
    success_count = 0
    failure_count = 0
    errors = {}

    with ThreadPoolExecutor(max_workers=worker_pool_size) as executor:
        futures = [
            executor.submit(worker_loop, base_url, stop_at, pacing_delay)
            for _ in range(worker_pool_size)
        ]
        for f in futures:
            w_lats, w_succ, w_fail, w_errs = f.result()
            latencies.extend(w_lats)
            success_count += w_succ
            failure_count += w_fail
            for err, cnt in w_errs.items():
                errors[err] = errors.get(err, 0) + cnt

    total_time = time.perf_counter() - start_bench
    actual_rps = len(latencies) / total_time if total_time > 0 else 0

    latencies.sort()
    n = len(latencies)
    p50 = latencies[int(n * 0.50)] if n else 0
    p90 = latencies[int(n * 0.90)] if n else 0
    p95 = latencies[int(n * 0.95)] if n else 0
    p99 = latencies[int(n * 0.99)] if n else 0
    error_rate = (failure_count / n * 100.0) if n else 0.0

    print(f"Results for {virtual_users:,} Users:")
    print(f"  Throughput:  {actual_rps:.2f} RPS ({success_count} success, {failure_count} failed)")
    print(f"  Error Rate:  {error_rate:.2f}%")
    print(f"  Latency p50: {p50:.2f} ms")
    print(f"  Latency p90: {p90:.2f} ms")
    print(f"  Latency p95: {p95:.2f} ms  (Target: <500ms)")
    print(f"  Latency p99: {p99:.2f} ms")
    if errors:
        print(f"  Errors encountered: {errors}")

    return {
        'users': virtual_users,
        'target_rps': round(target_rps, 1),
        'actual_rps': round(actual_rps, 2),
        'success': success_count,
        'failed': failure_count,
        'error_rate': round(error_rate, 2),
        'p50': round(p50, 2),
        'p90': round(p90, 2),
        'p95': round(p95, 2),
        'p99': round(p99, 2),
    }


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else 'https://skillsphere-cyan.vercel.app'
    print(f"Starting SkillSphere Capacity & Progressive Concurrency Benchmark against: {base_url}")

    stages = [100, 500, 1000, 2500, 5000, 7500, 10000, 12000]
    results = []

    for stage_users in stages:
        res = run_stage(base_url, stage_users, duration_seconds=10, max_workers=100)
        results.append(res)
        time.sleep(2)  # Cooldown between stages

    print(f"\n\n{'='*95}")
    print("FINAL CAPACITY & PROGRESSIVE LOAD TESTING SUMMARY TABLE")
    print(f"{'='*95}")
    header = f"{'Stage (Users)':<15} | {'Target RPS':<11} | {'Actual RPS':<11} | {'p50 (ms)':<9} | {'p95 (ms)':<9} | {'p99 (ms)':<9} | {'Error %':<8} | {'Status'}"
    print(header)
    print("-" * len(header))

    for r in results:
        status = "PASSED" if r['error_rate'] < 1.0 and r['p95'] < 500 else ("ACCEPTABLE" if r['error_rate'] < 2.0 else "DEGRADED")
        print(f"{r['users']:<15,d} | {r['target_rps']:<11.1f} | {r['actual_rps']:<11.2f} | {r['p50']:<9.2f} | {r['p95']:<9.2f} | {r['p99']:<9.2f} | {r['error_rate']:<7.2f}% | {status}")
    print(f"{'='*95}\n")


if __name__ == '__main__':
    main()
