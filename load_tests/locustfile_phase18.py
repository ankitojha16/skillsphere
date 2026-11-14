"""
SkillSphere Phase 18 — Multi-Instance Distributed Staging Load Test Suite (Locust)
Simulates realistic student behavior across multi-instance staging topologies.

Configured for staged load scenarios:
- Level 1: 1,000 Concurrent Users (Baseline Warmup)
- Level 2: 2,500 Concurrent Users (Autoscaling Trigger)
- Level 3: 5,000 Concurrent Users (Mid-tier Multi-AZ Fleet)
- Level 4: 7,500 Concurrent Users (High Capacity Stress)
- Level 5: 10,000 Concurrent Users (Peak Enterprise Target)
"""

import random
import time
from locust import HttpUser, task, between, events, tag


class CatalogDiscoveryStudent(HttpUser):
    """
    Cohort 1: Browsing, search autocomplete, catalog filtering, course detail views.
    Represents 50% of the active student population.
    """
    weight = 50
    wait_time = between(2, 6)

    def on_start(self):
        self.client.headers.update({
            'User-Agent': 'SkillSphereLoadBot/Phase18-Catalog',
            'Accept': 'text/html,application/xhtml+xml,application/json',
        })

    @task(30)
    def browse_catalog(self):
        self.client.get("/courses/", name="/courses/ [Catalog Grid]")

    @task(20)
    def search_autocomplete(self):
        query = random.choice(['python', 'docker', 'machine learning', 'sql', 'system design'])
        self.client.get(f"/courses/search-autocomplete/?q={query}", name="/courses/search-autocomplete/ [Search]")

    @task(25)
    def view_course_detail(self):
        slug = random.choice([
            'machine-learning-foundations',
            'full-stack-web-development-bootcamp',
            'cloud-architecture-mastery'
        ])
        self.client.get(f"/courses/{slug}/", name="/courses/<slug>/ [Course Detail]")

    @task(10)
    def liveness_ping(self):
        self.client.get("/health/live/", name="/health/live/ [Liveness Ping]")


class ActiveEnrolledStudent(HttpUser):
    """
    Cohort 2: Active learners consuming lessons, updating progress, and taking quizzes.
    Represents 35% of the active student population.
    """
    weight = 35
    wait_time = between(3, 8)

    def on_start(self):
        self.client.headers.update({
            'User-Agent': 'SkillSphereLoadBot/Phase18-ActiveLearner',
            'Accept': 'text/html,application/xhtml+xml,application/json',
        })

    @task(25)
    def access_dashboard(self):
        self.client.get("/dashboard/", name="/dashboard/ [Dashboard Home]")

    @task(20)
    def view_lesson_content(self):
        self.client.get("/courses/machine-learning-foundations/", name="/courses/<slug>/ [Study View]")

    @task(15)
    def load_assessment_intro(self):
        self.client.get(
            "/courses/machine-learning-foundations/assessments/diagnostic/",
            name="/courses/<slug>/assessments/<type>/ [Quiz Intro]"
        )

    @task(10)
    def check_roadmap(self):
        self.client.get("/learning-roadmap/", name="/learning-roadmap/ [Career Paths]")


class HeavyResourceStudent(HttpUser):
    """
    Cohort 3: Heavy operations (certificate verification, export downloads, PDF queries).
    Represents 15% of the active student population.
    """
    weight = 15
    wait_time = between(5, 12)

    def on_start(self):
        self.client.headers.update({
            'User-Agent': 'SkillSphereLoadBot/Phase18-HeavyResource',
            'Accept': 'text/html,application/xhtml+xml,application/json',
        })

    @task(20)
    def verify_certificate(self):
        self.client.get("/certificates/", name="/certificates/ [Certificate Center]")

    @task(15)
    def check_public_verification(self):
        self.client.get("/verify/SS-CERT-DEMO-001/", name="/verify/<code/ [Public Cert Verify]")

    @task(15)
    def read_metrics_health(self):
        self.client.get("/health/ready/", name="/health/ready/ [Readiness Probe]")
