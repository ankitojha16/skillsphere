from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import MockInterview, InterviewResponse
from services.ai_service import AIService
from gamification.services import award_user_xp, award_badge_if_eligible

INTERVIEW_QUESTION_BANKS = {
    'Python Developer': [
        "Explain how memory management and garbage collection work in Python.",
        "What are Python generators and decorators, and in what practical scenarios would you use them?",
        "How do *args and **kwargs function, and how does Python resolve method resolution order (MRO)?",
        "Describe the difference between deep copy and shallow copy in Python with mutable structures.",
        "How would you optimize a Python script processing a 10GB CSV file without running out of RAM?"
    ],
    'Django Developer': [
        "Explain Django's MVT request-response lifecycle from browser request to template rendering.",
        "How does the Django ORM handle N+1 query problems, and how do select_related and prefetch_related solve them?",
        "What is CSRF protection in Django, and how does the framework validate incoming POST requests?",
        "How do Django database migrations operate under the hood, and what precautions do you take with zero-downtime deployments?",
        "How do Django signals work, and what are their benefits versus potential architectural drawbacks?"
    ],
    'Frontend Developer': [
        "Explain the browser event loop, microtasks, and macrotasks in modern JavaScript.",
        "What is the difference between CSS Flexbox and CSS Grid, and when would you use each?",
        "How do closures work in JavaScript, and what is a practical real-world use case?",
        "What strategies do you use to optimize web performance and reduce Cumulative Layout Shift (CLS)?",
        "Explain how modern fetch requests handle CORS preflight checks."
    ],
    'Backend Developer': [
        "What is the difference between synchronous and asynchronous architectures in backend systems?",
        "Explain RESTful principles, idempotency in HTTP methods, and status code best practices.",
        "How do database indexes (e.g. B-Trees) speed up read operations and what are their write trade-offs?",
        "How would you design a rate limiter to protect backend APIs from abusive traffic?",
        "What are ACID transactions, and how does database isolation prevent dirty reads?"
    ],
    'SQL Developer': [
        "Explain the differences between INNER JOIN, LEFT OUTER JOIN, and FULL OUTER JOIN.",
        "What are Common Table Expressions (CTEs) and Window Functions like ROW_NUMBER() and RANK()?",
        "How would you diagnose and optimize a slow SQL query using EXPLAIN ANALYZE?",
        "What are database foreign key ON DELETE CASCADE constraints and their architectural risks?",
        "Explain database normalization from 1NF to 3NF."
    ],
    'General Programming': [
        "What is the difference between an Array and a Linked List in memory?",
        "Explain recursion, its base case, and how the call stack functions during execution.",
        "How does hashing work in Hash Maps, and how are hash collisions resolved?",
        "What is the difference between monolithic architecture and microservices?",
        "What are the SOLID design principles, and why are they valuable in team codebases?"
    ],
    'HR Interview': [
        "Tell me about a challenging technical bug or conflict you encountered in a team project and how you resolved it.",
        "How do you prioritize deadlines when juggling multiple complex coursework or development tasks?",
        "Where do you see your technical trajectory progressing over the next 2 to 3 years?",
        "Describe a time you received critical constructive feedback on your code and how you incorporated it.",
        "Why are you passionate about software engineering and continuous technical learning?"
    ]
}

@login_required
def interview_setup_view(request):
    if request.method == 'POST':
        category = request.POST.get('category', 'Python Developer')
        difficulty = request.POST.get('difficulty', 'Junior')
        total_questions = int(request.POST.get('total_questions', 3))

        interview = MockInterview.objects.create(
            user=request.user,
            category=category,
            difficulty=difficulty,
            total_questions=min(5, max(2, total_questions))
        )

        # Pre-populate question bank
        bank = INTERVIEW_QUESTION_BANKS.get(category, INTERVIEW_QUESTION_BANKS['General Programming'])
        for idx in range(interview.total_questions):
            q_text = bank[idx % len(bank)]
            InterviewResponse.objects.create(
                interview=interview,
                question_order=idx + 1,
                question_text=q_text
            )

        return redirect('interviews:session', interview_id=interview.id)

    past_interviews = MockInterview.objects.filter(user=request.user)

    return render(request, 'interviews/setup.html', {
        'past_interviews': past_interviews,
        'categories': MockInterview.CATEGORY_CHOICES,
        'difficulties': MockInterview.DIFFICULTY_CHOICES,
    })


@login_required
def interview_session_view(request, interview_id):
    interview = get_object_or_404(MockInterview, id=interview_id, user=request.user)
    if interview.is_completed:
        return redirect('interviews:report', interview_id=interview.id)

    # Find the current unanswered question
    current_q = interview.responses.filter(user_answer="").order_by('question_order').first()
    if not current_q:
        # All answered - finalize interview
        return finalize_interview(interview, request)

    answered_responses = interview.responses.exclude(user_answer="").order_by('question_order')

    return render(request, 'interviews/session.html', {
        'interview': interview,
        'current_q': current_q,
        'answered_responses': answered_responses,
        'progress_pct': int(((current_q.question_order - 1) / interview.total_questions) * 100),
    })


@login_required
def interview_submit_answer(request, interview_id):
    if request.method != 'POST':
        return redirect('interviews:session', interview_id=interview_id)

    interview = get_object_or_404(MockInterview, id=interview_id, user=request.user)
    current_q = interview.responses.filter(user_answer="").order_by('question_order').first()
    if not current_q:
        return redirect('interviews:report', interview_id=interview.id)

    user_answer = request.POST.get('user_answer', '').strip()[:3000]
    if not user_answer:
        messages.error(request, "Please enter your technical explanation before continuing.")
        return redirect('interviews:session', interview_id=interview.id)

    # Rate limiting
    allowed, retry_after = AIService.check_rate_limit(request.user.id)
    if not allowed:
        messages.error(request, f"Rate limit reached. Please wait {retry_after} seconds before submitting your response.")
        return redirect('interviews:session', interview_id=interview.id)

    # Evaluate answer using AI Service with user-scoped context
    eval_result = AIService.evaluate_interview_response(
        category=interview.category,
        question=current_q.question_text,
        user_answer=user_answer,
        user_id=request.user.id
    )

    current_q.user_answer = user_answer
    current_q.ai_feedback = eval_result.get('constructive_feedback', 'Good technical explanation.')
    current_q.technical_rating = eval_result.get('rating', 7)
    current_q.save()

    # Check if all questions are now answered
    has_unanswered = interview.responses.filter(user_answer="").exists()
    if not has_unanswered:
        return finalize_interview(interview, request)

    messages.success(request, f"Question {current_q.question_order} answered! Feedback recorded.")
    return redirect('interviews:session', interview_id=interview.id)


def finalize_interview(interview: MockInterview, request):
    responses = interview.responses.all()
    ratings = [r.technical_rating for r in responses if r.technical_rating > 0]
    avg_score = int(round(sum(ratings) / len(ratings))) * 10 if ratings else 70

    interview.overall_score = min(100, avg_score)
    interview.is_completed = True
    interview.strong_areas = f"Solid foundational grasp of {interview.category} concepts and problem explanation."
    interview.improvement_areas = "Enhance discussion of production trade-offs, edge cases, and performance complexity."
    interview.overall_feedback = (
        f"You completed the {interview.category} mock interview with a rating of {interview.overall_score}/100. "
        "Keep practicing structured communication: define the concept, give a concrete example, and state the trade-offs."
    )
    interview.save()

    award_user_xp(request.user, 75, f"Completed {interview.category} mock interview")
    award_badge_if_eligible(request.user, 'interview-ready')

    return redirect('interviews:report', interview_id=interview.id)


@login_required
def interview_report_view(request, interview_id):
    interview = get_object_or_404(MockInterview, id=interview_id, user=request.user)
    responses = interview.responses.all().order_by('question_order')

    return render(request, 'interviews/report.html', {
        'interview': interview,
        'responses': responses,
    })
