import json
import random
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.models import User

from .models import Badge, UserBadge, UserGamification, XPTransaction, League, LeagueMembership, SkillDuel
from .services import get_or_create_gamification, award_user_xp

DUEL_QUESTIONS = {
    'python': [
        {
            'id': 1,
            'question': "What is the average time complexity of looking up a key in a standard Python dictionary (hashmap)?",
            'options': ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            'correct': 0,
            'explanation': "Python dict lookups use hash tables and achieve O(1) average time complexity."
        },
        {
            'id': 2,
            'question': "Which keyword turns a Python function into a generator yielding values lazily?",
            'options': ["produce", "yield", "return", "await"],
            'correct': 1,
            'explanation': "'yield' suspends execution and returns an iterator object."
        },
        {
            'id': 3,
            'question': "What is the primary purpose of Python's Global Interpreter Lock (GIL)?",
            'options': [
                "To optimize GPU tensor operations",
                "To prevent race conditions during CPython memory management",
                "To enforce strict type annotations at runtime",
                "To compile Python bytecode to machine code"
            ],
            'correct': 1,
            'explanation': "The GIL ensures thread-safe reference counting in CPython."
        },
        {
            'id': 4,
            'question': "What does the @classmethod decorator pass as its implicit first argument?",
            'options': ["self (the instance)", "cls (the class object)", "None", "args (tuple)"],
            'correct': 1,
            'explanation': "@classmethod receives 'cls' pointing to the class itself rather than an instance."
        },
        {
            'id': 5,
            'question': "In Python, which list method appends all elements from an iterable to the end of a list?",
            'options': ["append()", "extend()", "push()", "insert()"],
            'correct': 1,
            'explanation': "extend() iterates over its argument and adds each element to the list."
        }
    ],
    'sql': [
        {
            'id': 6,
            'question': "Which SQL clause filters groups produced by a GROUP BY aggregation?",
            'options': ["WHERE", "HAVING", "LIMIT", "FILTER"],
            'correct': 1,
            'explanation': "HAVING filters aggregated grouped records, whereas WHERE filters individual rows prior to grouping."
        },
        {
            'id': 7,
            'question': "What type of index is most commonly used by default in relational databases like PostgreSQL?",
            'options': ["B-Tree Index", "Hash Index", "GIN Index", "BRIN Index"],
            'correct': 0,
            'explanation': "B-Tree indexes are the default and excel at equality and range queries."
        },
        {
            'id': 8,
            'question': "Which ACID property guarantees that completed database transactions survive system crashes?",
            'options': ["Atomicity", "Consistency", "Isolation", "Durability"],
            'correct': 3,
            'explanation': "Durability ensures committed transactions are persisted to non-volatile storage via WAL."
        },
        {
            'id': 9,
            'question': "What SQL statement removes all rows from a table quickly without logging individual row deletions?",
            'options': ["DROP TABLE", "DELETE FROM", "TRUNCATE TABLE", "PURGE TABLE"],
            'correct': 2,
            'explanation': "TRUNCATE deallocates data pages directly and is much faster than DELETE."
        },
        {
            'id': 10,
            'question': "What does the SQL COALESCE(val1, val2) function return?",
            'options': [
                "The concatenation of both values",
                "The first non-null expression in the list",
                "The larger of the two values",
                "A boolean indicating if both values are null"
            ],
            'correct': 1,
            'explanation': "COALESCE returns the first non-null argument."
        }
    ],
    'web': [
        {
            'id': 11,
            'question': "What security header prevents Clickjacking by restricting whether a site can be framed in an <iframe>?",
            'options': ["Content-Security-Policy: frame-ancestors", "Access-Control-Allow-Origin", "Strict-Transport-Security", "X-XSS-Protection"],
            'correct': 0,
            'explanation': "CSP frame-ancestors (and the legacy X-Frame-Options) dictates which origins may embed the resource in an iframe."
        },
        {
            'id': 12,
            'question': "In JWT (JSON Web Tokens), which component contains user claims and expiration timestamp?",
            'options': ["Header", "Payload", "Signature", "Digest"],
            'correct': 1,
            'explanation': "The second base64url-encoded segment is the Payload containing claims and timestamps."
        },
        {
            'id': 13,
            'question': "What HTTP status code is most appropriate when a client request violates rate limiting policies?",
            'options': ["400 Bad Request", "403 Forbidden", "429 Too Many Requests", "503 Service Unavailable"],
            'correct': 2,
            'explanation': "HTTP 429 Too Many Requests indicates the user has sent too many requests in a given amount of time."
        },
        {
            'id': 14,
            'question': "Why is SameSite=Strict recommended on session authentication cookies?",
            'options': [
                "It encrypts cookie data with AES-256",
                "It prevents the cookie from being sent on cross-site requests, mitigating CSRF",
                "It allows cookies to be read via JavaScript fetch",
                "It speeds up DNS lookup resolution"
            ],
            'correct': 1,
            'explanation': "SameSite=Strict prevents browsers from sending cookies on cross-site navigation, effectively neutralizing CSRF."
        },
        {
            'id': 15,
            'question': "What is the primary benefit of HTTP/2 multiplexing over HTTP/1.1?",
            'options': [
                "Mandatory symmetric encryption",
                "Concurrent bidirectional streaming over a single TCP connection without head-of-line blocking",
                "Automatic database query caching",
                "Elimination of TLS handshakes"
            ],
            'correct': 1,
            'explanation': "Multiplexing interleaves multiple request/response frames concurrently over one TCP socket."
        }
    ],
    'system': [
        {
            'id': 16,
            'question': "According to the CAP theorem, in the event of a network partition (P), what trade-off must a distributed system make?",
            'options': [
                "Between Latency and Cost",
                "Between Consistency (C) and Availability (A)",
                "Between Scalability and Durability",
                "Between Throughput and Concurrency"
            ],
            'correct': 1,
            'explanation': "When a partition occurs, a distributed system must choose between returning consistent data or remaining available."
        },
        {
            'id': 17,
            'question': "What cache eviction strategy discards items that have not been accessed for the longest period of time?",
            'options': ["FIFO (First In First Out)", "LRU (Least Recently Used)", "LFU (Least Frequently Used)", "TTL (Time To Live)"],
            'correct': 1,
            'explanation': "LRU tracks access order and evicts items with the oldest last-accessed timestamp."
        },
        {
            'id': 18,
            'question': "What is the primary function of a consistent hashing ring in distributed caches like Redis or Cassandra?",
            'options': [
                "To encrypt all payload data in transit",
                "To minimize key remapping when nodes are added or removed from the cluster",
                "To perform ACID transactions across all nodes simultaneously",
                "To compress JSON keys using gzip"
            ],
            'correct': 1,
            'explanation': "Consistent hashing ensures only K/N keys need relocation on average when cluster topology changes."
        },
        {
            'id': 19,
            'question': "Which database partitioning technique splits large tables horizontally across multiple database servers based on a shard key?",
            'options': ["Replication", "Database Sharding", "Denormalization", "Indexing"],
            'correct': 1,
            'explanation': "Horizontal sharding partitions rows across multiple distinct database nodes based on shard key hash."
        },
        {
            'id': 20,
            'question': "What pattern prevents cascading failure when a downstream microservice is unresponsive?",
            'options': ["Circuit Breaker Pattern", "Singleton Pattern", "Factory Method Pattern", "Observer Pattern"],
            'correct': 0,
            'explanation': "Circuit Breaker trips after repeated downstream timeouts, fast-failing and protecting caller threads."
        }
    ]
}


COHORT_BOT_PEERS = [
    {"name": "Sophia Zhang", "handle": "sophia_z", "xp": 480, "avatar": "👩‍💻", "badge": "Gold Prospect"},
    {"name": "Marcus Vance", "handle": "marcus_v", "xp": 435, "avatar": "🚀", "badge": "Speed Demon"},
    {"name": "Elena Rostova", "handle": "elena_code", "xp": 395, "avatar": "⚡", "badge": "Algorithm Ace"},
    {"name": "Liam Patel", "handle": "liam_p", "xp": 350, "avatar": "🧠", "badge": "Full Stack Pro"},
    {"name": "Amina Touré", "handle": "amina_t", "xp": 310, "avatar": "✨", "badge": "Debugger"},
    {"name": "Kai Takahashi", "handle": "kai_t", "xp": 285, "avatar": "🎯", "badge": "Test Driven"},
    {"name": "Chloe Bennett", "handle": "chloe_b", "xp": 260, "avatar": "💎", "badge": "Frontend Wizard"},
    {"name": "DevSprint Bot", "handle": "dev_sprint", "xp": 240, "avatar": "🤖", "badge": "Pacer"},
    {"name": "Mateo Silva", "handle": "mateo_s", "xp": 210, "avatar": "🔥", "badge": "Streaker"},
    {"name": "Jordan Lee", "handle": "jordan_l", "xp": 175, "avatar": "💻", "badge": "API Architect"},
    {"name": "Nadia Al-Mansoor", "handle": "nadia_m", "xp": 140, "avatar": "🌟", "badge": "Learner"},
    {"name": "Lucas Meyer", "handle": "lucas_m", "xp": 95, "avatar": "📚", "badge": "Rising Star"},
    {"name": "Zoe Kravitz", "handle": "zoe_k", "xp": 70, "avatar": "🛡️", "badge": "Safety Zone"},
    {"name": "Vikram Seth", "handle": "vikram_s", "xp": 40, "avatar": "⚠️", "badge": "At Risk"},
    {"name": "Emma Watson", "handle": "emma_w", "xp": 20, "avatar": "📉", "badge": "Demotion Zone"},
]


@login_required
def achievements_view(request):
    gamification = get_or_create_gamification(request.user)
    all_badges = Badge.objects.all()
    unlocked_badge_ids = set(
        UserBadge.objects.filter(user=request.user).values_list('badge_id', flat=True)
    )

    # Compute user metrics for badge progress tracking
    completed_courses = 0
    try:
        from courses.models import CourseCompletion
        completed_courses = CourseCompletion.objects.filter(user=request.user, is_completed=True).count()
    except Exception:
        pass

    passed_assessments = 0
    try:
        from assessments.models import AssessmentAttempt
        passed_assessments = AssessmentAttempt.objects.filter(user=request.user, is_passed=True).count()
    except Exception:
        pass

    completed_interviews = 0
    try:
        from interviews.models import MockInterview
        completed_interviews = MockInterview.objects.filter(user=request.user, is_completed=True).count()
    except Exception:
        pass

    completed_milestones = 0
    try:
        from roadmaps.models import RoadmapMilestone
        completed_milestones = RoadmapMilestone.objects.filter(roadmap__user=request.user, is_completed=True).count()
    except Exception:
        pass

    badges_data = []
    for badge in all_badges:
        is_unlocked = badge.id in unlocked_badge_ids
        slug = badge.slug

        if slug == 'first-course-complete':
            current_val = 1 if is_unlocked or completed_courses > 0 else 0
            target_val = 1
            progress_label = f"{current_val} / 1 Course"
            progress_pct = 100 if (is_unlocked or completed_courses > 0) else 0
        elif slug == 'explorer-badge':
            target_val = max(1, badge.xp_requirement or 100)
            current_val = min(target_val, gamification.total_xp) if not is_unlocked else target_val
            progress_label = f"{current_val} / {target_val} XP"
            progress_pct = 100 if is_unlocked else min(100, int((current_val / target_val) * 100))
        elif slug == '7-day-streak':
            target_val = 7
            best_streak = max(gamification.current_streak, gamification.longest_streak)
            current_val = 7 if is_unlocked else min(7, best_streak)
            progress_label = f"{current_val} / 7 Days"
            progress_pct = 100 if is_unlocked else min(100, int((current_val / 7) * 100))
        elif slug == 'dsa-explorer':
            current_val = 1 if is_unlocked or completed_milestones > 0 else 0
            target_val = 1
            progress_label = f"{current_val} / 1 Milestone"
            progress_pct = 100 if (is_unlocked or completed_milestones > 0) else 0
        elif slug == 'first-assessment-complete':
            current_val = 1 if is_unlocked or passed_assessments > 0 else 0
            target_val = 1
            progress_label = f"{current_val} / 1 Assessment"
            progress_pct = 100 if (is_unlocked or passed_assessments > 0) else 0
        elif slug == 'first-roadmap-complete':
            current_val = 1 if is_unlocked or completed_milestones >= 3 else 0
            target_val = 1
            progress_label = f"{current_val} / 1 Roadmap"
            progress_pct = 100 if (is_unlocked or completed_milestones >= 3) else 0
        elif slug == 'interview-ready':
            current_val = 1 if is_unlocked or completed_interviews > 0 else 0
            target_val = 1
            progress_label = f"{current_val} / 1 Session"
            progress_pct = 100 if (is_unlocked or completed_interviews > 0) else 0
        else:
            current_val = 1 if is_unlocked else 0
            target_val = 1
            progress_label = "Completed" if is_unlocked else "In Progress"
            progress_pct = 100 if is_unlocked else 0

        badges_data.append({
            'badge': badge,
            'is_unlocked': is_unlocked,
            'current_value': current_val,
            'target_value': target_val,
            'progress_label': progress_label,
            'progress_pct': progress_pct,
        })

    # Next level progress
    level_order = [
        ('Beginner', 0, 100),
        ('Explorer', 100, 300),
        ('Learner', 300, 600),
        ('Developer', 600, 1000),
        ('Advanced Learner', 1000, 1500),
        ('Skill Master', 1500, 2500)
    ]
    next_level = 'Skill Master'
    xp_to_next = 0
    level_progress_pct = 100
    for idx, (lvl_name, low, high) in enumerate(level_order):
        if gamification.current_level == lvl_name:
            if idx < len(level_order) - 1:
                next_level = level_order[idx + 1][0]
                target_xp = high
                xp_in_level = gamification.total_xp - low
                span = high - low
                level_progress_pct = min(100, max(0, int((xp_in_level / span) * 100)))
                xp_to_next = max(0, target_xp - gamification.total_xp)
            else:
                level_progress_pct = 100
                xp_to_next = 0
            break

    # Top Platform Engineers Leaderboard
    from .models import UserGamification
    leaderboard = list(UserGamification.objects.select_related('user').order_by('-total_xp', '-current_streak')[:5])
    user_rank = UserGamification.objects.filter(total_xp__gt=gamification.total_xp).count() + 1

    return render(request, 'gamification/achievements.html', {
        'gamification': gamification,
        'badges_data': badges_data,
        'unlocked_count': len(unlocked_badge_ids),
        'total_badges': len(all_badges),
        'next_level': next_level,
        'xp_to_next': xp_to_next,
        'level_progress_pct': level_progress_pct,
        'leaderboard': leaderboard,
        'user_rank': user_rank,
    })


@login_required
def leagues_view(request):
    """
    Duolingo-style weekly competitive leagues (Bronze -> Silver -> Gold -> Diamond)
    with 30-member cohorts, promotion/relegation zones, and countdown timer.
    """
    gamification = get_or_create_gamification(request.user)
    today = timezone.now().date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    # Determine user's tier by their overall experience
    if gamification.total_xp >= 3000:
        tier, tier_level, tier_color, tier_badge = 'DIAMOND', 4, 'info', '💎 Diamond League'
    elif gamification.total_xp >= 1500:
        tier, tier_level, tier_color, tier_badge = 'GOLD', 3, 'warning', '🥇 Gold League'
    elif gamification.total_xp >= 500:
        tier, tier_level, tier_color, tier_badge = 'SILVER', 2, 'secondary', '🥈 Silver League'
    else:
        tier, tier_level, tier_color, tier_badge = 'BRONZE', 1, 'warning', '🥉 Bronze League'

    cohort_id = f"{monday.strftime('%Y-W%W')}-{tier[:3]}-1"
    league, _ = League.objects.get_or_create(
        cohort_id=cohort_id,
        week_start=monday,
        defaults={
            'tier': tier,
            'tier_level': tier_level,
            'week_end': sunday,
            'is_active': True
        }
    )

    # Compute or seed weekly XP for user
    weekly_xp_calc = XPTransaction.objects.filter(
        user=request.user,
        created_at__date__gte=monday
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    if weekly_xp_calc == 0:
        weekly_xp_calc = max(45, (gamification.total_xp % 180) + 50)

    membership, _ = LeagueMembership.objects.get_or_create(
        league=league,
        user=request.user,
        defaults={'weekly_xp': weekly_xp_calc}
    )
    if membership.weekly_xp < weekly_xp_calc:
        membership.weekly_xp = weekly_xp_calc
        membership.save()

    # Build cohort ranking list combining active user and realistic cohort peers
    cohort_list = []
    cohort_list.append({
        'is_current_user': True,
        'user_id': request.user.id,
        'name': request.user.profile.full_name if hasattr(request.user, 'profile') and request.user.profile.full_name else request.user.username,
        'handle': request.user.username,
        'weekly_xp': membership.weekly_xp,
        'avatar': '👑',
        'badge': 'You',
        'streak': gamification.current_streak,
    })

    for bot in COHORT_BOT_PEERS:
        cohort_list.append({
            'is_current_user': False,
            'user_id': None,
            'name': bot['name'],
            'handle': bot['handle'],
            'weekly_xp': bot['xp'],
            'avatar': bot['avatar'],
            'badge': bot['badge'],
            'streak': random.randint(2, 14),
        })

    # Sort cohort by weekly XP descending
    cohort_list.sort(key=lambda x: x['weekly_xp'], reverse=True)

    # Assign ranks and zones
    user_rank = 1
    total_cohort = len(cohort_list)
    promotion_cutoff = 7
    demotion_cutoff = max(8, total_cohort - 4)

    for idx, competitor in enumerate(cohort_list, 1):
        competitor['rank'] = idx
        if idx <= promotion_cutoff:
            competitor['zone'] = 'promotion'
        elif idx >= demotion_cutoff and tier != 'BRONZE':
            competitor['zone'] = 'demotion'
        else:
            competitor['zone'] = 'safe'

        if competitor['is_current_user']:
            user_rank = idx
            membership.rank = idx
            membership.save()

    # Time remaining calculation
    now = timezone.now()
    reset_dt = timezone.datetime(sunday.year, sunday.month, sunday.day, 23, 59, 59, tzinfo=timezone.utc)
    seconds_left = max(0, int((reset_dt - now).total_seconds()))
    days_left = seconds_left // 86400
    hours_left = (seconds_left % 86400) // 3600
    mins_left = (seconds_left % 3600) // 60

    # User's recent duels
    recent_duels = SkillDuel.objects.filter(challenger=request.user).order_by('-created_at')[:5]

    context = {
        'gamification': gamification,
        'league': league,
        'tier': tier,
        'tier_badge': tier_badge,
        'tier_color': tier_color,
        'membership': membership,
        'cohort_list': cohort_list,
        'user_rank': user_rank,
        'total_cohort': total_cohort,
        'promotion_cutoff': promotion_cutoff,
        'demotion_cutoff': demotion_cutoff,
        'days_left': days_left,
        'hours_left': hours_left,
        'mins_left': mins_left,
        'recent_duels': recent_duels,
    }
    return render(request, 'gamification/leagues.html', context)


@login_required
def start_duel_api(request):
    """
    Returns 5 timed challenge questions for a 60-second 1v1 Skill Duel.
    """
    topic_key = request.GET.get('topic', 'python')
    if topic_key not in DUEL_QUESTIONS:
        topic_key = 'python'

    questions = DUEL_QUESTIONS[topic_key]
    client_questions = []
    for q in questions:
        client_questions.append({
            'id': q['id'],
            'question': q['question'],
            'options': q['options'],
        })

    topic_titles = {
        'python': 'Python & Algorithms',
        'sql': 'Relational Databases & SQL',
        'web': 'Web Architecture & Security',
        'system': 'System Design & Scalability'
    }

    return JsonResponse({
        'success': True,
        'topic': topic_titles.get(topic_key, 'Python & Algorithms'),
        'topic_key': topic_key,
        'opponent_name': random.choice(['DevBot 3000', 'CodeViper', 'ByteMaster', 'AlgoRival', 'CyberKnight']),
        'time_limit': 60,
        'questions': client_questions,
    })


@login_required
def submit_duel_api(request):
    """
    Validates answers for 1v1 Skill Duel, calculates winner, and awards XP with combo multipliers.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required.'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = {}

    topic_key = data.get('topic_key', 'python')
    if topic_key not in DUEL_QUESTIONS:
        topic_key = 'python'

    topic_titles = {
        'python': 'Python & Algorithms',
        'sql': 'Relational Databases & SQL',
        'web': 'Web Architecture & Security',
        'system': 'System Design & Scalability'
    }

    user_answers = data.get('answers', {})
    questions = DUEL_QUESTIONS[topic_key]

    correct_count = 0
    feedback = []
    for q in questions:
        qid_str = str(q['id'])
        user_pick = user_answers.get(qid_str)
        is_correct = (user_pick is not None and int(user_pick) == q['correct'])
        if is_correct:
            correct_count += 1
        feedback.append({
            'id': q['id'],
            'is_correct': is_correct,
            'correct_index': q['correct'],
            'explanation': q['explanation']
        })

    opponent_score = random.randint(2, 4)
    opponent_name = data.get('opponent_name', 'DevBot 3000')

    # Streak Combo Multiplier
    if correct_count == 5:
        combo_multiplier = 1.5
    elif correct_count == 4:
        combo_multiplier = 1.2
    else:
        combo_multiplier = 1.0

    if correct_count > opponent_score:
        outcome = 'VICTORY'
        base_xp = 30
        winner = request.user
    elif correct_count == opponent_score:
        outcome = 'DRAW'
        base_xp = 15
        winner = None
    else:
        outcome = 'DEFEAT'
        base_xp = 10
        winner = None

    xp_awarded = int(base_xp * combo_multiplier)
    award_user_xp(request.user, xp_awarded, f"Skill Duel ({outcome} {combo_multiplier}x): {correct_count} vs {opponent_score}")

    today = timezone.now().date()
    monday = today - timedelta(days=today.weekday())
    membership = LeagueMembership.objects.filter(
        user=request.user,
        league__week_start=monday
    ).first()
    if membership:
        membership.weekly_xp += xp_awarded
        membership.save()

    duel = SkillDuel.objects.create(
        challenger=request.user,
        opponent_name=opponent_name,
        topic=topic_titles.get(topic_key, 'Python & Algorithms'),
        challenger_score=correct_count,
        opponent_score=opponent_score,
        winner=winner,
        xp_wager=xp_awarded,
        status='COMPLETED'
    )

    return JsonResponse({
        'success': True,
        'duel_id': duel.id,
        'outcome': outcome,
        'challenger_score': correct_count,
        'opponent_score': opponent_score,
        'opponent_name': opponent_name,
        'base_xp': base_xp,
        'combo_multiplier': combo_multiplier,
        'xp_awarded': xp_awarded,
        'feedback': feedback,
    })


def public_user_badge_svg(request, username: str):
    """
    Public dynamic SVG badge generator for GitHub READMEs, personal portfolios, and blogs.
    Caches for 5 minutes with stale-while-revalidate for fast GitHub asset proxy loads.
    """
    from .badges import generate_github_badge_svg
    
    try:
        target_user = User.objects.get(username=username)
        gamification = get_or_create_gamification(target_user)
        
        # Calculate tier
        if gamification.total_xp >= 3000:
            tier = 'DIAMOND'
        elif gamification.total_xp >= 1500:
            tier = 'GOLD'
        elif gamification.total_xp >= 500:
            tier = 'SILVER'
        else:
            tier = 'BRONZE'
            
        duels_won = SkillDuel.objects.filter(winner=target_user).count()
        total_xp = gamification.total_xp
        streak = gamification.current_streak
    except User.DoesNotExist:
        tier = 'BRONZE'
        total_xp = 0
        streak = 1
        duels_won = 0

    svg_content = generate_github_badge_svg(
        username=username,
        tier=tier,
        total_xp=total_xp,
        streak=streak,
        duels_won=duels_won,
    )
    
    response = HttpResponse(svg_content, content_type='image/svg+xml')
    response['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=600'
    response['Access-Control-Allow-Origin'] = '*'
    return response



