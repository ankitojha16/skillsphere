from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import json

from courses.models import Course, Enrollment, CourseCompletion
from learning.models import Lesson, LessonProgress
from goals.models import LearningGoal, LearningActivity
from gamification.services import get_or_create_gamification
from roadmaps.models import LearningRoadmap
from assessments.models import SkillAssessment, AssessmentAttempt
from projects.models import ProjectIdea

from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate

@login_required
def dashboard_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    # 1. Total Enrolled Courses (evaluated as list for reuse)
    enrollments = list(
        Enrollment.objects.filter(user=user)
        .select_related('course', 'course__category')
        .order_by('-enrolled_at')
    )
    total_enrolled = len(enrollments)
    enrolled_course_ids = [e.course_id for e in enrollments]

    # 2. Batch compute per-course progress & completed courses in 3 fast queries
    completed_courses_count = 0
    enrolled_courses_data = []
    total_lessons_sum = 0
    completed_lessons_sum = 0

    if enrolled_course_ids:
        completions = {
            c.course_id: c
            for c in CourseCompletion.objects.filter(user=user, course_id__in=enrolled_course_ids)
        }
        completed_lesson_ids = set(
            LessonProgress.objects.filter(
                user=user,
                is_completed=True,
                lesson__course_id__in=enrolled_course_ids
            ).values_list('lesson_id', flat=True)
        )
        lessons_by_course = {}
        for l in Lesson.objects.filter(course_id__in=enrolled_course_ids).order_by('lesson_order', 'id'):
            lessons_by_course.setdefault(l.course_id, []).append(l)

        for enrollment in enrollments:
            course = enrollment.course
            course_lessons = lessons_by_course.get(course.id, [])
            total_lessons = len(course_lessons)
            comp_count = sum(1 for l in course_lessons if l.id in completed_lesson_ids)

            comp = completions.get(course.id)
            calc_pct = min(100, int(round((comp_count / total_lessons) * 100))) if total_lessons > 0 else 0
            quiz_passed = comp.quiz_passed if comp else False
            mock_passed = comp.mock_passed if comp else False
            pct = calc_pct

            is_certificate_eligible = (pct >= 85 and quiz_passed and mock_passed)
            is_completed = (comp.is_completed if comp else False) or is_certificate_eligible

            if comp and (comp.learning_progress != pct or comp.is_completed != is_completed):
                comp.learning_progress = pct
                comp.is_completed = is_completed
                comp.save(update_fields=['learning_progress', 'is_completed', 'updated_at'])

            total_lessons_sum += total_lessons
            completed_lessons_sum += comp_count

            if is_completed:
                completed_courses_count += 1

            next_lesson = None
            for l in course_lessons:
                if l.id not in completed_lesson_ids:
                    next_lesson = l
                    break
            if not next_lesson and course_lessons:
                next_lesson = course_lessons[0]

            progress = {
                'percentage': pct,
                'completed': comp_count,
                'total': total_lessons,
                'is_completed': is_completed,
                'is_certificate_eligible': is_certificate_eligible,
                'is_unlocked': pct >= 80,
                'quiz_passed': quiz_passed,
                'mock_passed': mock_passed,
            }

            enrolled_courses_data.append({
                'course': course,
                'progress': progress,
                'next_lesson': next_lesson,
                'is_completed': is_completed,
            })

    # 3. Completed Lessons total
    total_completed_lessons = LessonProgress.objects.filter(user=user, is_completed=True).count()

    # 4. Overall Progress percentage
    overall_progress = int(round((completed_lessons_sum / total_lessons_sum) * 100)) if total_lessons_sum > 0 else 0

    # 5. Weekly Learning Activity for Chart.js (Last 7 days in 1 single aggregation query)
    today = timezone.now().date()
    week_start = today - timedelta(days=6)
    activity_by_day = dict(
        LessonProgress.objects.filter(
            user=user,
            is_completed=True,
            completed_at__date__gte=week_start
        ).annotate(day=TruncDate('completed_at')).values('day').annotate(cnt=Count('id')).values_list('day', 'cnt')
    )

    chart_labels = []
    chart_counts = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime('%a'))
        chart_counts.append(activity_by_day.get(day, 0))

    # 6. Active and Recent Learning Goals
    goals_qs = list(LearningGoal.objects.filter(user=user).order_by('target_date'))
    active_goals = [g for g in goals_qs if not g.is_completed][:4]
    completed_goals_count = sum(1 for g in goals_qs if g.is_completed)
    total_goals_count = len(goals_qs)

    # 7. Recent Activity Feed
    recent_activities = list(LearningActivity.objects.filter(user=user).order_by('-created_at')[:8])

    # 8. Phase 2 Gamification (XP, Level, Streak)
    gamification = get_or_create_gamification(user)

    # 9. Phase 2 Roadmaps & Milestones
    active_roadmap = LearningRoadmap.objects.filter(user=user).order_by('-updated_at').first()
    roadmap_progress = active_roadmap.get_progress() if active_roadmap else {'percentage': 0, 'completed': 0, 'total': 0}
    pending_milestones = []
    if active_roadmap:
        pending_milestones = list(active_roadmap.milestones.filter(is_completed=False).order_by('milestone_order')[:3])

    # 10. Phase 2 Assessments Stats (Single Aggregation)
    assessment_agg = AssessmentAttempt.objects.filter(user=user).aggregate(avg_score=Avg('percentage'))
    assessment_avg = int(round(assessment_agg['avg_score'])) if assessment_agg['avg_score'] is not None else 0

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
    recommended_courses = Course.objects.filter(is_published=True).select_related('category').exclude(id__in=enrolled_course_ids)
    if profile and profile.get_interests_list():
        interest_names = [i.replace('_', ' ') for i in profile.get_interests_list()]
        q_interest = Q()
        for term in interest_names:
            q_interest |= Q(title__icontains=term)
        if q_interest:
            matched_rec = recommended_courses.filter(q_interest)
            if matched_rec.exists():
                recommended_courses = matched_rec
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
