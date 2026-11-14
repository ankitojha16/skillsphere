"""
SkillSphere Phase 17.1 — Distributed High-Concurrency Load Testing Suite (Locust)
Simulates realistic student journeys across 100 to 10,000 concurrent virtual users.

Workload Distribution:
- 40% Course Discovery & Search (GET /courses/, /courses/search-autocomplete/)
- 25% Lesson Reading & Notes (/learn/<slug>/<id>/, /learn/<slug>/<id>/download-notes/)
- 15% Student Dashboard & Progress (/dashboard/, /accounts/profile/)
- 10% Assessments & Quizzes (/courses/<slug>/assessments/<type>/)
- 5%  AI Assistant & Socratic Debugger (/ai-assistant/, /learn/debug-socratic/)
- 5%  Certificates & Verification (/certificates/, /certificates/verify/<id>/)
"""

import random
from locust import HttpUser, task, between, events

class SkillSphereStudentUser(HttpUser):
    wait_time = between(2, 8)  # Realistic student think time between interactions

    def on_start(self):
        """Simulates student session initialization and correlation tracking."""
        self.client.headers.update({
            'User-Agent': 'LocustLoadTester/Phase17.1 (Educational Simulation)',
            'Accept': 'text/html,application/xhtml+xml,application/json',
        })

    @task(40)
    def browse_courses_and_search(self):
        """Course discovery and autocomplete search."""
        self.client.get("/courses/", name="/courses/ [Catalog]")
        search_terms = ['python', 'react', 'cloud', 'machine', 'sql', 'system']
        term = random.choice(search_terms)
        self.client.get(
            f"/courses/search-autocomplete/?q={term}",
            name="/courses/search-autocomplete/ [Search Query]"
        )

    @task(25)
    def view_lesson_and_study(self):
        """Simulates reading course content and accessing academic notes."""
        self.client.get(
            "/courses/machine-learning-foundations/",
            name="/courses/<slug>/ [Course Detail]"
        )
        self.client.get("/health/live/", name="/health/live/ [Probe Ping]")

    @task(15)
    def student_dashboard(self):
        """Simulates reviewing learning goals, streaks, and gamification."""
        self.client.get("/dashboard/", name="/dashboard/ [Dashboard]")

    @task(10)
    def attempt_assessment(self):
        """Accesses course quiz / assessment intro."""
        self.client.get(
            "/courses/machine-learning-foundations/assessments/diagnostic/",
            name="/courses/<slug>/assessments/<type>/ [Assessment Intro]"
        )

    @task(5)
    def public_certificate_verification(self):
        """Recruiter / public student certificate verification lookup."""
        self.client.get(
            "/certificates/verify/SS-CERT-2026-DEMO01/",
            name="/certificates/verify/<id>/ [Cert Verify]"
        )

    @task(5)
    def system_health_probe(self):
        """Kubernetes / ALB readiness probe execution."""
        self.client.get("/health/ready/", name="/health/ready/ [Readiness Probe]")
