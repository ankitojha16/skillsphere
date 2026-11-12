"""
SkillSphere Spaced Repetition Engine (SuperMemo SM-2 Algorithm).
Calculates optimal review intervals and delivers personalized daily micro-drills
to reinforce long-term memory and prevent the forgetting curve.
"""
import random
from typing import Dict, Any, List


def calculate_sm2(repetitions: int, easiness_factor: float, interval_days: int, quality: int) -> Dict[str, Any]:
    """
    Computes new SuperMemo SM-2 parameters based on recall quality (0-5 scale).
    - quality < 3: Incorrect recall, reset repetition count and interval.
    - quality >= 3: Correct recall, calculate next interval.
    """
    q = max(0, min(5, quality))
    ef = max(1.3, easiness_factor)

    if q < 3:
        new_repetitions = 0
        new_interval = 1
    else:
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = max(1, round(interval_days * ef))
        new_repetitions = repetitions + 1

    # Update easiness factor: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ef = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ef = round(max(1.3, min(3.0, new_ef)), 2)

    return {
        'repetitions': new_repetitions,
        'interval_days': new_interval,
        'easiness_factor': new_ef,
        'quality': q,
        'status': 'memorized' if q >= 4 else ('learning' if q >= 3 else 'relearning'),
    }


CURATED_DRILL_DECK = [
    {
        'id': 'drill_py_mutability',
        'category': 'Python Core & Memory',
        'question': 'Which of the following built-in Python types is immutable?',
        'options': ['list', 'tuple', 'set', 'dict'],
        'correct': 1,
        'explanation': 'Tuples cannot be modified after creation (immutable), while lists, sets, and dicts are mutable.',
        'key_takeaway': 'Immutability ensures hashability and thread safety for dictionary keys and set elements.'
    },
    {
        'id': 'drill_algo_binary_search',
        'category': 'Algorithms & Complexity',
        'question': 'What is the worst-case space complexity of iterative binary search on a sorted array?',
        'options': ['O(log n)', 'O(1)', 'O(n)', 'O(n log n)'],
        'correct': 1,
        'explanation': 'Iterative binary search uses only two pointer variables (left, right), requiring constant O(1) auxiliary space.',
        'key_takeaway': 'Prefer iterative over recursive binary search to avoid stack frame overhead.'
    },
    {
        'id': 'drill_sql_index',
        'category': 'Databases & SQL',
        'question': 'Which type of index is most effective for equality and range queries on B-Tree relational engines?',
        'options': ['Hash Index', 'B-Tree Index', 'Bitmap Index', 'Spatial Index'],
        'correct': 1,
        'explanation': 'B-Tree indices maintain sorted key orders, enabling efficient logarithmic searches for both =, <, >, and BETWEEN.',
        'key_takeaway': 'Hash indices only support exact equality (=) and fail on range scans.'
    },
    {
        'id': 'drill_web_jwt',
        'category': 'Web Architecture & Security',
        'question': 'Where should sensitive JWT access tokens be stored in modern web applications to mitigate XSS theft?',
        'options': ['localStorage', 'sessionStorage', 'HttpOnly, Secure SameSite Cookie', 'Window global object'],
        'correct': 2,
        'explanation': 'HttpOnly cookies cannot be read by JavaScript `document.cookie`, shielding tokens from malicious script injection.',
        'key_takeaway': 'Never store long-lived credentials in localStorage.'
    },
    {
        'id': 'drill_devops_docker',
        'category': 'DevOps & Containers',
        'question': 'Which Dockerfile instruction creates a new cached layer and executes commands during image build time?',
        'options': ['CMD', 'ENTRYPOINT', 'RUN', 'EXPOSE'],
        'correct': 2,
        'explanation': 'RUN executes commands and commits the result into the next container image layer during `docker build`.',
        'key_takeaway': 'Combine multi-step RUN commands (`apt-get update && apt-get install -y ...`) to minimize image layers.'
    },
    {
        'id': 'drill_py_gil',
        'category': 'Python Concurrency',
        'question': 'How does Python CPython GIL (Global Interpreter Lock) impact CPU-bound multi-threaded programs?',
        'options': [
            'It accelerates multi-threaded compute across all CPU cores',
            'It restricts bytecode execution to one native thread at a time',
            'It disables garbage collection',
            'It enforces asynchronous I/O loops'
        ],
        'correct': 1,
        'explanation': 'The GIL ensures memory safety in CPython by allowing only one thread to hold the Python interpreter at any given moment.',
        'key_takeaway': 'Use the `multiprocessing` module or native C extensions for CPU-intensive parallel computing in Python.'
    },
]


def get_personalized_daily_drills(user=None, count: int = 3) -> List[Dict[str, Any]]:
    """
    Returns 3 curated micro-drill cards for the day.
    Uses deterministic seeding by date and user ID to ensure consistent daily deck per user.
    """
    from django.utils import timezone
    today_str = timezone.now().strftime('%Y%m%d')
    seed = int(today_str) + (user.id if user and user.is_authenticated else 42)
    rng = random.Random(seed)
    
    deck = list(CURATED_DRILL_DECK)
    rng.shuffle(deck)
    return deck[:count]
