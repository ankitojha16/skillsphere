from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from .forms import UserRegistrationForm, UserLoginForm, ProfileSetupForm
from .models import StudentProfile
from goals.models import LearningActivity
from analytics.services import track_event

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            full_name = form.cleaned_data['full_name']

            # Use email as username or sanitized base
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            names = full_name.split(' ', 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ''

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Signal auto-creates StudentProfile, but let's ensure full_name is populated
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            profile.full_name = full_name
            profile.save()

            # Log registration activity
            LearningActivity.objects.create(
                user=user,
                activity_type='ENROLL',
                description=f"Joined SkillSphere! Welcome, {full_name}."
            )

            # Privacy-conscious first-party telemetry
            track_event(
                user=user,
                event_type='registration_completed',
                metadata={'method': 'email_signup'},
                event_key=f"reg_{user.id}"
            )

            # Log user in
            login(request, user)
            messages.success(request, f"Welcome to SkillSphere, {full_name}! Let's set up your learning preferences.")
            return redirect('accounts:profile_setup')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)

            # Brute force protection: 5 attempts per 15 minutes
            ip = request.META.get('REMOTE_ADDR', 'unknown')
            lockout_key = f"login_lockout_{email}_{ip}"
            failed_attempts = cache.get(lockout_key, 0)

            if failed_attempts >= 5:
                messages.error(request, "Too many failed login attempts. Please wait 15 minutes before trying again.")
                return render(request, 'accounts/login.html', {'form': form})

            # Look up username by email
            user_obj = User.objects.filter(email__iexact=email).first()
            user = None
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                # Clear lockout on success
                cache.delete(lockout_key)

                is_first_login = (user.last_login is None)
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)  # Browser close session
                else:
                    request.session.set_expiry(1209600)  # 2 weeks

                # Telemetry
                if is_first_login:
                    track_event(user=user, event_type='first_login', event_key=f"first_login_{user.id}")
                track_event(user=user, event_type='login')

                messages.success(request, f"Welcome back, {user.profile.full_name or user.username}!")
                next_url = request.GET.get('next')
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect('dashboard:index')
            else:
                new_attempts = failed_attempts + 1
                cache.set(lockout_key, new_attempts, timeout=900)
                remaining = max(0, 5 - new_attempts)
                if remaining > 0:
                    messages.error(request, f"Invalid email address or password. ({remaining} attempt{'s' if remaining != 1 else ''} remaining)")
                else:
                    messages.error(request, "Too many failed login attempts. Your account has been temporarily locked for 15 minutes.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('accounts:login')


@login_required
def profile_setup_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    # Allow skip
    if request.GET.get('skip') == '1':
        profile.onboarding_completed = True
        profile.save(update_fields=['onboarding_completed'])
        track_event(user=request.user, event_type='onboarding_completed', metadata={'status': 'skipped'}, event_key=f"onboard_{request.user.id}")
        messages.info(request, "Setup skipped. You can personalize your learning preferences anytime in profile settings.")
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = ProfileSetupForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            try:
                form.save()
                profile.onboarding_completed = True
                profile.save(update_fields=['onboarding_completed'])
                track_event(
                    user=request.user,
                    event_type='onboarding_completed',
                    metadata={
                        'learning_level': profile.learning_level,
                        'education_level': profile.education_level,
                        'career_goal': profile.career_goal,
                    },
                    event_key=f"onboard_{request.user.id}"
                )
                messages.success(request, "Preferences saved! Here are your recommended starter courses.")
                return redirect('accounts:onboarding_recommendations')
            except Exception as e:
                import logging
                logging.getLogger(__name__).exception("Profile setup save failed: %s", e)
                profile.onboarding_completed = True
                profile.save(update_fields=['onboarding_completed'])
                messages.warning(request, "Your preferences were saved. You can update your avatar anytime in settings.")
                return redirect('accounts:onboarding_recommendations')
    else:
        form = ProfileSetupForm(instance=profile)

    interest_options = StudentProfile.AVAILABLE_INTERESTS
    selected_interests = profile.get_interests_list()

    return render(request, 'accounts/profile_setup.html', {
        'form': form,
        'profile': profile,
        'interest_options': interest_options,
        'selected_interests': selected_interests,
    })


@login_required
def onboarding_recommendations_view(request):
    """
    Step 2 of beta onboarding: Displays personalized starter course recommendations
    and direct link to start the first lesson.
    """
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    interests = profile.get_interests_list()

    from django.db.models import Q
    from courses.models import Course
    from learning.models import Lesson

    interest_keywords = {
        'python': 'Python',
        'cpp': 'C++',
        'java': 'Java',
        'web_dev': 'Web',
        'dsa': 'Data Structures',
        'ai': 'AI',
        'data_science': 'Data Science',
        'dbms': 'Database',
    }

    matched_courses = []
    if interests:
        query = Q()
        for i in interests:
            kw = interest_keywords.get(i, i)
            query |= Q(title__icontains=kw) | Q(category__name__icontains=kw) | Q(description__icontains=kw)
        matched_courses = list(Course.objects.filter(query, is_published=True).distinct()[:4])

    if len(matched_courses) < 3:
        fallback_courses = list(Course.objects.filter(is_published=True).exclude(id__in=[c.id for c in matched_courses])[:4 - len(matched_courses)])
        matched_courses.extend(fallback_courses)

    top_course = matched_courses[0] if matched_courses else None
    first_lesson = None
    if top_course:
        first_lesson = Lesson.objects.filter(course=top_course).order_by('lesson_order', 'id').first()

    from careers.models import CareerTrack, StudentCareerGoal
    career_tracks = list(CareerTrack.objects.filter(is_active=True).order_by('display_order')[:4])
    active_career_goal = StudentCareerGoal.objects.filter(user=request.user).select_related('primary_track').first()

    suggested_project = None
    if active_career_goal and active_career_goal.primary_track and active_career_goal.primary_track.suggested_projects:
        suggested_project = active_career_goal.primary_track.suggested_projects[0]
    elif career_tracks and career_tracks[0].suggested_projects:
        suggested_project = career_tracks[0].suggested_projects[0]

    from .onboarding_service import OnboardingLaunchpadService
    return render(request, 'accounts/onboarding_recommendations.html', {
        'profile': profile,
        'recommended_courses': matched_courses,
        'top_course': top_course,
        'first_lesson': first_lesson,
        'career_tracks': career_tracks,
        'active_career_goal': active_career_goal,
        'suggested_project': suggested_project,
        'onboarding_launchpad': OnboardingLaunchpadService.get_status(request.user),
    })


@login_required
def export_user_data_view(request):
    """
    Exports all personal student data, learning activity, progress, and certificates
    as a downloadable JSON archive.
    Strictly excludes internal staff notes, secrets, and other users' records.
    """
    import json
    from django.http import HttpResponse
    from django.utils import timezone
    from courses.models import Enrollment, CourseCompletion
    from learning.models import LessonProgress
    from certificates.models import Certificate
    from assessments.models import AssessmentAttempt
    from analytics.models import BetaFeedback

    user = request.user
    profile, _ = StudentProfile.objects.get_or_create(user=user)

    from workspace.models import WorkspaceTask, CalendarEvent, FocusSession, PersonalNote, WorkspaceBookmark
    from projects.models import ProjectIdea
    from resumes.models import Resume
    from opportunities.models import SavedOpportunity

    data = {
        'export_metadata': {
            'exported_at': timezone.now().isoformat(),
            'platform': 'SkillSphere Beta',
            'user_id': user.id,
            'username': user.username,
        },
        'profile': {
            'full_name': profile.full_name or user.get_full_name(),
            'username': user.username,
            'email': user.email,
            'role': profile.role,
            'learning_level': profile.learning_level,
            'education_level': profile.education_level,
            'institution': profile.institution,
            'career_goal': profile.career_goal,
            'interests': profile.get_interests_list(),
            'analytics_opt_out': profile.analytics_opt_out,
            'date_joined': user.date_joined.isoformat() if user.date_joined else None,
        },
        'enrollments': [
            {
                'course_title': e.course.title,
                'course_slug': e.course.slug,
                'enrolled_at': e.enrolled_at.isoformat() if hasattr(e, 'enrolled_at') and e.enrolled_at else None,
            }
            for e in Enrollment.objects.filter(user=user).select_related('course')
        ],
        'lesson_progress': [
            {
                'lesson_title': lp.lesson.title,
                'course_title': lp.lesson.course.title if lp.lesson.course else '',
                'is_completed': lp.is_completed,
                'completed_at': lp.completed_at.isoformat() if lp.completed_at else None,
            }
            for lp in LessonProgress.objects.filter(user=user).select_related('lesson', 'lesson__course')
        ],
        'course_completions': [
            {
                'course_title': cc.course.title,
                'is_completed': cc.is_completed,
                'completed_at': cc.completed_at.isoformat() if cc.completed_at else None,
            }
            for cc in CourseCompletion.objects.filter(user=user).select_related('course')
        ],
        'certificates': [
            {
                'certificate_code': c.certificate_code,
                'course_title': c.course.title if c.course else '',
                'issued_at': c.issued_at.isoformat() if c.issued_at else None,
                'grade': c.grade,
                'verification_url': c.verification_url if hasattr(c, 'verification_url') else '',
            }
            for c in Certificate.objects.filter(user=user).select_related('course')
        ],
        'assessment_attempts': [
            {
                'assessment_title': a.assessment.title if a.assessment else '',
                'score': a.score,
                'total_questions': a.total_questions,
                'percentage': a.percentage,
                'completed_at': a.completed_at.isoformat() if a.completed_at else None,
            }
            for a in AssessmentAttempt.objects.filter(user=user).select_related('assessment')
        ],
        'feedback_submissions': [
            {
                'category': f.category,
                'description': f.description,
                'rating': f.rating,
                'status': f.status,
                'created_at': f.created_at.isoformat(),
            }
            for f in BetaFeedback.objects.filter(user=user)
        ],
        'workspace': {
            'tasks': [
                {
                    'title': t.title,
                    'is_completed': t.is_completed,
                    'priority': t.priority,
                    'task_type': t.task_type,
                    'due_date': t.due_date.isoformat() if t.due_date else None,
                    'estimated_minutes': t.estimated_minutes,
                }
                for t in WorkspaceTask.objects.filter(user=user)
            ],
            'calendar_events': [
                {
                    'title': ev.title,
                    'event_type': ev.event_type,
                    'start_time': ev.start_time.isoformat() if ev.start_time else None,
                    'end_time': ev.end_time.isoformat() if ev.end_time else None,
                }
                for ev in CalendarEvent.objects.filter(user=user)
            ],
            'focus_sessions': [
                {
                    'session_type': fs.session_type,
                    'duration_minutes': fs.duration_minutes,
                    'completed': fs.completed,
                    'notes': fs.notes,
                    'created_at': fs.created_at.isoformat() if fs.created_at else None,
                }
                for fs in FocusSession.objects.filter(user=user)
            ],
            'personal_notes': [
                {
                    'title': n.title,
                    'content': n.content,
                    'folder': n.folder,
                    'is_pinned': n.is_pinned,
                    'created_at': n.created_at.isoformat() if n.created_at else None,
                }
                for n in PersonalNote.objects.filter(user=user)
            ],
            'bookmarks': [
                {
                    'title': b.title,
                    'url': b.url,
                    'bookmark_type': b.bookmark_type,
                    'category': b.category,
                    'notes': b.notes,
                }
                for b in WorkspaceBookmark.objects.filter(user=user)
            ],
        },
        'career_portfolio': {
            'projects': [
                {
                    'title': p.title,
                    'status': p.status,
                    'description': p.description,
                    'demo_url': p.demo_url,
                    'github_url': p.github_url,
                    'is_public': p.is_public,
                }
                for p in ProjectIdea.objects.filter(user=user)
            ],
            'resumes': [
                {
                    'title': r.title,
                    'ats_score': r.ats_score,
                    'summary': r.summary,
                    'updated_at': r.updated_at.isoformat() if r.updated_at else None,
                }
                for r in Resume.objects.filter(user=user)
            ],
            'applications': [
                {
                    'opportunity': app.opportunity.title if app.opportunity else '',
                    'organization': app.opportunity.organization if app.opportunity else '',
                    'status': app.application_status,
                    'applied_at': app.applied_at.isoformat() if app.applied_at else None,
                }
                for app in SavedOpportunity.objects.filter(user=user).select_related('opportunity')
            ],
        }
    }

    json_bytes = json.dumps(data, indent=2).encode('utf-8')
    response = HttpResponse(json_bytes, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="skillsphere_data_export_{user.username}.json"'
    return response


@login_required
def delete_account_view(request):
    """
    Self-service account deletion.
    - Requires explicit POST with password confirmation and CSRF protection.
    - Permanently deletes User and cascading records (profile, enrollments, progress, certificates).
    - Logs user out immediately.
    """
    if request.method == 'POST':
        password = request.POST.get('password', '')
        if not request.user.check_password(password):
            messages.error(request, "Incorrect password. Account deletion was cancelled to protect your security.")
            return render(request, 'accounts/delete_account.html')

        user = request.user
        username = user.username
        logout(request)
        user.delete()

        messages.success(request, f"Your SkillSphere account (@{username}) and personal learning data have been permanently removed.")
        return redirect('courses:list')

    return render(request, 'accounts/delete_account.html')


@login_required
def profile_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    interests_display = []
    interests_map = dict(StudentProfile.AVAILABLE_INTERESTS)
    for i in profile.get_interests_list():
        interests_display.append(interests_map.get(i, i))

    enrolled_count = request.user.enrollments.count()
    completed_goals_count = request.user.goals.filter(is_completed=True).count()
    total_goals_count = request.user.goals.count()

    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'interests_display': interests_display,
        'enrolled_count': enrolled_count,
        'completed_goals_count': completed_goals_count,
        'total_goals_count': total_goals_count,
    })


@login_required
def profile_edit_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileSetupForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Your profile details have been updated.")
                return redirect('accounts:profile')
            except Exception as e:
                import logging
                logging.getLogger(__name__).exception("Profile update save failed: %s", e)
                messages.error(request, "Could not process avatar image. Please try an external image URL instead.")
    else:
        form = ProfileSetupForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {
        'form': form,
        'profile': profile,
        'interest_options': StudentProfile.AVAILABLE_INTERESTS,
        'selected_interests': profile.get_interests_list(),
    })
