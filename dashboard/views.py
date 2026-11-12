from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json

from courses.models import Course, Enrollment, CourseCompletion
from learning.models import Lesson, LessonProgress
from goals.models import LearningGoal, LearningActivity
from gamification.services import get_or_create_gamification, award_user_xp
from roadmaps.models import LearningRoadmap
from assessments.models import SkillAssessment, AssessmentAttempt
from projects.models import ProjectIdea
from certificates.models import Certificate

from django.core.cache import cache
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate, Coalesce

@login_required
def dashboard_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    cache_key = f"user_dashboard_payload_{user.id}"
    cached_context = cache.get(cache_key)
    if cached_context is not None:
        cached_context['student_profile'] = profile
        cached_context['today_date'] = timezone.now().date()
        return render(request, 'dashboard/index.html', cached_context)

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

        from courses.models import CourseAssessment
        course_ids_with_assessments = set(
            CourseAssessment.objects.filter(course_id__in=enrolled_course_ids, is_active=True).values_list('course_id', flat=True)
        )
        cert_course_ids = set(
            Certificate.objects.filter(user=user, course_id__in=enrolled_course_ids, verification_status=True).values_list('course_id', flat=True)
        )

        for enrollment in enrollments:
            course = enrollment.course
            course_lessons = lessons_by_course.get(course.id, [])
            total_l = len(course_lessons)
            course.total_lessons = total_l
            comp = completions.get(course.id)

            comp_lessons_count = sum(1 for l in course_lessons if l.id in completed_lesson_ids)
            total_lessons_sum += total_l
            completed_lessons_sum += comp_lessons_count

            video_ratio = (comp_lessons_count / total_l) if total_l > 0 else 0.0
            video_pct = int(round(video_ratio * 100))
            is_cert_eligible = (video_pct >= 100) or (course.id in cert_course_ids)

            base_weighted = int(round(video_ratio * 80.0))
            if comp:
                weighted_prog = max(base_weighted, comp.learning_progress)
                is_comp = comp.is_completed or is_cert_eligible
            else:
                weighted_prog = base_weighted
                is_comp = is_cert_eligible

            bonus_pct = max(0, weighted_prog - base_weighted)
            if is_comp:
                completed_courses_count += 1

            prog = {
                'percentage': weighted_prog,
                'overall_progress': weighted_prog,
                'weighted_course_progress': weighted_prog,
                'video_completion_percentage': video_pct,
                'assessment_bonus_percentage': bonus_pct,
                'completed': comp_lessons_count,
                'total': total_l,
                'is_completed': is_comp,
                'is_certificate_eligible': is_cert_eligible,
                'is_unlocked': course.id in course_ids_with_assessments,
                'has_optional_assessments': course.id in course_ids_with_assessments,
            }

            next_lesson = None
            for l in course_lessons:
                if l.id not in completed_lesson_ids:
                    next_lesson = l
                    break
            if not next_lesson and course_lessons:
                next_lesson = course_lessons[0]

            enrolled_courses_data.append({
                'course': course,
                'progress': prog,
                'next_lesson': next_lesson,
                'is_completed': is_comp,
            })

    in_progress_courses = [c for c in enrolled_courses_data if not c['is_completed']]
    completed_courses = [c for c in enrolled_courses_data if c['is_completed']]

    # 3-Part Course Progress Breakdown for Dashboard Analytics
    n_enrolled = len(enrolled_courses_data)
    if n_enrolled > 0:
        avg_video_completion = int(round(sum(c['progress']['video_completion_percentage'] for c in enrolled_courses_data) / n_enrolled))
        avg_weighted_progress = int(round(sum(c['progress']['weighted_course_progress'] for c in enrolled_courses_data) / n_enrolled))
        avg_assessment_bonus = int(round(sum(c['progress']['assessment_bonus_percentage'] for c in enrolled_courses_data) / n_enrolled))
    else:
        avg_video_completion = 0
        avg_weighted_progress = 0
        avg_assessment_bonus = 0

    primary_next_step = None
    for item in in_progress_courses:
        if item.get('next_lesson'):
            primary_next_step = {
                'course': item['course'],
                'lesson': item['next_lesson'],
                'progress': item['progress'],
            }
            break

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
            completed_at__isnull=False,
            completed_at__date__gte=week_start
        )
        .annotate(day=TruncDate('completed_at'))
        .values('day')
        .annotate(cnt=Count('id'))
        .values_list('day', 'cnt')
    )

    chart_labels = []
    chart_counts = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime('%a'))
        chart_counts.append(activity_by_day.get(day, 0))

    weekly_lessons_completed = sum(chart_counts)

    # 5b. 52-Week Study Activity Heatmap (364 days / 52 full weeks)
    heatmap_start = today - timedelta(days=363)
    lesson_activity_year = dict(
        LessonProgress.objects.filter(
            user=user,
            is_completed=True,
            completed_at__isnull=False,
            completed_at__date__gte=heatmap_start
        )
        .annotate(day=TruncDate('completed_at'))
        .values('day')
        .annotate(cnt=Count('id'))
        .values_list('day', 'cnt')
    )

    extra_activity_year = dict(
        LearningActivity.objects.filter(
            user=user,
            created_at__date__gte=heatmap_start
        ).annotate(day=TruncDate('created_at')).values('day').annotate(cnt=Count('id')).values_list('day', 'cnt')
    )

    heatmap_days = []
    total_active_days = 0
    annual_study_actions = 0

    for i in range(363, -1, -1):
        d = today - timedelta(days=i)
        lessons_cnt = lesson_activity_year.get(d, 0)
        extra_cnt = extra_activity_year.get(d, 0)
        cnt = lessons_cnt + extra_cnt
        if cnt > 0:
            total_active_days += 1
            annual_study_actions += cnt

        # Level 0 to 4
        if cnt == 0:
            lvl = 0
        elif cnt == 1:
            lvl = 1
        elif cnt <= 3:
            lvl = 2
        elif cnt <= 5:
            lvl = 3
        else:
            lvl = 4

        heatmap_days.append({
            'date': d.strftime('%Y-%m-%d'),
            'display_date': d.strftime('%b %d, %Y'),
            'count': cnt,
            'lessons': lessons_cnt,
            'level': lvl,
            'weekday': d.weekday()  # 0=Mon, 6=Sun
        })

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

    # 11. Smart Course & Project Recommendations (Evaluated without redundant exists checks)
    recommended_courses_qs = Course.objects.filter(is_published=True).select_related('category').exclude(id__in=enrolled_course_ids)
    if profile and profile.get_interests_list():
        interest_names = [i.replace('_', ' ') for i in profile.get_interests_list()]
        q_interest = Q()
        for term in interest_names:
            q_interest |= Q(title__icontains=term)
        matched_rec = list(recommended_courses_qs.filter(q_interest)[:3])
        if matched_rec:
            recommended_courses = matched_rec
        else:
            recommended_courses = list(recommended_courses_qs[:3])
    else:
        recommended_courses = list(recommended_courses_qs[:3])

    recommended_projects = list(ProjectIdea.objects.filter(user=user)[:2])

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
    
    # 13. Earned Certificates
    user_certificates = list(
        Certificate.objects.filter(user=user, verification_status=True)
        .select_related('course', 'course__category')
        .order_by('-issued_at')
    )

    context = {
        'student_profile': profile,
        'today_date': today,
        'total_enrolled': total_enrolled,
        'completed_courses_count': completed_courses_count,
        'total_completed_lessons': total_completed_lessons,
        'overall_progress': overall_progress,
        'enrolled_courses_data': enrolled_courses_data,
        'in_progress_courses': in_progress_courses,
        'completed_courses': completed_courses,
        'primary_next_step': primary_next_step,
        'user_certificates': user_certificates,
        'user_certificates_count': len(user_certificates),
        'active_goals': active_goals,
        'completed_goals_count': completed_goals_count,
        'total_goals_count': total_goals_count,
        'recent_activities': recent_activities,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_counts_json': json.dumps(chart_counts),
        'heatmap_days_json': json.dumps(heatmap_days),
        'total_active_days': total_active_days,
        'annual_study_actions': annual_study_actions,
        
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

        # Phase 13 Progress Breakdown & Weekly Analytics
        'avg_video_completion': avg_video_completion,
        'avg_weighted_progress': avg_weighted_progress,
        'avg_assessment_bonus': avg_assessment_bonus,
        'weekly_lessons_completed': weekly_lessons_completed,
        'weekly_in_progress_count': len(in_progress_courses),
        'weekly_goals_achieved': completed_goals_count,
        'weekly_milestones_pending': len(pending_milestones),
    }

    try:
        cache.set(cache_key, context, 60)
    except Exception:
        pass

    return render(request, 'dashboard/index.html', context)


@login_required
def study_lounge_view(request):
    """
    Virtual Study Lounge & Ambient Pomodoro Focus Hub.
    Combines synchronized focus timer, Web Audio ambient generator, and task tracking.
    """
    today = timezone.now().date()
    today_sessions = LearningActivity.objects.filter(
        user=request.user,
        activity_type='FOCUS_SESSION',
        created_at__date=today
    )
    today_pomodoros = today_sessions.count()
    today_minutes = today_pomodoros * 25

    enrolled_courses = Course.objects.filter(enrollments__user=request.user).distinct()
    gamification = get_or_create_gamification(request.user)

    return render(request, 'dashboard/study_lounge.html', {
        'today_pomodoros': today_pomodoros,
        'today_minutes': today_minutes,
        'enrolled_courses': enrolled_courses,
        'gamification': gamification,
    })


@login_required
def log_focus_session_view(request):
    """
    Records a completed Pomodoro focus session, awards +25 XP, and updates the activity heatmap.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        if request.content_type == 'application/json':
            body = json.loads(request.body)
        else:
            body = request.POST

        minutes = int(body.get('minutes', 25))
        course_id = body.get('course_id')
        notes = body.get('notes', '').strip()

        desc = f"Completed {minutes}-minute Pomodoro focus block"
        if course_id:
            course = Course.objects.filter(id=course_id).first()
            if course:
                desc += f" on {course.title}"

        # 1. Log activity to feed 52-week heatmap
        LearningActivity.objects.create(
            user=request.user,
            activity_type='FOCUS_SESSION',
            reference_id=course_id if course_id else None,
            description=desc
        )

        # 2. Award XP via gamification
        award_user_xp(request.user, 25, "Pomodoro Focus Block")

        # 3. Invalidate dashboard cache for immediate heatmap reflection
        cache.delete(f"user_dashboard_payload_{request.user.id}")

        today = timezone.now().date()
        today_sessions = LearningActivity.objects.filter(
            user=request.user,
            activity_type='FOCUS_SESSION',
            created_at__date=today
        )
        total_poms = today_sessions.count()
        total_mins = total_poms * 25

        return JsonResponse({
            'success': True,
            'xp_awarded': 25,
            'today_pomodoros': total_poms,
            'today_minutes': total_mins,
            'message': f"Great focus! +25 XP awarded and logged to your activity heatmap."
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_daily_micro_drill_api(request):
    """
    Returns today's 3 personalized micro-drill flashcards for daily knowledge retention.
    """
    from learning.spaced_repetition import get_personalized_daily_drills
    cards = get_personalized_daily_drills(request.user, count=3)
    
    # Hide the correct answers from the client payload during questioning
    client_cards = []
    for c in cards:
        client_cards.append({
            'id': c['id'],
            'category': c['category'],
            'question': c['question'],
            'options': c['options'],
        })
        
    today_str = timezone.now().strftime('%Y-%m-%d')
    done_cache_key = f"user_drill_completed_{request.user.id}_{today_str}"
    is_completed_today = bool(cache.get(done_cache_key))

    return JsonResponse({
        'success': True,
        'cards': client_cards,
        'is_completed_today': is_completed_today,
        'xp_reward': 15,
    })


@login_required
def submit_daily_micro_drill_api(request):
    """
    Validates micro-drill answers, calculates SM-2 memory retention metrics,
    and awards +15 XP and maintains streak progression.
    """
    from learning.spaced_repetition import get_personalized_daily_drills, calculate_sm2
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    user_answers = data.get('answers', {})  # {'drill_id': selected_index}
    user_confidences = data.get('confidences', {})  # {'drill_id': 1..5}
    cards = get_personalized_daily_drills(request.user, count=3)

    results = []
    correct_count = 0

    for card in cards:
        card_id = card['id']
        selected = user_answers.get(card_id)
        is_correct = (selected == card['correct'])
        if is_correct:
            correct_count += 1
            quality = int(user_confidences.get(card_id, 5))
        else:
            quality = int(user_confidences.get(card_id, 1))

        sm2_metrics = calculate_sm2(
            repetitions=1 if is_correct else 0,
            easiness_factor=2.5,
            interval_days=1,
            quality=quality
        )

        results.append({
            'id': card_id,
            'category': card['category'],
            'question': card['question'],
            'is_correct': is_correct,
            'user_selected': selected,
            'correct_index': card['correct'],
            'correct_text': card['options'][card['correct']],
            'explanation': card['explanation'],
            'key_takeaway': card['key_takeaway'],
            'sm2': sm2_metrics,
        })

    # Award XP once per day for micro drill with streak multiplier
    today_str = timezone.now().strftime('%Y-%m-%d')
    done_cache_key = f"user_drill_completed_{request.user.id}_{today_str}"
    already_done = cache.get(done_cache_key)

    xp_awarded = 0
    streak_bonus = False
    if not already_done:
        base_xp = 15 if correct_count >= 2 else 5
        gamification = getattr(request.user, 'gamification', None)
        if gamification and gamification.current_streak >= 3:
            xp_awarded = int(round(base_xp * 1.33))  # 15 * 1.33 = 20 XP
            streak_bonus = True
        else:
            xp_awarded = base_xp

        award_user_xp(request.user, xp_awarded, "Daily Knowledge Micro-Drill (SM-2)")
        cache.set(done_cache_key, True, timeout=86400)

    return JsonResponse({
        'success': True,
        'correct_count': correct_count,
        'total_cards': len(cards),
        'score_percentage': int(round((correct_count / len(cards)) * 100)),
        'xp_awarded': xp_awarded,
        'streak_bonus': streak_bonus,
        'already_done_today': bool(already_done),
        'results': results,
    })


