# SkillSphere Phase 18.2 — Edge Proxy Security & Ingress Architecture

## 1. Edge Proxy Threat Model & Ingress Topology

SkillSphere employs Nginx as an edge reverse proxy and TLS-termination layer situated directly behind external cloud load balancers (e.g. AWS Application Load Balancer or Cloudflare CDN).

```
  [ Student Client ]  (e.g., Campus NAT: 198.51.100.45)
          │
          │ HTTPS (TLS 1.3)
          ▼
  [ Cloud Load Balancer / CDN ] (e.g., AWS ALB in 10.0.1.50)
          │
          │ HTTP / Ingress with X-Forwarded-For: 198.51.100.45, 10.0.1.50
          ▼
  [ Nginx Ingress Layer (nginx.staging.conf) ]
  ├── Real IP Processing: Walks right-to-left, detects 198.51.100.45
  ├── Anti-Spoofing: Discards forged client headers
  ├── DoS Protection: 100r/s rate limit, 120 burst, 100 conns/IP
  ├── Static / Media Bypass: Unthrottled static asset delivery
  └── WebSocket Pass-through: /ws/ with upgrade headers and 24h timeouts
          │
          ├──> [ Web Instance 1:8000 ]
          └──> [ Web Instance 2:8000 ]
```

---

## 2. Ingress Security & Header Verification

### 2.1 Anti-Spoofing & Trusted Proxy Ranges (`set_real_ip_from`)
A common vulnerability in cloud environments occurs when Nginx naively accepts the leftmost IP address in `X-Forwarded-For`. A malicious client could submit:
```http
X-Forwarded-For: 127.0.0.1, 10.0.0.1
```
thereby bypassing IP-based rate limiting or gaining administrative whitelisting.

**Hardening Measure in SkillSphere:**
```nginx
set_real_ip_from 10.0.0.0/8;
set_real_ip_from 172.16.0.0/12;
set_real_ip_from 192.168.0.0/16;
set_real_ip_from 127.0.0.1;
real_ip_header X-Forwarded-For;
real_ip_recursive on;
```
With `real_ip_recursive on`, Nginx evaluates the addresses in `X-Forwarded-For` from right to left. It untrusts each proxy IP that falls within `set_real_ip_from` subnets, and selects the first *untrusted* address encountered. This guarantees that client-injected fake IP headers are ignored, and the actual egress IP of the client is bound to `$remote_addr` for rate limiting and auditing.

---

## 3. Shared NAT Networks & False-Positive Rate Limiting

### 3.1 The Campus NAT Challenge
In university campuses, coding bootcamps, and enterprise environments, hundreds or thousands of students access SkillSphere simultaneously from a single public IP address.
- A rigid rate limit of `10r/s` or `30r/s` with a small burst pool causes immediate HTTP 429 Too Many Requests errors when an entire cohort loads course catalogs, lesson videos, and interactive quizzes.

### 3.2 Implemented Rate Limiting Strategy
1. **Capacity Tuning**:
   - `limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;`
   - `limit_req zone=api_limit burst=120 nodelay;`
   - Accommodates rapid multi-resource loading while continuing to throttle aggressive automated scrapers and volumetric denial-of-service bots.
2. **Dedicated Static Asset Bypass**:
   - Static assets (`/static/`) are explicitly proxied in a dedicated location block without `limit_req`. CSS, JavaScript bundles, SVGs, and web fonts do not consume student API rate limit budgets.
3. **Browser Concurrency Sizing**:
   - `limit_conn conn_limit 100;` supports modern HTTP/1.1 and HTTP/2 pipelining where individual browsers open 6–8 concurrent TCP sockets per origin.

---

## 4. Upstream Timeouts & Streaming Buffering

| Location | Directive | Value | Rationale |
| :--- | :--- | :--- | :--- |
| **`/` (Web & API)** | `proxy_read_timeout` | `60s` | Bounds standard request durations against hanging threads. |
| **`/` (Web & API)** | `proxy_connect_timeout`| `5s` | Rapid failover to sibling instance if a node crashes. |
| **`/media/`** | `proxy_buffering` | `off` | Memory-efficient streaming of large resumes and certificates. |
| **`/media/`** | `proxy_read_timeout` | `120s` | Accommodates large file downloads on bandwidth-constrained links. |
| **`/ws/`** | `proxy_read_timeout` | `86400s` | Keeps interactive lounge and collaboration WebSockets open. |
| **Global** | `client_max_body_size` | `25M` | Enforces bounded payload sizes for resume and project uploads. |

---

## 5. Security Headers & TLS Offloading

Nginx injects global defense headers on every response:
```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

**HSTS (`Strict-Transport-Security`) Policy:**
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` is enforced by Django's `SECURE_HSTS_SECONDS` in production (`DEBUG=False`), when the upstream load balancer passes `X-Forwarded-Proto: https`.
- HSTS is deliberately omitted from plain HTTP port 80 blocks to prevent breaking local developer environments and staging tests without TLS certificates.
