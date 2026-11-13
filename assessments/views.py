import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.db.models import Max, Count, Q
from .models import (
    SkillAssessment, AssessmentQuestion, AssessmentAttempt, AssessmentResponse,
    CodingChallenge, CodingTestCase, ChallengeSubmission
)
from courses.models import Course
from gamification.services import award_user_xp, award_badge_if_eligible

@login_required
def assessments_list_view(request):
    assessments = SkillAssessment.objects.filter(is_active=True).prefetch_related('questions')

    category_filter = request.GET.get('category', 'all')
    if category_filter and category_filter != 'all':
        assessments = assessments.filter(category=category_filter)

    difficulty_filter = request.GET.get('difficulty', 'all')
    if difficulty_filter and difficulty_filter != 'all':
        assessments = assessments.filter(difficulty=difficulty_filter)

    # Get user's best scores
    user_attempts = AssessmentAttempt.objects.filter(user=request.user)
    best_scores = {}
    for att in user_attempts:
        if att.assessment_id not in best_scores or att.percentage > best_scores[att.assessment_id]:
            best_scores[att.assessment_id] = att.percentage

    assessments_data = []
    for ass in assessments:
        assessments_data.append({
            'assessment': ass,
            'question_count': ass.questions.count(),
            'best_score': best_scores.get(ass.id, None),
        })

    return render(request, 'assessments/list.html', {
        'assessments_data': assessments_data,
        'category_choices': SkillAssessment.CATEGORY_CHOICES,
        'selected_category': category_filter,
        'selected_difficulty': difficulty_filter,
    })


@login_required
def take_assessment_view(request, assessment_id):
    assessment = get_object_or_404(SkillAssessment, id=assessment_id, is_active=True)
    questions = assessment.questions.all().order_by('id')

    if not questions.exists():
        messages.warning(request, "This assessment is currently being updated with new questions.")
        return redirect('assessments:list')

    return render(request, 'assessments/take.html', {
        'assessment': assessment,
        'questions': questions,
    })


@login_required
def submit_assessment_view(request, assessment_id):
    if request.method != 'POST':
        return redirect('assessments:take', assessment_id=assessment_id)

    assessment = get_object_or_404(SkillAssessment, id=assessment_id, is_active=True)
    questions = assessment.questions.all()
    total_questions = questions.count()

    if total_questions == 0:
        return redirect('assessments:list')

    score = 0
    topic_stats = {}  # topic -> {'total': int, 'correct': int}
    responses_to_create = []

    for q in questions:
        field_name = f"question_{q.id}"
        selected = request.POST.get(field_name, '').upper().strip()
        is_correct = (selected == q.correct_answer)

        if is_correct:
            score += 1

        topic = q.topic_tag or "Core Fundamentals"
        if topic not in topic_stats:
            topic_stats[topic] = {'total': 0, 'correct': 0}
        topic_stats[topic]['total'] += 1
        if is_correct:
            topic_stats[topic]['correct'] += 1

        responses_to_create.append({
            'question': q,
            'selected_answer': selected,
            'is_correct': is_correct
        })

    percentage = int(round((score / total_questions) * 100))

    # Evaluate Strengths and Weaknesses
    strengths = []
    weaknesses = []
    for topic, stat in topic_stats.items():
        ratio = stat['correct'] / stat['total']
        if ratio >= 0.75:
            strengths.append(f"{topic} ({stat['correct']}/{stat['total']})")
        else:
            weaknesses.append(f"{topic} ({stat['correct']}/{stat['total']})")

    # Generate Personalized Feedback
    if percentage >= 80:
        ai_feedback = (
            f"Outstanding performance on {assessment.title}! You demonstrated strong conceptual understanding "
            "and technical precision across the majority of topics. Continue to challenge yourself with advanced implementations."
        )
    elif percentage >= 50:
        ai_feedback = (
            f"Solid foundational effort on {assessment.title}. You have a good grasp of the basic concepts, but review the "
            "missed topics below to strengthen edge-case handling and in-depth architecture."
        )
    else:
        ai_feedback = (
            f"You completed {assessment.title}. Several core topics need revision before moving to complex projects. "
            "Take advantage of the recommended SkillSphere courses below to master the fundamentals."
        )

    # Create Attempt Record
    attempt = AssessmentAttempt.objects.create(
        user=request.user,
        assessment=assessment,
        score=score,
        total_questions=total_questions,
        percentage=percentage,
        ai_feedback=ai_feedback,
        strengths=", ".join(strengths) if strengths else "Consistent initial effort",
        weaknesses=", ".join(weaknesses) if weaknesses else "None identified",
    )

    # Telemetry: Assessment attempted
    from analytics.services import track_event
    track_event(
        user=request.user,
        event_type='assessment_attempted',
        metadata={
            'assessment_id': assessment.id,
            'assessment_title': assessment.title,
            'category': assessment.category,
            'score': score,
            'percentage': percentage,
        }
    )

    # Save individual responses
    for r in responses_to_create:
        AssessmentResponse.objects.create(
            attempt=attempt,
            question=r['question'],
            selected_answer=r['selected_answer'],
            is_correct=r['is_correct']
        )

    # Award XP & Badge
    xp_amount = 50 if percentage >= 70 else 25
    award_user_xp(request.user, xp_amount, f"Completed assessment: {assessment.title} ({percentage}%)")
    award_badge_if_eligible(request.user, 'first-assessment-complete')

    return redirect('assessments:result', attempt_id=attempt.id)


@login_required
def assessment_result_view(request, attempt_id):
    attempt = get_object_or_404(AssessmentAttempt, id=attempt_id, user=request.user)
    responses = attempt.responses.select_related('question').all()

    # Smart Course Recommendations based on category
    cat_keyword = attempt.assessment.category.lower()
    recommended_courses = Course.objects.filter(is_published=True).filter(
        title__icontains=attempt.assessment.title.split()[0]
    )[:3]
    if not recommended_courses.exists():
        recommended_courses = Course.objects.filter(is_published=True)[:3]

    return render(request, 'assessments/result.html', {
        'attempt': attempt,
        'responses': responses,
        'recommended_courses': recommended_courses,
    })


# ==========================================
# LEETCODE-GRADE CODING CHALLENGES & JUDGE
# ==========================================

@login_required
def challenges_list_view(request):
    challenges = CodingChallenge.objects.filter(is_active=True).prefetch_related('test_cases', 'submissions')

    category_filter = request.GET.get('category', 'all')
    difficulty_filter = request.GET.get('difficulty', 'all')
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '').strip()

    if category_filter and category_filter != 'all':
        challenges = challenges.filter(category=category_filter)

    if difficulty_filter and difficulty_filter != 'all':
        challenges = challenges.filter(difficulty=difficulty_filter)

    if search_query:
        challenges = challenges.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )

    # Submissions by user
    user_accepted = ChallengeSubmission.objects.filter(
        user=request.user, status='Accepted'
    ).values_list('challenge_id', flat=True).distinct()
    user_accepted_set = set(user_accepted)

    if status_filter == 'solved':
        challenges = challenges.filter(id__in=user_accepted_set)
    elif status_filter == 'unsolved':
        challenges = challenges.exclude(id__in=user_accepted_set)

    all_active = CodingChallenge.objects.filter(is_active=True)
    total_challenges = all_active.count()
    solved_count = len(user_accepted_set)
    easy_total = all_active.filter(difficulty='Easy').count()
    medium_total = all_active.filter(difficulty='Medium').count()
    hard_total = all_active.filter(difficulty='Hard').count()

    solved_easy = all_active.filter(id__in=user_accepted_set, difficulty='Easy').count()
    solved_medium = all_active.filter(id__in=user_accepted_set, difficulty='Medium').count()
    solved_hard = all_active.filter(id__in=user_accepted_set, difficulty='Hard').count()

    challenges_data = []
    for c in challenges:
        challenges_data.append({
            'challenge': c,
            'is_solved': c.id in user_accepted_set,
            'acceptance_rate': c.acceptance_rate,
            'test_cases_count': c.test_cases.count(),
        })

    return render(request, 'assessments/challenges_list.html', {
        'challenges_data': challenges_data,
        'selected_category': category_filter,
        'selected_difficulty': difficulty_filter,
        'selected_status': status_filter,
        'search_query': search_query,
        'category_choices': CodingChallenge.CATEGORY_CHOICES,
        'difficulty_choices': CodingChallenge.DIFFICULTY_CHOICES,
        'stats': {
            'total': total_challenges,
            'solved': solved_count,
            'easy_total': easy_total,
            'medium_total': medium_total,
            'hard_total': hard_total,
            'solved_easy': solved_easy,
            'solved_medium': solved_medium,
            'solved_hard': solved_hard,
            'completion_pct': round((solved_count / max(1, total_challenges)) * 100, 1) if total_challenges else 0,
        }
    })


@login_required
def challenge_detail_view(request, slug):
    challenge = get_object_or_404(CodingChallenge, slug=slug, is_active=True)
    visible_cases = challenge.test_cases.filter(is_hidden=False).order_by('order')
    hidden_count = challenge.test_cases.filter(is_hidden=True).count()
    user_submissions = ChallengeSubmission.objects.filter(
        user=request.user, challenge=challenge
    ).order_by('-created_at')[:10]
    
    is_solved = challenge.submissions.filter(user=request.user, status='Accepted').exists()
    latest_submission = user_submissions.first()

    visible_cases_json = []
    for tc in visible_cases:
        try:
            inp = json.loads(tc.input_data)
        except Exception:
            inp = tc.input_data
        try:
            out = json.loads(tc.expected_output)
        except Exception:
            out = tc.expected_output

        visible_cases_json.append({
            'id': tc.id,
            'order': tc.order,
            'input': inp,
            'output': out,
            'explanation': tc.explanation,
        })

    return render(request, 'assessments/challenge_detail.html', {
        'challenge': challenge,
        'visible_cases': visible_cases,
        'visible_cases_json': json.dumps(visible_cases_json),
        'hidden_count': hidden_count,
        'total_cases_count': challenge.test_cases.count(),
        'user_submissions': user_submissions,
        'is_solved': is_solved,
        'latest_submission': latest_submission,
        'hints_list': challenge.get_hints_list(),
        'constraints_list': challenge.get_constraints_list(),
    })


@login_required
def challenge_test_cases_api(request, slug):
    challenge = get_object_or_404(CodingChallenge, slug=slug, is_active=True)
    mode = request.GET.get('mode', 'visible')
    
    if mode == 'all':
        cases = challenge.test_cases.all().order_by('order')
    else:
        cases = challenge.test_cases.filter(is_hidden=False).order_by('order')

    data = []
    for tc in cases:
        try:
            inp = json.loads(tc.input_data)
        except Exception:
            inp = tc.input_data
        try:
            out = json.loads(tc.expected_output)
        except Exception:
            out = tc.expected_output
            
        data.append({
            'id': tc.id,
            'order': tc.order,
            'input': inp,
            'expected_output': out,
            'is_hidden': tc.is_hidden,
            'explanation': tc.explanation,
        })

    return JsonResponse({'status': 'success', 'test_cases': data})


@login_required
@require_POST
def submit_challenge_solution(request, slug):
    challenge = get_object_or_404(CodingChallenge, slug=slug, is_active=True)
    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON body'}, status=400)

    language = body.get('language', 'python')
    code = body.get('code', '')
    status = body.get('status', 'Accepted')
    runtime_ms = int(body.get('runtime_ms', 25))
    memory_kb = int(body.get('memory_kb', 14200))
    passed_cases = int(body.get('passed_cases', 0))
    total_cases = int(body.get('total_cases', challenge.test_cases.count()))

    accepted_subs = ChallengeSubmission.objects.filter(challenge=challenge, status='Accepted')
    total_accepted = accepted_subs.count()
    if total_accepted > 0:
        slower_subs = accepted_subs.filter(runtime_ms__gte=runtime_ms).count()
        percentile_beats = round((slower_subs / total_accepted) * 100, 1)
        if percentile_beats < 5.0:
            percentile_beats = 5.0
        elif percentile_beats > 99.0:
            percentile_beats = 99.0
    else:
        percentile_beats = 92.5

    was_previously_solved = ChallengeSubmission.objects.filter(
        user=request.user, challenge=challenge, status='Accepted'
    ).exists()

    submission = ChallengeSubmission.objects.create(
        user=request.user,
        challenge=challenge,
        language=language,
        code=code,
        status=status,
        runtime_ms=runtime_ms,
        memory_kb=memory_kb,
        passed_cases=passed_cases,
        total_cases=total_cases,
        percentile_beats=percentile_beats,
    )

    xp_awarded = 0
    is_first_solve = False
    if status == 'Accepted' and not was_previously_solved:
        xp_awarded = challenge.xp_reward
        is_first_solve = True
        award_user_xp(
            request.user,
            xp_awarded,
            f"Solved coding challenge: {challenge.title} ({challenge.difficulty})"
        )
        award_badge_if_eligible(request.user, 'algorithm-champion')

    return JsonResponse({
        'status': 'success',
        'submission_id': submission.id,
        'submission_status': submission.status,
        'runtime_ms': submission.runtime_ms,
        'memory_kb': submission.memory_kb,
        'percentile_beats': submission.percentile_beats,
        'passed_cases': submission.passed_cases,
        'total_cases': submission.total_cases,
        'xp_awarded': xp_awarded,
        'is_first_solve': is_first_solve,
        'created_at': submission.created_at.strftime('%b %d, %Y %H:%M'),
    })

