from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import json

from courses.models import Course, Enrollment
from learning.models import Lesson, LessonProgress
from goals.models import LearningGoal, LearningActivity
from gamification.services import get_or_create_gamification
from roadmaps.models import LearningRoadmap
from assessments.models import SkillAssessment, AssessmentAttempt
from projects.models import ProjectIdea

@login_required
def dashboard_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    # 1. Total Enrolled Courses
    enrollments = Enrollment.objects.filter(user=user).select_related('course', 'course__category').order_by('-enrolled_at')
    total_enrolled = enrollments.count()
    enrolled_course_ids = set(enrollments.values_list('course_id', flat=True))

    # 2. Compute per-course progress & completed courses
    completed_courses_count = 0
    enrolled_courses_data = []
    total_lessons_sum = 0
    completed_lessons_sum = 0

    for enrollment in enrollments:
        course = enrollment.course
        progress = course.get_user_progress(user)
        total_lessons_sum += progress['total']
        completed_lessons_sum += progress['completed']

        if progress['total'] > 0 and progress['percentage'] == 100:
            completed_courses_count += 1

        # Next incomplete lesson for this course
        completed_ids = set(
            LessonProgress.objects.filter(
                user=user,
                lesson__course=course,
                is_completed=True
            ).values_list('lesson_id', flat=True)
        )
        next_lesson = course.lessons.exclude(id__in=completed_ids).order_by('lesson_order').first()
        if not next_lesson:
            next_lesson = course.lessons.order_by('lesson_order').first()

        enrolled_courses_data.append({
            'course': course,
            'progress': progress,
            'next_lesson': next_lesson,
            'is_completed': progress['total'] > 0 and progress['percentage'] == 100,
        })

    # 3. Completed Lessons total
    total_completed_lessons = LessonProgress.objects.filter(user=user, is_completed=True).count()

    # 4. Overall Progress percentage
    overall_progress = int(round((completed_lessons_sum / total_lessons_sum) * 100)) if total_lessons_sum > 0 else 0

    # 5. Weekly Learning Activity for Chart.js (Last 7 days)
    today = timezone.now().date()
    chart_labels = []
    chart_counts = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_name = day.strftime('%a')
        chart_labels.append(day_name)
        count = LessonProgress.objects.filter(
            user=user,
            is_completed=True,
            completed_at__date=day
        ).count()
        chart_counts.append(count)

    # 6. Active and Recent Learning Goals
    active_goals = LearningGoal.objects.filter(user=user, is_completed=False).order_by('target_date')[:4]
    completed_goals_count = LearningGoal.objects.filter(user=user, is_completed=True).count()
    total_goals_count = LearningGoal.objects.filter(user=user).count()

    # 7. Recent Activity Feed
    recent_activities = LearningActivity.objects.filter(user=user).order_by('-created_at')[:8]

    # 8. Phase 2 Gamification (XP, Level, Streak)
    gamification = get_or_create_gamification(user)

    # 9. Phase 2 Roadmaps & Milestones
    active_roadmap = LearningRoadmap.objects.filter(user=user).order_by('-updated_at').first()
    roadmap_progress = active_roadmap.get_progress() if active_roadmap else {'percentage': 0, 'completed': 0, 'total': 0}
    pending_milestones = []
    if active_roadmap:
        pending_milestones = active_roadmap.milestones.filter(is_completed=False).order_by('milestone_order')[:3]

    # 10. Phase 2 Assessments Stats
    user_attempts = AssessmentAttempt.objects.filter(user=user)
    assessment_avg = 0
    if user_attempts.exists():
        total_pct = sum(a.percentage for a in user_attempts)
        assessment_avg = int(round(total_pct / user_attempts.count()))

    suggested_assessment = SkillAssessment.objects.filter(is_active=True).first()
    if profile and profile.get_interests_list():
        first_interest = profile.get_interests_list()[0]
        matching_assessment = SkillAssessment.objects.filter(
            is_active=True,
            title__icontains=first_interest
        ).first()
        if matching_assessment:
            suggested_assessment = matching_assessment

    # 11. Smart Course & Project Recommendations
    recommended_courses = Course.objects.filter(is_published=True).exclude(id__in=enrolled_course_ids)
    if profile and profile.get_interests_list():
        # Match by interests
        interest_names = [i.replace('_', ' ') for i in profile.get_interests_list()]
        q_courses = Course.objects.none()
        for term in interest_names:
            q_courses = q_courses | Course.objects.filter(is_published=True, title__icontains=term).exclude(id__in=enrolled_course_ids)
        if q_courses.exists():
            recommended_courses = q_courses.distinct()
    recommended_courses = list(recommended_courses[:3])

    recommended_projects = ProjectIdea.objects.filter(user=user)[:2]

    # 12. Dynamic AI Learning Summary
    ai_summary_points = []
    if gamification.current_streak > 1:
        ai_summary_points.append(f"🔥 You're on an active **{gamification.current_streak}-day learning streak**! Keep the momentum going.")
    else:
        ai_summary_points.append("Ready to learn! Complete a lesson today to ignite your study streak.")

    if active_roadmap:
        ai_summary_points.append(f"🗺️ Your **{active_roadmap.title}** is currently at **{roadmap_progress['percentage']}% completion**.")
    else:
        ai_summary_points.append("💡 Generate a personalized learning roadmap to guide your career path.")

    if total_completed_lessons > 0:
        ai_summary_points.append(f"📚 You have completed **{total_completed_lessons} lessons** across {total_enrolled} enrolled courses.")
    
    if suggested_assessment:
        ai_summary_points.append(f"🎯 Recommended next challenge: **{suggested_assessment.title}**.")

    context = {
        'student_profile': profile,
        'today_date': today,
        'total_enrolled': total_enrolled,
        'completed_courses_count': completed_courses_count,
        'total_completed_lessons': total_completed_lessons,
        'overall_progress': overall_progress,
        'enrolled_courses_data': enrolled_courses_data[:3],
        'active_goals': active_goals,
        'completed_goals_count': completed_goals_count,
        'total_goals_count': total_goals_count,
        'recent_activities': recent_activities,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_counts_json': json.dumps(chart_counts),
        
        # Phase 2 additions
        'gamification': gamification,
        'active_roadmap': active_roadmap,
        'roadmap_progress': roadmap_progress,
        'pending_milestones': pending_milestones,
        'assessment_avg': assessment_avg,
        'suggested_assessment': suggested_assessment,
        'recommended_courses': recommended_courses,
        'recommended_projects': recommended_projects,
        'ai_summary_points': ai_summary_points,
    }

    return render(request, 'dashboard/index.html', context)
