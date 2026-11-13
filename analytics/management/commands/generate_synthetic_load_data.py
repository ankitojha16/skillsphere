import os
import uuid
import random
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction

from accounts.models import StudentProfile
from courses.models import Course, Enrollment, CourseCompletion, Category
from learning.models import Lesson, LessonProgress
from certificates.models import Certificate
from analytics.models import ProductEvent, BetaFeedback


class Command(BaseCommand):
    help = "Generates realistic synthetic student profiles, progress, and telemetry for load testing in staging."

    def add_arguments(self, parser):
        parser.add_argument('--students', type=int, default=2000, help="Number of synthetic students to create")
        parser.add_argument('--clean', action='store_true', help="Remove existing synthetic test data")

    def handle(self, *args, **options):
        # Strict Production Safeguard
        if os.getenv('VERCEL') or (not settings.DEBUG and os.getenv('ALLOW_SYNTHETIC_DATA') != 'True'):
            raise CommandError(
                "CRITICAL SAFEGUARD: Refusing to generate synthetic data on production. "
                "Synthetic accounts must only be generated in local or staging environments "
                "with ALLOW_SYNTHETIC_DATA=True."
            )

        prefix = "loadtest_user_"

        if options['clean']:
            self.stdout.write(self.style.WARNING("Cleaning up synthetic load test data..."))
            users = User.objects.filter(username__startswith=prefix)
            count = users.count()
            users.delete()
            self.stdout.write(self.style.SUCCESS(f"Cleaned up {count} synthetic test users."))
            return

        total_students = options['students']
        self.stdout.write(self.style.NOTICE(f"Generating {total_students} synthetic student accounts..."))

        courses = list(Course.objects.filter(is_published=True))
        if not courses:
            raise CommandError("No published courses found in database to attach synthetic enrollments.")

        now = timezone.now()
        existing_count = User.objects.filter(username__startswith=prefix).count()

        # Batch create users
        users_to_create = []
        for i in range(existing_count, existing_count + total_students):
            u = User(
                username=f"{prefix}{i}",
                email=f"synthetic_student_{i}@staging.skillsphere.local",
                first_name=f"Student",
                last_name=f"#{i}",
            )
            u.set_password("StagingLoadTest123!")
            users_to_create.append(u)

        created_users = User.objects.bulk_create(users_to_create, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f"Created {len(created_users)} User records."))

        # Refresh with IDs
        persisted_users = list(User.objects.filter(username__startswith=prefix).order_by('-id')[:total_students])

        # Batch create StudentProfiles
        interests_pool = ['web_dev', 'python', 'cloud_devops', 'data_science', 'system_design', 'ai_ml']
        profiles_to_create = []
        for u in persisted_users:
            profile = StudentProfile(
                user=u,
                primary_goal=random.choice(['career_switch', 'upskilling', 'interview_prep']),
                skill_level=random.choice(['beginner', 'intermediate', 'advanced']),
                interests=','.join(random.sample(interests_pool, k=random.randint(2, 4))),
                education_level=random.choice(['undergraduate', 'postgraduate', 'self_taught']),
                onboarding_completed=True,
                analytics_opt_out=False,
            )
            profiles_to_create.append(profile)

        StudentProfile.objects.bulk_create(profiles_to_create, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f"Created {len(profiles_to_create)} StudentProfile records."))

        # Batch create Enrollments and Progress
        enrollments_to_create = []
        completions_to_create = []
        progress_to_create = []
        certs_to_create = []
        events_to_create = []

        lessons_by_course = {}
        for c in courses:
            lessons_by_course[c.id] = list(c.lessons.all()[:8])

        for u in persisted_users:
            enrolled_courses = random.sample(courses, k=min(3, len(courses)))
            for c in enrolled_courses:
                enrollments_to_create.append(
                    Enrollment(user=u, course=c, enrolled_at=now - timedelta(days=random.randint(1, 30)))
                )
                
                # Progress
                course_lessons = lessons_by_course.get(c.id, [])
                num_completed = random.randint(0, len(course_lessons))
                for l in course_lessons[:num_completed]:
                    progress_to_create.append(
                        LessonProgress(user=u, lesson=l, is_completed=True, completed_at=now - timedelta(days=random.randint(1, 15)))
                    )

                pct = int((num_completed / len(course_lessons)) * 100) if course_lessons else 0
                is_comp = (pct >= 80)
                completions_to_create.append(
                    CourseCompletion(
                        user=u,
                        course=c,
                        learning_progress=pct,
                        is_completed=is_comp,
                        completed_at=(now - timedelta(days=1)) if is_comp else None
                    )
                )

                if is_comp and random.random() > 0.4:
                    certs_to_create.append(
                        Certificate(
                            user=u,
                            course=c,
                            certificate_id=f"CERT-{uuid.uuid4().hex[:10].upper()}",
                            verification_status=True,
                            issued_at=now - timedelta(days=random.randint(1, 10))
                        )
                    )

            # Telemetry events
            events_to_create.append(
                ProductEvent(
                    user=u,
                    event_type='login',
                    timestamp=now - timedelta(hours=random.randint(1, 48)),
                    metadata={'source': 'load_test'}
                )
            )

        Enrollment.objects.bulk_create(enrollments_to_create, batch_size=1000)
        CourseCompletion.objects.bulk_create(completions_to_create, batch_size=1000)
        LessonProgress.objects.bulk_create(progress_to_create, batch_size=1000)
        Certificate.objects.bulk_create(certs_to_create, batch_size=1000)
        ProductEvent.objects.bulk_create(events_to_create, batch_size=1000)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully generated synthetic dataset:\n"
            f"  - {len(persisted_users)} Users & Profiles\n"
            f"  - {len(enrollments_to_create)} Enrollments\n"
            f"  - {len(progress_to_create)} Lesson Progress records\n"
            f"  - {len(completions_to_create)} Course Completion records\n"
            f"  - {len(certs_to_create)} Certificates\n"
            f"  - {len(events_to_create)} Product Events"
        ))
