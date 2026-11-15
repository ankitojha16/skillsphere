from django.urls import reverse
from accounts.models import StudentProfile
from courses.models import Enrollment
from careers.models import StudentCareerGoal
from roadmaps.models import LearningRoadmap
from workspace.models import WorkspaceTask
from projects.models import ProjectIdea


class OnboardingLaunchpadService:
    """
    Computes real-time progress across the 6 foundational milestones for new SkillSphere students.
    Zero fabrication: strictly reads authentic student database records.
    """

    @classmethod
    def get_status(cls, user):
        if not user.is_authenticated:
            return None

        profile, _ = StudentProfile.objects.get_or_create(user=user)

        step_profile = bool(profile.onboarding_completed)
        step_track = StudentCareerGoal.objects.filter(user=user, status='active').exists()
        step_course = Enrollment.objects.filter(user=user).exists()
        step_roadmap = LearningRoadmap.objects.filter(user=user).exists()
        step_task = WorkspaceTask.objects.filter(user=user).exists()
        step_project = ProjectIdea.objects.filter(user=user).exists()

        steps = [
            {
                'id': 'profile',
                'title': 'Complete Student Profile',
                'description': 'Set your learning background, education level, and tech interests.',
                'is_completed': step_profile,
                'url': reverse('accounts:profile_setup'),
                'icon': 'user-check',
                'action_label': 'Edit Profile' if step_profile else 'Complete Profile',
            },
            {
                'id': 'career_track',
                'title': 'Select Career Track',
                'description': 'Choose from 11 curated engineering tracks like Full Stack, Python, or AI/ML.',
                'is_completed': step_track,
                'url': reverse('careers:studio_paths'),
                'action_label': 'View Track' if step_track else 'Select Track',
            },
            {
                'id': 'course_enrollment',
                'title': 'Enroll in First Course',
                'description': 'Choose from 69 comprehensive courses with structured video lessons.',
                'is_completed': step_course,
                'url': reverse('courses:list'),
                'action_label': 'Browse Courses' if not step_course else 'View Learning',
            },
            {
                'id': 'roadmap',
                'title': 'Generate Learning Roadmap',
                'description': 'Unlock your milestone-driven sequence of skills and curriculum targets.',
                'is_completed': step_roadmap,
                'url': reverse('careers:studio_roadmap'),
                'action_label': 'View Roadmap' if step_roadmap else 'Generate Roadmap',
            },
            {
                'id': 'daily_plan',
                'title': 'Set Your Daily Focus Plan',
                'description': 'Schedule your first learning task in your smart Workspace planner.',
                'is_completed': step_task,
                'url': reverse('workspace:planner'),
                'action_label': 'Open Planner' if step_task else 'Add Daily Task',
            },
            {
                'id': 'portfolio_project',
                'title': 'Initialize Portfolio Project',
                'description': 'Create your first project idea to build demonstrable proof of competence.',
                'is_completed': step_project,
                'url': reverse('careers:create_studio_project'),
                'action_label': 'View Projects' if step_project else 'Create Project',
            },
        ]

        completed_count = sum(1 for s in steps if s['is_completed'])
        total_steps = len(steps)
        progress_pct = int(round((completed_count / total_steps) * 100))

        return {
            'steps': steps,
            'completed_count': completed_count,
            'total_steps': total_steps,
            'progress_percent': progress_pct,
            'is_all_completed': completed_count == total_steps,
        }
