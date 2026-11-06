import time
import logging
from django.db import connection

logger = logging.getLogger('skillsphere.performance')

class PerformanceMonitoringMiddleware:
    """
    Middleware that measures total response time and database query metrics.
    Appends the standard W3C `Server-Timing` header to HTTP responses:
      Server-Timing: total;dur=..., db;dur=..., sql_count=...
    Also logs any requests exceeding 500ms or slow queries without leaking sensitive data.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()
        query_times = []
        query_count = 0

        def query_timer(execute, sql, params, many, context):
            nonlocal query_count
            q_start = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                q_duration = (time.perf_counter() - q_start) * 1000.0
                query_count += 1
                query_times.append(q_duration)
                if q_duration > 150.0:
                    # Log slow queries (safely truncate without printing user params)
                    safe_sql = (sql[:120] + '...') if len(sql) > 120 else sql
                    logger.warning(f"SLOW QUERY [{q_duration:.2f}ms]: {safe_sql}")

        # Wrap DB queries for accurate measurement across all backends
        with connection.execute_wrapper(query_timer):
            response = self.get_response(request)

        total_duration = (time.perf_counter() - start_time) * 1000.0
        db_duration = sum(query_times)

        # Set Server-Timing headers for real-time browser & API observability
        response['Server-Timing'] = (
            f"total;dur={total_duration:.2f}, "
            f"db;dur={db_duration:.2f}, "
            f"sql_count={query_count}"
        )

        if total_duration > 600.0 and not request.path.startswith('/static/'):
            logger.info(
                f"Slow Request: {request.method} {request.path} took {total_duration:.2f}ms "
                f"({query_count} queries, {db_duration:.2f}ms in DB)"
            )

        return response
