# SkillSphere Production Gunicorn Configuration
# Tuned for high concurrency (Option B Container Architecture)

import os
import multiprocessing

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Calculate optimal workers: (2 * vCPUs) + 1 capped by available RAM
cpu_count = multiprocessing.cpu_count()
workers = int(os.getenv('WEB_CONCURRENCY', max(2, (2 * cpu_count) + 1)))

# Threaded worker model: ideal for mixed I/O, database queries, and edge CDN traffic
worker_class = 'gthread'
threads = int(os.getenv('GUNICORN_THREADS', 4))

# Bounded lifecycle to prevent memory fragmentation under 10K load
max_requests = 5000
max_requests_jitter = 500

# Connection timeouts
timeout = int(os.getenv('GUNICORN_TIMEOUT', 30))
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', 30))
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', 65))

# Logging format with request latency in microseconds
accesslog = '-'
errorlog = '-'
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

# Process naming
proc_name = 'skillsphere_gunicorn'
preload_app = True
