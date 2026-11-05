import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from accounts.models import StudentProfile
from courses.models import Category, Course, Enrollment
from learning.models import Lesson, LessonProgress
from goals.models import LearningGoal, LearningActivity

from opportunities.models import Opportunity, SavedOpportunity
from events.models import Event, SavedEvent
from community.models import CommunityPost, CommunityComment
from collaboration.models import CollaborationProject, CollaborationMembership
from certificates.models import Certificate
from careers.models import CareerProfile
from portfolios.models import Portfolio, PortfolioProject
from resumes.models import Resume
from notifications.models import Notification

class Command(BaseCommand):
    help = 'Seeds initial sample categories, courses, lessons, and demo student for SkillSphere'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting SkillSphere sample data seeding...'))

        # 1. Categories
        categories_data = [
            {
                'name': 'Programming',
                'slug': 'programming',
                'description': 'Master core programming languages including Python, C++, and Java from syntax to architecture.',
                'icon': 'code'
            },
            {
                'name': 'Web Development',
                'slug': 'web-development',
                'description': 'Build modern, responsive full-stack web applications with Python, Django, HTML5, and CSS3.',
                'icon': 'globe'
            },
            {
                'name': 'Data Structures & Algorithms',
                'slug': 'dsa',
                'description': 'Ace technical coding interviews and develop optimal problem-solving algorithms.',
                'icon': 'binary'
            },
            {
                'name': 'Database Management',
                'slug': 'database-management',
                'description': 'Learn relational database modeling, PostgreSQL queries, indexing, and transactional ACID integrity.',
                'icon': 'database'
            },
            {
                'name': 'Artificial Intelligence',
                'slug': 'artificial-intelligence',
                'description': 'Explore machine learning algorithms, deep neural architectures, and applied AI systems.',
                'icon': 'cpu'
            },
            {
                'name': 'Data Science',
                'slug': 'data-science',
                'description': 'Extract insights from data using Python, Pandas, statistical testing, and visual analytics.',
                'icon': 'pie-chart'
            },
            {
                'name': 'Computer Science Fundamentals',
                'slug': 'cs-fundamentals',
                'description': 'Understand operating systems, memory management, networks, and computer architecture.',
                'icon': 'server'
            },
            {
                'name': 'Career Development',
                'slug': 'career-development',
                'description': 'Build an impactful student portfolio, polish your tech resume, and ace technical behavioral interviews.',
                'icon': 'briefcase'
            },
        ]

        categories_map = {}
        for cat_info in categories_data:
            cat, created = Category.objects.update_or_create(
                slug=cat_info['slug'],
                defaults={
                    'name': cat_info['name'],
                    'description': cat_info['description'],
                    'icon': cat_info['icon']
                }
            )
            categories_map[cat.slug] = cat
        self.stdout.write(self.style.SUCCESS(f'Created/updated {len(categories_map)} categories.'))

        # 2. Courses and Lessons
        courses_data = [
            {
                'title': 'Python Programming from Scratch to OOP',
                'slug': 'python-programming-from-scratch',
                'category': 'programming',
                'difficulty': 'Beginner',
                'instructor_name': 'Dr. Elena Vance (Educational Demo)',
                'instructor_title': 'Senior Software Architect & CS Educator',
                'estimated_duration': '14 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?auto=format&fit=crop&w=800&q=80',
                'description': 'A comprehensive beginner-friendly introduction to Python 3. Learn fundamentals, control structures, functional programming, data manipulation, and Object-Oriented Design patterns.',
                'short_description': 'Learn core syntax, data structures, and Object-Oriented Programming with Python 3.',
                'learning_objectives': "Master Python syntax, types, and control flow\nWrite reusable functions and modular packages\nUnderstand Object-Oriented Programming (Classes & Inheritance)\nHandle errors and build real-world CLI scripts",
                'lessons': [
                    {
                        'chapter': 'Module 1: Getting Started with Python',
                        'title': 'Introduction to Python & Setup',
                        'order': 1,
                        'minutes': 15,
                        'content': """
<h3>Welcome to Python 3</h3>
<p>Python is an expressive, high-level, interpreted programming language favored by millions of developers worldwide for web engineering, data analysis, and artificial intelligence.</p>

<h4>Core Philosophy</h4>
<p>Python emphasizes readability and developer velocity. As formulated in <em>The Zen of Python</em>:</p>
<blockquote>Beautiful is better than ugly. Explicit is better than implicit. Simple is better than complex.</blockquote>

<h4>Your First Program</h4>
<pre><code># Hello World in Python
def greet_student(name: str) -> str:
    return f"Welcome to SkillSphere, {name}!"

if __name__ == "__main__":
    message = greet_student("Alex")
    print(message)
</code></pre>

<h4>Key Takeaways</h4>
<ul>
    <li>Python uses whitespace indentation rather than curly braces.</li>
    <li>Dynamic typing with modern optional type hints.</li>
    <li>Batteries included: a powerful standard library.</li>
</ul>
                        """,
                        'resources': '<a href="https://docs.python.org/3/tutorial/" target="_blank" class="text-primary-accent-light">Official Python 3 Documentation</a>'
                    },
                    {
                        'chapter': 'Module 1: Getting Started with Python',
                        'title': 'Variables, Data Types, and Operators',
                        'order': 2,
                        'minutes': 20,
                        'content': """
<h3>Python Fundamental Data Types</h3>
<p>Python provides built-in primitive and collection types that make storing and manipulating data intuitive.</p>

<h4>Primitives and Sequences</h4>
<pre><code># Primitives
student_id: int = 101
gpa: float = 3.85
is_enrolled: bool = True
course_name: str = "SkillSphere Phase 1"

# Collections
skills: list = ["Python", "Django", "PostgreSQL"]
student_info: dict = {
    "name": "Jordan",
    "level": "Beginner",
    "streak_days": 7
}
</code></pre>
                        """,
                        'resources': '<a href="https://docs.python.org/3/library/stdtypes.html" target="_blank" class="text-primary-accent-light">Python Standard Types Guide</a>'
                    },
                    {
                        'chapter': 'Module 2: Object-Oriented Programming',
                        'title': 'Classes, Objects, and Encapsulation',
                        'order': 3,
                        'minutes': 25,
                        'content': """
<h3>Object-Oriented Programming in Python</h3>
<p>OOP allows organizing software into modular, reusable classes that encapsulate state and behavior.</p>

<pre><code>class StudentAccount:
    def __init__(self, full_name: str, email: str):
        self.full_name = full_name
        self.email = email
        self._completed_courses = 0

    def complete_course(self, course_name: str) -> None:
        self._completed_courses += 1
        print(f"{self.full_name} completed: {course_name}!")

    @property
    def total_completed(self) -> int:
        return self._completed_courses

student = StudentAccount("Maya Patel", "maya@example.com")
student.complete_course("Python Fundamentals")
print("Total:", student.total_completed)
</code></pre>
                        """,
                        'resources': '<a href="https://realpython.com/python3-object-oriented-programming/" target="_blank" class="text-primary-accent-light">RealPython OOP Guide</a>'
                    }
                ]
            },
            {
                'title': 'Full-Stack Web Development with Django & Bootstrap',
                'slug': 'full-stack-django-web-dev',
                'category': 'web-development',
                'difficulty': 'Intermediate',
                'instructor_name': 'Marcus Vance (Educational Demo)',
                'instructor_title': 'Staff Web Engineer',
                'estimated_duration': '18 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=800&q=80',
                'description': 'Build industrial-strength full-stack web applications. Learn the Django MVT architecture, ORM queries, authentication, session security, Bootstrap 5 UI styling, and deployment.',
                'short_description': 'Build secure, scalable full-stack web platforms using Django 4 and Bootstrap 5.',
                'learning_objectives': "Design relational schemas using Django ORM\nBuild user authentication with login and session handling\nCreate responsive dark SaaS UI interfaces using Bootstrap 5\nDeploy Django applications with Whitenoise and Gunicorn",
                'lessons': [
                    {
                        'chapter': 'Module 1: Django Architecture',
                        'title': 'MVT Pattern & Project Architecture',
                        'order': 1,
                        'minutes': 20,
                        'content': """
<h3>Understanding Django's MVT Architecture</h3>
<p>Django follows the Model-View-Template pattern, separating data models, business logic views, and presentation templates.</p>

<h4>The Request-Response Lifecycle</h4>
<ol>
    <li><strong>Client Request:</strong> The browser issues an HTTP GET or POST request.</li>
    <li><strong>URLconf:</strong> Django matches the path against `urls.py`.</li>
    <li><strong>View Function:</strong> The view processes queries, interacts with models, and renders a response.</li>
    <li><strong>Templates:</strong> Django Template Language (DTL) evaluates context variables and produces HTML.</li>
</ol>
                        """,
                        'resources': '<a href="https://docs.djangoproject.com/en/4.2/" target="_blank" class="text-primary-accent-light">Django 4.2 Documentation</a>'
                    },
                    {
                        'chapter': 'Module 2: Database & ORM',
                        'title': 'Mastering the Django ORM',
                        'order': 2,
                        'minutes': 25,
                        'content': """
<h3>Django ORM Queries & Optimizations</h3>
<p>The Django ORM bridges Python code and relational database tables.</p>

<pre><code># Efficient querying with select_related to prevent N+1 queries
courses = Course.objects.filter(
    is_published=True
).select_related('category').annotate(
    enrollment_count=Count('enrollments')
)
</code></pre>
                        """,
                        'resources': '<a href="https://docs.djangoproject.com/en/4.2/topics/db/queries/" target="_blank" class="text-primary-accent-light">Django QuerySet Guide</a>'
                    }
                ]
            },
            {
                'title': 'Mastering Data Structures & Algorithms with Python',
                'slug': 'mastering-dsa-with-python',
                'category': 'dsa',
                'difficulty': 'Intermediate',
                'instructor_name': 'Prof. Dev Patel (Educational Demo)',
                'instructor_title': 'Algorithms Researcher',
                'estimated_duration': '20 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=800&q=80',
                'description': 'Deep-dive into essential data structures: arrays, hash maps, linked lists, trees, and graphs. Master algorithmic patterns like two pointers, sliding window, DFS, BFS, and dynamic programming.',
                'short_description': 'Ace technical interviews with asymptotic analysis, trees, graphs, and dynamic programming.',
                'learning_objectives': "Understand Big O time and space complexity\nImplement linked lists, binary trees, and heaps from scratch\nMaster graph traversal algorithms (BFS & DFS)\nSolve top interview algorithm patterns with confidence",
                'lessons': [
                    {
                        'chapter': 'Module 1: Complexity Analysis',
                        'title': 'Big-O Notation & Asymptotic Analysis',
                        'order': 1,
                        'minutes': 15,
                        'content': """
<h3>Big-O Complexity Analysis</h3>
<p>As software engineers, analyzing algorithm efficiency is critical for scalable systems.</p>

<h4>Common Complexities</h4>
<ul>
    <li><strong>O(1):</strong> Hash table lookup, array indexing.</li>
    <li><strong>O(log N):</strong> Binary search in a sorted array.</li>
    <li><strong>O(N):</strong> Linear scan over a sequence.</li>
    <li><strong>O(N log N):</strong> Merge sort, Quick sort.</li>
    <li><strong>O(N²):</strong> Nested loops, Bubble sort.</li>
</ul>
                        """,
                        'resources': '<a href="https://en.wikipedia.org/wiki/Big_O_notation" target="_blank" class="text-primary-accent-light">Big O Reference</a>'
                    }
                ]
            },
            {
                'title': 'Relational Databases & SQL Mastery with PostgreSQL',
                'slug': 'postgresql-database-mastery',
                'category': 'database-management',
                'difficulty': 'Intermediate',
                'instructor_name': 'Sarah Jenkins (Educational Demo)',
                'instructor_title': 'Principal Database Architect',
                'estimated_duration': '12 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1544383835-bda2bc66a55d?auto=format&fit=crop&w=800&q=80',
                'description': 'Master PostgreSQL from basic DDL/DML to complex CTEs, window functions, indexing strategies, transactions, and ACID principles.',
                'short_description': 'Design robust relational schemas and write high-performance SQL queries.',
                'learning_objectives': "Design normalized schemas up to 3NF\nMaster JOINs, GROUP BY, and Window Functions\nCreate B-Tree indexes and examine EXPLAIN ANALYZE\nUnderstand ACID transactions and locking levels",
                'lessons': [
                    {
                        'chapter': 'Module 1: Relational Modeling',
                        'title': 'Relational Schema Design & Normalization',
                        'order': 1,
                        'minutes': 20,
                        'content': """
<h3>Relational Schema Fundamentals</h3>
<p>PostgreSQL provides enterprise-grade data integrity, support for complex relational models, JSONB fields, and high concurrency.</p>
                        """,
                        'resources': '<a href="https://www.postgresql.org/docs/" target="_blank" class="text-primary-accent-light">PostgreSQL Official Documentation</a>'
                    }
                ]
            },
            {
                'title': 'Introduction to Artificial Intelligence & Neural Networks',
                'slug': 'intro-to-ai-and-neural-networks',
                'category': 'artificial-intelligence',
                'difficulty': 'Beginner',
                'instructor_name': 'Kavita Rao (Educational Demo)',
                'instructor_title': 'AI Research Scientist',
                'estimated_duration': '16 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=800&q=80',
                'description': 'Understand how modern artificial intelligence works. Learn machine learning foundations, supervised vs unsupervised learning, gradient descent, perceptrons, and multi-layer neural networks.',
                'short_description': 'Demystify machine learning, gradient descent, and deep neural architectures.',
                'learning_objectives': "Understand supervised and unsupervised learning paradigms\nImplement gradient descent from scratch\nConstruct simple multi-layer neural networks\nEvaluate models with precision, recall, and ROC curves",
                'lessons': [
                    {
                        'chapter': 'Module 1: AI Fundamentals',
                        'title': 'What is Machine Learning?',
                        'order': 1,
                        'minutes': 15,
                        'content': """
<h3>Machine Learning Overview</h3>
<p>Machine learning is the study of computer algorithms that improve automatically through experience and the use of data.</p>
                        """,
                        'resources': '<a href="https://scikit-learn.org/stable/" target="_blank" class="text-primary-accent-light">Scikit-Learn Documentation</a>'
                    }
                ]
            },
            {
                'title': 'Applied Data Science & Exploratory Data Analysis',
                'slug': 'applied-data-science-eda',
                'category': 'data-science',
                'difficulty': 'Beginner',
                'instructor_name': 'Arjun Mehta (Educational Demo)',
                'instructor_title': 'Head of Data Science',
                'estimated_duration': '15 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80',
                'description': 'Harness the power of Python data libraries: NumPy, Pandas, Matplotlib, and Seaborn. Clean messy datasets, discover patterns, and present actionable visual insights.',
                'short_description': 'Clean, analyze, and visualize complex datasets using NumPy, Pandas, and Matplotlib.',
                'learning_objectives': "Master Pandas DataFrames and Series manipulation\nClean missing, duplicated, and inconsistent data\nPerform exploratory data analysis and hypothesis testing\nCreate compelling charts and dashboards",
                'lessons': [
                    {
                        'chapter': 'Module 1: Pandas Fundamentals',
                        'title': 'DataFrames & Series Operations',
                        'order': 1,
                        'minutes': 18,
                        'content': """
<h3>Working with Pandas</h3>
<p>Pandas is Python's primary library for tabular data manipulation and analysis.</p>
                        """,
                        'resources': '<a href="https://pandas.pydata.org/docs/" target="_blank" class="text-primary-accent-light">Pandas Documentation</a>'
                    }
                ]
            },
            {
                'title': 'Computer Science Fundamentals: OS, Networks & Architecture',
                'slug': 'cs-fundamentals-os-networks',
                'category': 'cs-fundamentals',
                'difficulty': 'Advanced',
                'instructor_name': 'Prof. Alan Clark (Educational Demo)',
                'instructor_title': 'Distinguished CS Professor',
                'estimated_duration': '18 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80',
                'description': 'The foundational knowledge every software engineer needs: process scheduling, threads, concurrency, TCP/IP networking, and memory hierarchy.',
                'short_description': 'Deep-dive into operating system internals, TCP/IP networking, and hardware memory.',
                'learning_objectives': "Understand process scheduling and concurrency synchronization\nExplore the TCP/IP stack, sockets, and HTTP protocols\nExamine CPU cache lines, virtual memory, and paging",
                'lessons': [
                    {
                        'chapter': 'Module 1: Operating Systems',
                        'title': 'Processes, Threads, and Concurrency',
                        'order': 1,
                        'minutes': 22,
                        'content': """
<h3>Operating Systems: Processes vs Threads</h3>
<p>Understanding how the operating system manages execution contexts is vital for high-performance software engineering.</p>
                        """,
                        'resources': '<a href="https://pages.cs.wisc.edu/~remzi/OSTEP/" target="_blank" class="text-primary-accent-light">Operating Systems: Three Easy Pieces</a>'
                    }
                ]
            },
            {
                'title': 'Tech Career Accelerator: Portfolios, Resumes & Tech Interviews',
                'slug': 'tech-career-accelerator',
                'category': 'career-development',
                'difficulty': 'Beginner',
                'instructor_name': 'Rachel Green (Educational Demo)',
                'instructor_title': 'Engineering Hiring Lead',
                'estimated_duration': '8 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=800&q=80',
                'description': 'Turn your skills into career opportunities. Learn how to craft high-impact software engineering resumes, showcase projects in portfolio websites, and master behavioral interview techniques.',
                'short_description': 'Craft standout portfolios, technical resumes, and master developer interviews.',
                'learning_objectives': "Format developer resumes for Applicant Tracking Systems\nShowcase full-stack projects with live demos and clean READMEs\nMaster the STAR method for behavioral interviews\nNegotiate technical internship and entry-level offers",
                'lessons': [
                    {
                        'chapter': 'Module 1: Technical Portfolios',
                        'title': 'Building Projects That Stand Out to Recruiters',
                        'order': 1,
                        'minutes': 15,
                        'content': """
<h3>Showcasing Engineering Depth</h3>
<p>Recruiters look for projects that solve real problems, demonstrate full-stack architecture, and include robust automated tests.</p>
                        """,
                        'resources': '<a href="https://github.com" target="_blank" class="text-primary-accent-light">GitHub Developer Showcase</a>'
                    }
                ]
            }
        ]

        for c_data in courses_data:
            cat = categories_map[c_data['category']]
            course, _ = Course.objects.update_or_create(
                slug=c_data['slug'],
                defaults={
                    'title': c_data['title'],
                    'category': cat,
                    'difficulty': c_data['difficulty'],
                    'instructor_name': c_data['instructor_name'],
                    'instructor_title': c_data['instructor_title'],
                    'estimated_duration': c_data['estimated_duration'],
                    'thumbnail_url': c_data['thumbnail_url'],
                    'description': c_data['description'],
                    'short_description': c_data['short_description'],
                    'learning_objectives': c_data['learning_objectives'],
                    'is_published': True
                }
            )

            for l_data in c_data['lessons']:
                Lesson.objects.update_or_create(
                    course=course,
                    lesson_order=l_data['order'],
                    defaults={
                        'chapter_name': l_data['chapter'],
                        'title': l_data['title'],
                        'estimated_minutes': l_data['minutes'],
                        'content': l_data['content'].strip(),
                        'external_resources': l_data['resources'].strip()
                    }
                )

        self.stdout.write(self.style.SUCCESS('Created 8 comprehensive courses with structured lessons.'))

        # 3. Create Demo Student Account
        demo_user, created = User.objects.get_or_create(
            username='student_demo',
            defaults={
                'email': 'student@skillsphere.edu',
                'first_name': 'Ankit',
                'last_name': 'Kumar'
            }
        )
        if created:
            demo_user.set_password('Password123!')
            demo_user.save()

        # Update profile
        profile, _ = StudentProfile.objects.get_or_create(user=demo_user)
        profile.full_name = 'Ankit Kumar'
        profile.education_level = 'undergraduate'
        profile.institution = 'Indian Institute of Technology / Engineering College'
        profile.learning_level = 'intermediate'
        profile.set_interests_list(['python', 'web_dev', 'dsa'])
        profile.career_goal = 'Full-Stack Software Engineer'
        profile.save()

        # Enroll demo student in Python and Django courses
        python_course = Course.objects.get(slug='python-programming-from-scratch')
        django_course = Course.objects.get(slug='full-stack-django-web-dev')

        Enrollment.objects.get_or_create(user=demo_user, course=python_course)
        Enrollment.objects.get_or_create(user=demo_user, course=django_course)

        # Mark some lessons as completed for Python course to demonstrate real progress
        python_lessons = list(python_course.lessons.all().order_by('lesson_order'))
        if len(python_lessons) >= 2:
            LessonProgress.objects.update_or_create(
                user=demo_user,
                lesson=python_lessons[0],
                defaults={'is_completed': True, 'completed_at': timezone.now() - timedelta(days=2)}
            )
            LessonProgress.objects.update_or_create(
                user=demo_user,
                lesson=python_lessons[1],
                defaults={'is_completed': True, 'completed_at': timezone.now() - timedelta(days=1)}
            )

        # Seed sample learning goals
        today = timezone.now().date()
        goals_data = [
            {
                'title': 'Master Python OOP & Design Patterns',
                'description': 'Finish classes, polymorphism, and inheritance lessons.',
                'target_date': today + timedelta(days=5),
                'is_completed': False,
            },
            {
                'title': 'Build SkillSphere Phase 1 Full-Stack Project',
                'description': 'Deliver authentication, courses, dashboard, and testing.',
                'target_date': today + timedelta(days=2),
                'is_completed': True,
            },
            {
                'title': 'Solve 15 Tree & Graph Interview Problems',
                'description': 'Practice DFS, BFS, and Dijkstra on LeetCode/SkillSphere.',
                'target_date': today + timedelta(days=12),
                'is_completed': False,
            }
        ]

        for g_data in goals_data:
            LearningGoal.objects.update_or_create(
                user=demo_user,
                title=g_data['title'],
                defaults={
                    'description': g_data['description'],
                    'target_date': g_data['target_date'],
                    'is_completed': g_data['is_completed']
                }
            )

        # Seed activities
        LearningActivity.objects.get_or_create(
            user=demo_user,
            activity_type='ENROLL',
            description='Enrolled in Python Programming from Scratch to OOP'
        )
        LearningActivity.objects.get_or_create(
            user=demo_user,
            activity_type='COMPLETE_LESSON',
            description="Completed 'Introduction to Python & Setup'"
        )

        # 4. Phase 2 Badges Seeding
        from gamification.models import Badge, UserGamification, UserBadge
        from gamification.services import award_user_xp, award_badge_if_eligible
        from assessments.models import SkillAssessment, AssessmentQuestion
        from roadmaps.models import LearningRoadmap, RoadmapMilestone

        badges_info = [
            {'slug': 'first-course-complete', 'name': 'First Course Completed', 'desc': 'Awarded for achieving 100% completion in your first course.', 'icon': 'award', 'xp': 150},
            {'slug': 'explorer-badge', 'name': 'Skill Explorer', 'desc': 'Earned by reaching 100+ platform Experience Points.', 'icon': 'compass', 'xp': 50},
            {'slug': '7-day-streak', 'name': '7-Day Learning Streak', 'desc': 'Maintained consistent study activity for 7 consecutive days.', 'icon': 'flame', 'xp': 100},
            {'slug': 'dsa-explorer', 'name': 'DSA Explorer', 'desc': 'Completed your first Data Structures & Algorithms milestone.', 'icon': 'binary', 'xp': 50},
            {'slug': 'first-assessment-complete', 'name': 'First Assessment Completed', 'desc': 'Took and completed your first technical skill assessment.', 'icon': 'clipboard-check', 'xp': 50},
            {'slug': 'first-roadmap-complete', 'name': 'First Roadmap Completed', 'desc': 'Successfully completed all phases of a learning roadmap.', 'icon': 'map', 'xp': 200},
            {'slug': 'interview-ready', 'name': 'Interview Ready', 'desc': 'Completed an AI Technical Mock Interview session.', 'icon': 'message-square-code', 'xp': 75},
        ]

        for b in badges_info:
            Badge.objects.update_or_create(
                slug=b['slug'],
                defaults={'name': b['name'], 'description': b['desc'], 'icon': b['icon'], 'xp_requirement': b['xp']}
            )
        self.stdout.write(self.style.SUCCESS(f'Created/updated {len(badges_info)} achievement badges.'))

        # 5. Phase 2 Skill Assessments Seeding
        assessments_info = [
            {
                'title': 'Python Fundamentals & Syntax Assessment',
                'category': 'Python',
                'difficulty': 'Beginner',
                'minutes': 15,
                'questions': [
                    {
                        'q': 'Which of the following data structures in Python is immutable?',
                        'tag': 'Data Types',
                        'a': 'List', 'b': 'Tuple', 'c': 'Dictionary', 'd': 'Set',
                        'ans': 'B',
                        'exp': 'Tuples are immutable sequences in Python; once initialized, their elements cannot be modified.'
                    },
                    {
                        'q': 'What is the primary purpose of the `__init__` method in a Python class?',
                        'tag': 'OOP',
                        'a': 'To destroy an object', 'b': 'To import external modules', 'c': 'To initialize a new instance of the class', 'd': 'To override operators',
                        'ans': 'C',
                        'exp': 'The `__init__` method acts as the constructor in Python, executing automatically when a new class instance is instantiated.'
                    },
                    {
                        'q': 'What does a Python generator function use to return intermediate values?',
                        'tag': 'Advanced Python',
                        'a': 'return', 'b': 'yield', 'c': 'emit', 'd': 'send',
                        'ans': 'B',
                        'exp': 'The `yield` keyword pauses function execution and emits a value to the caller, resuming state on the next iteration.'
                    },
                    {
                        'q': 'What is the time complexity of looking up a key in a standard Python dictionary?',
                        'tag': 'Complexity',
                        'a': 'O(1) on average', 'b': 'O(N)', 'c': 'O(log N)', 'd': 'O(N²)',
                        'ans': 'A',
                        'exp': 'Python dictionaries use hash tables under the hood, providing average O(1) constant time lookups.'
                    }
                ]
            },
            {
                'title': 'Django Full-Stack Architecture Assessment',
                'category': 'Django',
                'difficulty': 'Intermediate',
                'minutes': 15,
                'questions': [
                    {
                        'q': 'What architectural pattern does Django follow?',
                        'tag': 'Architecture',
                        'a': 'MVC (Model View Controller)', 'b': 'MVT (Model View Template)', 'c': 'MVVM (Model View ViewModel)', 'd': 'Flux',
                        'ans': 'B',
                        'exp': 'Django follows the Model-View-Template pattern where the template handles presentation and the view handles business logic.'
                    },
                    {
                        'q': 'Which ORM method is used to eliminate N+1 queries when traversing ForeignKey relationships?',
                        'tag': 'ORM Optimization',
                        'a': 'select_related()', 'b': 'filter()', 'c': 'only()', 'd': 'values()',
                        'ans': 'A',
                        'exp': 'select_related() performs an SQL JOIN and includes the related fields in the SELECT statement to prevent N+1 queries.'
                    },
                    {
                        'q': 'Where are CSRF tokens typically required in standard Django templates?',
                        'tag': 'Security',
                        'a': 'Inside HTTP GET forms', 'b': 'Inside HTTP POST forms', 'c': 'Inside image tags', 'd': 'Inside the <head> tag only',
                        'ans': 'B',
                        'exp': 'POST forms that mutate server-side state require the {% csrf_token %} tag to protect against Cross-Site Request Forgery.'
                    }
                ]
            },
            {
                'title': 'Data Structures & Algorithms Diagnostic Quiz',
                'category': 'DSA',
                'difficulty': 'Intermediate',
                'minutes': 20,
                'questions': [
                    {
                        'q': 'What is the worst-case time complexity of Quick Sort with poor pivot selection?',
                        'tag': 'Sorting',
                        'a': 'O(N log N)', 'b': 'O(N)', 'c': 'O(N²)', 'd': 'O(1)',
                        'ans': 'C',
                        'exp': 'When the pivot chosen is consistently the extreme element on already sorted data, QuickSort degrades to O(N²).'
                    },
                    {
                        'q': 'Which data structure follows a Last-In, First-Out (LIFO) order?',
                        'tag': 'Data Structures',
                        'a': 'Queue', 'b': 'Stack', 'c': 'Heap', 'd': 'Binary Tree',
                        'ans': 'B',
                        'exp': 'A Stack operates strictly on a Last-In, First-Out (LIFO) basis using push and pop operations.'
                    }
                ]
            },
            {
                'title': 'PostgreSQL & Relational SQL Assessment',
                'category': 'SQL',
                'difficulty': 'Beginner',
                'minutes': 15,
                'questions': [
                    {
                        'q': 'Which SQL clause is used to filter groups created by a GROUP BY clause?',
                        'tag': 'SQL Queries',
                        'a': 'WHERE', 'b': 'HAVING', 'c': 'ORDER BY', 'd': 'FILTER',
                        'ans': 'B',
                        'exp': 'WHERE filters rows before grouping; HAVING filters aggregated groups after grouping.'
                    },
                    {
                        'q': 'What does the "A" in ACID database transactions stand for?',
                        'tag': 'Database Theory',
                        'a': 'Asynchronous', 'b': 'Atomicity', 'c': 'Availability', 'd': 'Authentication',
                        'ans': 'B',
                        'exp': 'Atomicity guarantees that all statements within a transaction succeed completely or none are applied (all-or-nothing).'
                    }
                ]
            }
        ]

        for a_info in assessments_info:
            ass, _ = SkillAssessment.objects.update_or_create(
                title=a_info['title'],
                defaults={
                    'category': a_info['category'],
                    'difficulty': a_info['difficulty'],
                    'time_limit_minutes': a_info['minutes'],
                    'is_active': True,
                }
            )
            for q_data in a_info['questions']:
                AssessmentQuestion.objects.update_or_create(
                    assessment=ass,
                    question_text=q_data['q'],
                    defaults={
                        'topic_tag': q_data['tag'],
                        'option_a': q_data['a'],
                        'option_b': q_data['b'],
                        'option_c': q_data['c'],
                        'option_d': q_data['d'],
                        'correct_answer': q_data['ans'],
                        'explanation': q_data['exp'],
                    }
                )
        self.stdout.write(self.style.SUCCESS('Created 4 comprehensive skill assessments with structured questions.'))

        # 6. Initialize Demo Student Gamification & Sample Roadmap
        award_user_xp(demo_user, 120, "Early student onboarding & curriculum progress")
        award_badge_if_eligible(demo_user, 'explorer-badge')

        # Sample Roadmap for Demo Student
        demo_roadmap, _ = LearningRoadmap.objects.update_or_create(
            user=demo_user,
            title='Python Full-Stack Backend Mastery',
            defaults={
                'target_skill': 'Python & Django',
                'current_level': 'Intermediate',
                'career_goal': 'Full-Stack Software Engineer',
                'daily_time': '1 hour/day',
                'duration': '3 months',
            }
        )
        RoadmapMilestone.objects.update_or_create(
            roadmap=demo_roadmap,
            milestone_order=1,
            defaults={
                'title': 'Phase 1: Advanced Python & Clean Code',
                'description': 'Master object-oriented design, decorators, context managers, and type hints.',
                'topics_json': json.dumps(['OOP Design Patterns', 'Context Managers', 'Generators & Iterators', 'Type Annotations']),
                'mini_project': 'CLI File Audit & Compression Utility',
                'is_completed': True,
                'completed_at': timezone.now() - timedelta(days=2),
            }
        )
        RoadmapMilestone.objects.update_or_create(
            roadmap=demo_roadmap,
            milestone_order=2,
            defaults={
                'title': 'Phase 2: Django ORM & Database Optimization',
                'description': 'Design normalized schemas, master select_related, and configure PostgreSQL transactions.',
                'topics_json': json.dumps(['Relational Modeling', 'QuerySet Caching', 'PostgreSQL B-Tree Indexes', 'Database Migrations']),
                'mini_project': 'E-Commerce Inventory & Order Microservice',
                'is_completed': False,
            }
        )
        RoadmapMilestone.objects.update_or_create(
            roadmap=demo_roadmap,
            milestone_order=3,
            defaults={
                'title': 'Phase 3: RESTful APIs & Authentication Services',
                'description': 'Build token-authenticated endpoints using Django REST Framework with rate limiting.',
                'topics_json': json.dumps(['DRF Serializers', 'JWT Tokens', 'Throttling & Permissions', 'API Unit Tests']),
                'mini_project': 'Production REST API for SkillSphere Mobile',
                'is_completed': False,
            }
        )

        # =========================================================================
        # PHASE 3: Career Hub, Opportunities, Community, Collaboration, Events & Certs
        # =========================================================================
        self.stdout.write(self.style.NOTICE('Seeding Phase 3 Career, Community & Opportunities data...'))

        # 1. Opportunities
        opps_data = [
            {
                'title': 'Open Source Software Engineering Mentorship',
                'organization': 'The Linux Foundation',
                'category': 'software-development',
                'work_mode': 'remote',
                'location': 'Global / Remote',
                'required_skills': 'Python, C, Linux Kernel, Git, System Architecture',
                'eligibility': 'Full-time or part-time enrolled university students and beginners.',
                'stipend_information': '$3,000 / term stipend',
                'application_url': 'https://mentorship.lfx.linuxfoundation.org/',
                'deadline': timezone.now().date() + timedelta(days=45),
                'description': 'Work directly with open source maintainers on cloud native, hyperledger, and kernel-level infrastructure tools.',
            },
            {
                'title': 'Global Contributor Fellowship 2026',
                'organization': 'Major League Hacking (MLH)',
                'category': 'python-development',
                'work_mode': 'remote',
                'location': 'Remote / Worldwide',
                'required_skills': 'Python, Django, Flask, JavaScript, REST APIs',
                'eligibility': 'Students actively building software projects and seeking engineering mentorship.',
                'stipend_information': '$4,000 educational stipend',
                'application_url': 'https://fellowship.mlh.io/',
                'deadline': timezone.now().date() + timedelta(days=60),
                'description': 'A 12-week remote fellowship where students contribute to high-impact open source repositories used by millions.',
            },
            {
                'title': 'Google Summer of Code (GSoC) Contributor',
                'organization': 'Google Open Source Programs',
                'category': 'software-development',
                'work_mode': 'remote',
                'location': 'Worldwide Remote',
                'required_skills': 'Python, C++, Java, Data Structures, Algorithms, Git',
                'eligibility': 'Students and new contributors age 18+ eligible to work in their country of residence.',
                'stipend_information': 'Stipend adjusted by country ($1,500 - $3,000)',
                'application_url': 'https://summerofcode.withgoogle.com/',
                'deadline': timezone.now().date() + timedelta(days=90),
                'description': 'An international annual program focused on bringing new contributors into open source software development organizations.',
            },
            {
                'title': 'AI & Machine Learning Research Fellowship',
                'organization': 'Open Science Foundation',
                'category': 'ai-ml',
                'work_mode': 'hybrid',
                'location': 'San Francisco, CA / Remote',
                'required_skills': 'Python, PyTorch, Scikit-Learn, Statistics, Pandas',
                'eligibility': 'Undergraduate and graduate students with demonstrated ML course foundation.',
                'stipend_information': '$2,500 / month',
                'application_url': 'https://openscience.org/fellowships',
                'deadline': timezone.now().date() + timedelta(days=30),
                'description': 'Assist principal investigators in evaluating large language models and developing reproducible benchmark datasets.',
            },
            {
                'title': 'Frontend & Design System Engineering Intern',
                'organization': 'DesignScale Labs',
                'category': 'web-development',
                'work_mode': 'remote',
                'location': 'Remote',
                'required_skills': 'JavaScript, React, CSS3, Figma, Web Accessibility',
                'eligibility': 'College students with a public portfolio demonstrating responsive UI components.',
                'stipend_information': '$2,000 / month',
                'application_url': 'https://designscale.dev/careers',
                'deadline': timezone.now().date() + timedelta(days=25),
                'description': 'Build accessible component libraries, documentation, and fluid micro-interactions for modern web platforms.',
            }
        ]

        created_opps = []
        for o_data in opps_data:
            opp, _ = Opportunity.objects.update_or_create(
                title=o_data['title'],
                organization=o_data['organization'],
                defaults=o_data
            )
            created_opps.append(opp)

        # Save an opportunity for demo student in tracker
        if created_opps:
            SavedOpportunity.objects.update_or_create(
                user=demo_user,
                opportunity=created_opps[0],
                defaults={
                    'application_status': 'applied',
                    'application_notes': 'Applied via official LFX portal. Prepared proposal on async job queue architecture.',
                    'applied_at': timezone.now() - timedelta(days=3),
                }
            )
            if len(created_opps) > 1:
                SavedOpportunity.objects.update_or_create(
                    user=demo_user,
                    opportunity=created_opps[1],
                    defaults={
                        'application_status': 'interview',
                        'application_notes': 'Interview round scheduled with fellowship lead next Monday!',
                        'applied_at': timezone.now() - timedelta(days=7),
                    }
                )

        # 2. Events & Hackathons
        events_data = [
            {
                'title': 'Global University AI Hackathon 2026',
                'organizer': 'Global Collegiate Tech League',
                'category': 'hackathon',
                'is_online': True,
                'location': 'Virtual / Global Discord',
                'start_date': timezone.now() + timedelta(days=14),
                'end_date': timezone.now() + timedelta(days=16),
                'registration_deadline': timezone.now() + timedelta(days=10),
                'registration_url': 'https://collegiate-hackathon.org/',
                'description': 'A 48-hour virtual hackathon where student teams design and build innovative AI solutions addressing climate, education, and accessibility.',
            },
            {
                'title': 'International Collegiate Coding Championship',
                'organizer': 'AlgoSphere Tech Society',
                'category': 'competition',
                'is_online': True,
                'location': 'Online Competitive Platform',
                'start_date': timezone.now() + timedelta(days=21),
                'end_date': timezone.now() + timedelta(days=21, hours=5),
                'registration_deadline': timezone.now() + timedelta(days=18),
                'registration_url': 'https://algosphere.org/championship',
                'description': 'Speed-coding challenge featuring algorithmic problem sets across graph theory, dynamic programming, and binary search trees.',
            },
            {
                'title': 'PyCon US Student Developer Summit',
                'organizer': 'Python Software Foundation',
                'category': 'conference',
                'is_online': False,
                'location': 'Pittsburgh, PA',
                'start_date': timezone.now() + timedelta(days=75),
                'end_date': timezone.now() + timedelta(days=78),
                'registration_deadline': timezone.now() + timedelta(days=40),
                'registration_url': 'https://us.pycon.org/students',
                'description': 'The premier global conference for the Python programming community featuring dedicated talks, career fairs, and open source sprints for university students.',
            }
        ]

        created_events = []
        for e_data in events_data:
            ev, _ = Event.objects.update_or_create(
                title=e_data['title'],
                organizer=e_data['organizer'],
                defaults=e_data
            )
            created_events.append(ev)

        if created_events:
            SavedEvent.objects.update_or_create(
                user=demo_user,
                event=created_events[0],
                defaults={'reminder_set': True}
            )

        # 3. Community Discussions
        posts_data = [
            {
                'title': 'How to optimize N+1 queries in Django ORM with select_related vs prefetch_related?',
                'category': 'python',
                'content': (
                    "When building the courses and lessons view in Django, I noticed that querying enrolled courses was "
                    "firing multiple duplicate SELECT queries for each lesson.\n\n"
                    "I solved this by using:\n"
                    "courses = Course.objects.prefetch_related('lessons', 'categories').select_related('instructor')\n\n"
                    "This reduced total database queries from 48 down to 3! Sharing this pattern for anyone preparing for backend interviews."
                )
            },
            {
                'title': 'Tips for your first technical coding interview: What I learned from mock interviews',
                'category': 'interview-prep',
                'content': (
                    "I just completed my 4th mock interview session on SkillSphere and wanted to share 3 key takeaways:\n"
                    "1. Always clarify edge cases before typing code (e.g., empty arrays, null values, negative integers).\n"
                    "2. State your time and space complexity out loud.\n"
                    "3. Practice writing clean variable names rather than single-letter identifiers.\n\n"
                    "Good luck everyone!"
                )
            },
            {
                'title': 'Project Showcase: Built a Real-Time Collaboration Hub for Students',
                'category': 'project-showcase',
                'content': (
                    "I just published my capstone project using Django, PostgreSQL, and Bootstrap 5!\n"
                    "It features role-based teammate recruitment and instant notifications. "
                    "Check out my public developer portfolio at /u/student/ and let me know your thoughts!"
                )
            }
        ]

        for p_data in posts_data:
            post, _ = CommunityPost.objects.update_or_create(
                title=p_data['title'],
                defaults={
                    'user': demo_user,
                    'category': p_data['category'],
                    'content': p_data['content'],
                    'is_approved': True,
                }
            )
            CommunityComment.objects.get_or_create(
                post=post,
                user=demo_user,
                content="Great insights! Keep sharing your learnings."
            )

        # 4. Collaboration Project
        collab_proj, _ = CollaborationProject.objects.update_or_create(
            owner=demo_user,
            title='AI Study Companion & Spaced Repetition Engine',
            defaults={
                'description': (
                    'Developing an open-source spaced repetition platform that uses flashcards and AI concept explainers '
                    'to assist engineering students in preparing for technical exams and DSA interviews.'
                ),
                'category': 'Web Development',
                'difficulty': 'intermediate',
                'technologies': 'Python, Django, PostgreSQL, React, Docker',
                'required_roles': 'Backend Engineer, Frontend Engineer, UI/UX Designer',
                'team_size': 4,
                'expected_duration': '6 weeks',
                'status': 'recruiting',
                'github_repo': 'https://github.com/skillsphere/ai-study-companion'
            }
        )

        # 5. Certificates
        # Issue verified certificate to demo_user for first course
        first_course = Course.objects.first()
        if first_course:
            Certificate.objects.update_or_create(
                user=demo_user,
                course=first_course,
                defaults={
                    'title': f"Course Mastery: {first_course.title}",
                    'certificate_id': 'SKILL-2026-DEMO001',
                    'issued_at': timezone.now() - timedelta(days=5),
                    'verification_status': True,
                    'recipient_name': 'Alex Mercer',
                    'criteria_met': f"Successfully completed all curriculum modules, exercises, and assessments in {first_course.title}."
                }
            )

        # 6. Career Profile
        CareerProfile.objects.update_or_create(
            user=demo_user,
            defaults={
                'professional_headline': 'Aspiring Full-Stack Python Developer | CS Sophomore',
                'professional_summary': 'Dedicated software developer with hands-on experience building Django backends, RESTful APIs, and relational database systems. Passionate about clean code and scalable architectures.',
                'target_career_path': 'fullstack-developer',
                'career_interests': ['Web Development', 'Distributed Systems', 'Cloud Architecture'],
                'preferred_roles': ['Software Engineer', 'Backend Developer', 'Full Stack Developer'],
                'preferred_locations': ['Remote', 'San Francisco', 'New York'],
            }
        )

        # 7. Portfolio & Projects
        demo_portfolio, _ = Portfolio.objects.update_or_create(
            user=demo_user,
            defaults={
                'username': demo_user.username,
                'title': 'Full Stack Developer & Systems Enthusiast',
                'about': 'Passionate about engineering reliable web applications with Python, Django, and modern frontend tools. Always building, learning, and contributing.',
                'template': 'modern',
                'theme': 'dark',
                'accent_color': '#8B5CF6',
                'github_url': 'https://github.com/student',
                'linkedin_url': 'https://linkedin.com/in/student',
                'is_public': True,
                'show_certifications': True,
                'show_skills': True,
            }
        )
        PortfolioProject.objects.update_or_create(
            portfolio=demo_portfolio,
            title='SkillSphere Full-Stack Learning Platform',
            defaults={
                'description': 'A modular full-stack learning and career ecosystem with automated progress metrics, AI-assisted roadmaps, and career readiness analytics.',
                'technologies': 'Python, Django, PostgreSQL, Bootstrap 5, Chart.js',
                'features': 'Role-based access, automated lesson tracking, ReportLab PDF generation, ATS resume auditing',
                'github_url': 'https://github.com/student/skillsphere',
                'is_featured': True,
                'display_order': 1
            }
        )

        # 8. Resume
        Resume.objects.update_or_create(
            user=demo_user,
            is_primary=True,
            defaults={
                'title': 'Alex Mercer - Software Engineer CV',
                'template': 'ats',
                'ats_score': 88,
                'resume_data': {
                    'contact': {
                        'full_name': 'Alex Mercer',
                        'headline': 'Software Engineer & Full Stack Developer',
                        'email': 'student@skillsphere.edu',
                        'phone': '+1 (555) 019-2834',
                        'location': 'San Francisco, CA (Open to Remote)',
                        'links': 'github.com/student • linkedin.com/in/student'
                    },
                    'summary': 'Dedicated Software Engineer with a solid foundation in Python, Django, PostgreSQL, and modern web application development. Experienced in designing modular REST APIs, optimizing relational queries, and building scalable full-stack applications.',
                    'education': [
                        {
                            'school': 'University of California, Berkeley',
                            'degree': 'B.S. in Computer Science',
                            'year': '2023 - 2027',
                            'gpa': '3.85 / 4.0'
                        }
                    ],
                    'skills': ['Python', 'Django', 'Django REST Framework', 'PostgreSQL', 'JavaScript', 'HTML5/CSS3', 'Git', 'Docker', 'Redis'],
                    'experience': [
                        {
                            'role': 'Software Engineering Intern',
                            'company': 'OpenSource Innovations',
                            'dates': 'June 2025 - August 2025',
                            'description': 'Engineered asynchronous task queues utilizing Celery and Redis. Reduced database query latency by 32% using optimized Django ORM prefetching.'
                        }
                    ],
                    'projects': [
                        {
                            'title': 'SkillSphere Full-Stack Learning Platform',
                            'technologies': 'Python, Django, PostgreSQL, ReportLab, Chart.js',
                            'description': 'Architected an end-to-end learning and career development platform featuring automated lesson progress tracking, cryptographic certificate verification, and ATS resume auditing.'
                        }
                    ],
                    'certifications': [
                        'Course Mastery: Python Core & Advanced - SkillSphere Verified',
                        'PostgreSQL Relational Database Architect - SkillSphere Verified'
                    ]
                }
            }
        )

        # 9. Notifications
        Notification.objects.update_or_create(
            user=demo_user,
            title='Welcome to SkillSphere Phase 3!',
            defaults={
                'message': 'Your complete student career development suite is ready: explore the Career Hub, build your ATS resume, and publish your portfolio!',
                'notification_type': 'system',
                'link': '/career-hub/',
                'is_read': False,
            }
        )
        Notification.objects.update_or_create(
            user=demo_user,
            title='Official Certificate Issued 🎓',
            defaults={
                'message': 'Your certificate for Python Core & Advanced is available for PDF download and public verification.',
                'notification_type': 'certificate_issued',
                'link': '/certificates/',
                'is_read': False,
            }
        )

        self.stdout.write(self.style.SUCCESS(
            'Successfully seeded demo student & Phase 3 data!\n'
            'Login: student@skillsphere.edu / Password123!'
        ))
