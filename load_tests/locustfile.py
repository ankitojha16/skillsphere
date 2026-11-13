"""
SkillSphere Enterprise Locust Load Test Suite
Simulates 10,000 concurrent active users distributed across 5 realistic learner personas:
- AnonymousVisitor (25% weight)
- EnrolledStudent (45% weight)
- AssessmentCandidate (10% weight)
- CertificateVerifier (15% weight)
- CommunityCollaborator (5% weight)
"""

import json
import random
from locust import HttpUser, task, between, events

class AnonymousVisitor(HttpUser):
    weight = 25
    wait_time = between(8, 16)

    @task(4)
    def browse_courses(self):
        page = random.randint(1, 4)
        cat = random.choice(['all', 'engineering-tech', 'management-business', 'computer-applications'])
        self.client.get(f"/courses/?category={cat}&page={page}", name="/courses/ [filter]")

    @task(3)
    def search_autocomplete(self):
        query = random.choice(['python', 'web', 'data', 'cloud', 'system', 'react', 'sql'])
        self.client.get(f"/courses/api/search/autocomplete/?q={query}", name="/courses/api/search/autocomplete/")

    @task(2)
    def view_course_detail(self):
        slug = random.choice([
            'python-programming-from-scratch',
            'full-stack-django-web-dev',
            'mastering-dsa-with-python',
            'postgresql-database-mastery',
            'strategic-management-mba'
        ])
        self.client.get(f"/courses/{slug}/", name="/courses/[slug]/")

    @task(1)
    def view_legal_pages(self):
        self.client.get("/privacy/", name="/privacy/")
        self.client.get("/terms/", name="/terms/")


class EnrolledStudent(HttpUser):
    weight = 45
    wait_time = between(15, 35)

    def on_start(self):
        # Emulate session authentication
        self.user_idx = random.randint(1, 2000)
        self.headers = {"X-Load-User": f"student_{self.user_idx}"}

    @task(3)
    def view_dashboard(self):
        self.client.get("/dashboard/", headers=self.headers, name="/dashboard/")

    @task(4)
    def view_lesson(self):
        course_slug = 'python-programming-from-scratch'
        lesson_id = random.randint(1, 16)
        self.client.get(f"/learn/{course_slug}/{lesson_id}/", headers=self.headers, name="/learn/[course]/[lesson]/")

    @task(2)
    def ping_video_progress(self):
        pos = random.randint(30, 480)
        self.client.post(
            "/learn/api/video-progress/",
            json={"lesson_id": random.randint(1, 16), "position": pos, "duration": 600},
            headers=self.headers,
            name="/learn/api/video-progress/"
        )

    @task(1)
    def mark_lesson_complete(self):
        lesson_id = random.randint(1, 16)
        self.client.post(
            f"/learn/python-programming-from-scratch/{lesson_id}/complete/",
            headers=self.headers,
            name="/learn/[course]/[lesson]/complete/"
        )


class AssessmentCandidate(HttpUser):
    weight = 10
    wait_time = between(20, 40)

    @task(2)
    def view_assessments_catalogue(self):
        self.client.get("/skill-assessment/", name="/skill-assessment/")

    @task(1)
    def attempt_assessment(self):
        # Simulate answering question in a skill assessment
        self.client.get("/skill-assessment/python-core/", name="/skill-assessment/[slug]/")


class CertificateVerifier(HttpUser):
    weight = 15
    wait_time = between(10, 25)

    @task(3)
    def verify_certificate(self):
        sample_cert_id = f"CERT-{random.randint(1000, 9999)}"
        self.client.get(f"/certificates/verify/{sample_cert_id}/", name="/certificates/verify/[id]/")


class CommunityCollaborator(HttpUser):
    weight = 5
    wait_time = between(15, 30)

    @task(2)
    def view_community_threads(self):
        self.client.get("/community/", name="/community/")

    @task(1)
    def submit_feedback(self):
        self.client.get("/feedback/", name="/feedback/")
