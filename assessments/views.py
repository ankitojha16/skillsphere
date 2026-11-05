from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Max
from .models import SkillAssessment, AssessmentQuestion, AssessmentAttempt, AssessmentResponse
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
