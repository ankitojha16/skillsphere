# Course Curriculum Data 2.0 for SkillSphere
# Defines Modules, Lessons (with Video, Notes, Exercises), and Assessments (Final Quiz & Mock Test)

COURSES_CURRICULUM = {
    'python-programming-from-scratch': {
        'modules': [
            {
                'order': 1,
                'title': 'Python Syntax, Types & Control Flow',
                'description': 'Master variable assignments, built-in primitive types, control statements, and loops.',
                'lessons': [
                    {
                        'order': 1,
                        'chapter': 'Syntax & Types',
                        'title': 'Variables, Types, and Expressions',
                        'minutes': 15,
                        'video_url': 'https://www.youtube.com/watch?v=kqtD5dpn9C8',
                        'video_duration': 600,
                        'content': """<h3>Variables, Primitive Types, and Dynamic Typing in Python</h3>
<p>Python is dynamically and strongly typed. Variables in Python are labels referencing in-memory objects rather than fixed memory slots.</p>
<h4>Fundamental Data Types</h4>
<ul>
    <li><strong>int & float:</strong> Arbitrary-precision integers and double-precision 64-bit IEEE 754 floats.</li>
    <li><strong>str:</strong> Immutable sequence of Unicode code points.</li>
    <li><strong>bool:</strong> Subclass of integer (`True == 1`, `False == 0`).</li>
</ul>
<pre><code class="language-python"># Dynamic variable assignment
age: int = 24
target_gpa: float = 3.85
student_name: str = "Elena"
is_graduating: bool = True

print(f"{student_name} (Age {age}) - Target GPA: {target_gpa}")
</code></pre>""",
                        'key_takeaways': [
                            "Python binds variable names to objects via references, not fixed memory slots.",
                            "Integers have arbitrary precision and do not overflow in Python 3.",
                            "Strings are immutable sequences of Unicode characters."
                        ],
                        'common_mistakes': [
                            "Assuming mutable default values in functions (e.g. `def f(x=[])`).",
                            "Confusing equality `==` (value check) with identity `is` (memory reference check)."
                        ],
                        'resources': '<a href="https://docs.python.org/3/tutorial/introduction.html" target="_blank" class="text-primary-accent-light">Python 3 Official Tutorial</a>',
                        'exercise': {
                            'title': 'Calculate Formatted Temperature',
                            'instructions': 'Write a function `celsius_to_fahrenheit(c)` that returns the Fahrenheit value rounded to 2 decimal places. Formula: `(c * 9/5) + 32`.',
                            'starter_code': "def celsius_to_fahrenheit(c: float) -> float:\n    # Return calculated fahrenheit value\n    return 0.0\n",
                            'expected_output': 'celsius_to_fahrenheit(100) == 212.0 and celsius_to_fahrenheit(0) == 32.0',
                            'hints': 'Multiply c by 9/5 and add 32. Use round(result, 2).'
                        }
                    },
                    {
                        'order': 2,
                        'chapter': 'Control Flow',
                        'title': 'Control Flow: If-Else & Loops',
                        'minutes': 20,
                        'video_url': 'https://www.youtube.com/watch?v=PqFKRqpHrjw',
                        'video_duration': 720,
                        'content': """<h3>Branching Logic and Loop Iterations</h3>
<p>Python provides `if`, `elif`, and `else` blocks for conditional evaluation, and `for` and `while` loops for iteration.</p>
<h4>Iterating with Enumerate and Zip</h4>
<pre><code class="language-python">skills = ["Python", "Django", "PostgreSQL", "Docker"]
for index, skill in enumerate(skills, start=1):
    print(f"Skill #{index}: {skill}")
</code></pre>""",
                        'key_takeaways': [
                            "Use `enumerate()` whenever you need index and element simultaneously.",
                            "Loop `else` blocks execute only if the loop completes without a `break`."
                        ],
                        'common_mistakes': [
                            "Modifying a list while iterating over it.",
                            "Writing infinite `while` loops without loop counter increments."
                        ],
                        'resources': '<a href="https://realpython.com/python-for-loop/" target="_blank" class="text-primary-accent-light">RealPython Loops Deep Dive</a>',
                        'exercise': {
                            'title': 'Filter Even Numbers',
                            'instructions': 'Write a function `filter_evens(nums)` that takes a list of integers and returns a new list containing only the even numbers.',
                            'starter_code': "def filter_evens(nums: list) -> list:\n    # Return list of even numbers\n    return []\n",
                            'expected_output': 'filter_evens([1, 2, 3, 4, 5, 6]) == [2, 4, 6]',
                            'hints': 'Use list comprehension `[n for n in nums if n % 2 == 0]`.'
                        }
                    }
                ]
            },
            {
                'order': 2,
                'title': 'Data Structures & Collections',
                'description': 'Master lists, dictionaries, sets, tuples, and high-performance comprehensions.',
                'lessons': [
                    {
                        'order': 3,
                        'chapter': 'Data Structures',
                        'title': 'Lists, Dictionaries, and Sets',
                        'minutes': 25,
                        'video_url': 'https://www.youtube.com/watch?v=daefaLgNkw0',
                        'video_duration': 800,
                        'content': """<h3>Built-in Python Collections</h3>
<p>Python data structures are optimized C implementations:</p>
<ul>
    <li><strong>List:</strong> Dynamic array, amortized O(1) appends, O(n) arbitrary inserts.</li>
    <li><strong>Dict:</strong> Hash table, average O(1) key lookups and inserts.</li>
    <li><strong>Set:</strong> Hash table storing unique keys without values, O(1) membership testing.</li>
</ul>
<pre><code class="language-python"># Dictionary Comprehension
squares = {x: x**2 for x in range(1, 6)}
print("Squares:", squares)
</code></pre>""",
                        'key_takeaways': [
                            "Dict lookups and set membership operations are average O(1) time complexity.",
                            "Keys in dictionaries and elements in sets must be hashable (immutable)."
                        ],
                        'common_mistakes': [
                            "Using a mutable list as a dictionary key or set item.",
                            "Using list `in` operator for membership testing in large datasets instead of `set`."
                        ],
                        'resources': '<a href="https://docs.python.org/3/tutorial/datastructures.html" target="_blank" class="text-primary-accent-light">Python Data Structures</a>',
                        'exercise': {
                            'title': 'Word Frequency Counter',
                            'instructions': 'Write a function `count_words(words)` that returns a dictionary mapping each unique word to its occurrences in the list.',
                            'starter_code': "def count_words(words: list) -> dict:\n    # Return dict with word frequencies\n    return {}\n",
                            'expected_output': "count_words(['apple', 'banana', 'apple']) == {'apple': 2, 'banana': 1}",
                            'hints': 'Use dict.get(w, 0) + 1 or collections.Counter.'
                        }
                    }
                ]
            },
            {
                'order': 3,
                'title': 'Object-Oriented Programming (OOP) & Clean Architecture',
                'description': 'Encapsulation, inheritance, polymorphism, and dunder methods.',
                'lessons': [
                    {
                        'order': 4,
                        'chapter': 'OOP Principles',
                        'title': 'Classes, Objects, and Magic Methods',
                        'minutes': 30,
                        'video_url': 'https://www.youtube.com/watch?v=JeznW_7DlB0',
                        'video_duration': 900,
                        'content': """<h3>Object-Oriented Programming in Python</h3>
<p>Classes encapsulate state and behavior into reusable software components.</p>
<pre><code class="language-python">class Student:
    def __init__(self, name: str, gpa: float):
        self.name = name
        self.gpa = gpa

    def __repr__(self) -> str:
        return f"Student(name='{self.name}', gpa={self.gpa})"

    def is_honors(self) -> bool:
        return self.gpa >= 3.7
</code></pre>""",
                        'key_takeaways': [
                            "`self` explicitly represents the instance within class methods.",
                            "Dunder methods like `__init__`, `__str__`, and `__repr__` integrate with Python language protocols."
                        ],
                        'common_mistakes': [
                            "Forgetting `self` as the first argument in instance methods.",
                            "Accidentally sharing mutable class-level attributes across all instances."
                        ],
                        'resources': '<a href="https://realpython.com/python3-object-oriented-programming/" target="_blank" class="text-primary-accent-light">OOP in Python</a>',
                        'exercise': {
                            'title': 'Create BankAccount Class',
                            'instructions': 'Create a class `BankAccount` with `__init__(self, owner, balance=0.0)`. Implement `deposit(amount)` and `withdraw(amount)` returning True if successful or False if insufficient funds.',
                            'starter_code': "class BankAccount:\n    def __init__(self, owner: str, balance: float = 0.0):\n        self.owner = owner\n        self.balance = balance\n\n    def deposit(self, amount: float) -> float:\n        self.balance += amount\n        return self.balance\n\n    def withdraw(self, amount: float) -> bool:\n        if amount <= self.balance:\n            self.balance -= amount\n            return True\n        return False\n",
                            'expected_output': 'acc = BankAccount("Alice", 100); acc.withdraw(40) is True and acc.balance == 60',
                            'hints': 'Check amount <= self.balance before deducting.'
                        }
                    }
                ]
            }
        ],
        'assessments': [
            {
                'type': 'final_quiz',
                'title': 'Python Programming Final Course Quiz',
                'description': 'Comprehensive 20-minute multiple-choice quiz testing core Python language mechanics, collections, and OOP.',
                'duration': 20,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'Which of the following data structures is immutable in Python?',
                        'a': 'List', 'b': 'Tuple', 'c': 'Dictionary', 'd': 'Set',
                        'correct': 'B', 'topic': 'Data Structures',
                        'explanation': 'Tuples in Python are immutable sequences; once created, their elements cannot be added, removed, or reassigned.'
                    },
                    {
                        'text': 'What is the average time complexity for checking if a key exists in a Python dictionary?',
                        'a': 'O(n)', 'b': 'O(log n)', 'c': 'O(1)', 'd': 'O(n^2)',
                        'correct': 'C', 'topic': 'Complexity & Dictionaries',
                        'explanation': 'Python dictionaries use hash tables under the hood, delivering average O(1) time complexity for key lookups.'
                    },
                    {
                        'text': 'What happens if a function argument has a mutable default value (e.g., def fn(items=[]))?',
                        'a': 'A new list is allocated every function invocation',
                        'b': 'The same list object is retained and mutated across calls',
                        'c': 'Python raises a RuntimeError during compilation',
                        'd': 'The list is automatically converted to an immutable tuple',
                        'correct': 'B', 'topic': 'Functions & Scope',
                        'explanation': 'Default argument expressions in Python are evaluated once when the function definition is executed, leading to a single shared list across calls.'
                    },
                    {
                        'text': 'Which dunder method is invoked when calling len(obj) on a custom class?',
                        'a': '__size__', 'b': '__count__', 'c': '__len__', 'd': '__length__',
                        'correct': 'C', 'topic': 'OOP & Dunder Methods',
                        'explanation': 'The built-in len() function delegates to the custom object’s __len__() method.'
                    },
                    {
                        'text': 'What is the output of print([x * 2 for x in range(4) if x % 2 == 0])?',
                        'a': '[0, 2, 4, 6]', 'b': '[0, 4]', 'c': '[2, 6]', 'd': '[4, 8]',
                        'correct': 'B', 'topic': 'Comprehensions',
                        'explanation': 'range(4) produces 0, 1, 2, 3. The even values are 0 and 2. Multiplied by 2, they yield [0, 4].'
                    }
                ]
            },
            {
                'type': 'final_mock',
                'title': 'Python Technical Interview Mock Examination',
                'description': 'Simulated technical screening examination testing memory model, scoping rules, and algorithmic debugging.',
                'duration': 30,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'What is the difference between `==` and `is` in Python?',
                        'a': '`==` compares object identity, `is` compares values',
                        'b': '`==` compares values, `is` compares object memory identity',
                        'c': 'They are identical and interchangeable aliases',
                        'd': '`is` only applies to primitive numbers',
                        'correct': 'B', 'topic': 'Python Memory Model',
                        'explanation': '`==` evaluates value equality via __eq__, while `is` compares memory address identity (id(a) == id(b)).'
                    },
                    {
                        'text': 'How does Python implement garbage collection?',
                        'a': 'Pure stop-the-world mark and sweep only',
                        'b': 'Reference counting complemented by a cyclic garbage collector',
                        'c': 'Manual free() calls like C',
                        'd': 'Generational copying without reference tracking',
                        'correct': 'B', 'topic': 'Memory Management',
                        'explanation': 'CPython primarily relies on immediate reference counting, with a generational cycle detector to clean up circular references.'
                    },
                    {
                        'text': 'In Python, what is the Global Interpreter Lock (GIL)?',
                        'a': 'A mutex that prevents multiple native threads from executing Python bytecodes simultaneously',
                        'b': 'A database transaction lock used by SQLite',
                        'c': 'A security lock that encrypts compiled pyc files',
                        'd': 'A mechanism that disallows importing untrusted modules',
                        'correct': 'A', 'topic': 'CPython Internals & Concurrency',
                        'explanation': 'The GIL is a mutex in CPython that ensures thread-safe memory management by allowing only one native OS thread to run Python bytecode at a time.'
                    },
                    {
                        'text': 'What will be the result of bool([]), bool(0), bool(None)?',
                        'a': 'True, True, True',
                        'b': 'False, False, False',
                        'c': 'False, True, False',
                        'd': 'True, False, None',
                        'correct': 'B', 'topic': 'Type Casting & Truthiness',
                        'explanation': 'In Python, empty collections, zero values, and None all evaluate to False in a boolean context.'
                    },
                    {
                        'text': 'What is the return type of a Python generator function containing the `yield` keyword?',
                        'a': 'A list containing all yield results',
                        'b': 'A generator object implementing the iterator protocol',
                        'c': 'A coroutine task',
                        'd': 'A tuple containing yielded items',
                        'correct': 'B', 'topic': 'Generators & Iterators',
                        'explanation': 'Functions containing `yield` produce generator objects that compute items lazily on demand via next().'
                    }
                ]
            }
        ]
    },
    'full-stack-django-web-dev': {
        'modules': [
            {
                'order': 1,
                'title': 'Django Architecture & The MVT Pattern',
                'description': 'Understand Model-View-Template flow, URL routing, settings, and request dispatching.',
                'lessons': [
                    {
                        'order': 1,
                        'chapter': 'Architecture',
                        'title': 'Django Request Lifecycle & MVT',
                        'minutes': 20,
                        'video_url': 'https://www.youtube.com/watch?v=F5mRW0jo-U4',
                        'video_duration': 750,
                        'content': """<h3>Django MVT Architecture</h3>
<p>Django follows Model-View-Template architecture, abstracting database interactions through the ORM and HTML rendering via templates.</p>
<h4>HTTP Request Flow</h4>
<ol>
    <li>WSGI/ASGI entry point passes `request` to middleware chain.</li>
    <li>Root URLconf matches URL patterns and routes to the view function/class.</li>
    <li>View queries database models via the ORM.</li>
    <li>View renders template with context data into an `HttpResponse`.</li>
</ol>""",
                        'key_takeaways': [
                            "Views in Django act as the controller/coordinator in classic MVC terminology.",
                            "Middleware wraps every incoming request and outgoing response."
                        ],
                        'common_mistakes': [
                            "Putting heavy database logic inside templates instead of views or model managers.",
                            "Forgetting to register installed apps in `settings.INSTALLED_APPS`."
                        ],
                        'resources': '<a href="https://docs.djangoproject.com/en/4.2/" target="_blank" class="text-primary-accent-light">Django 4.2 Documentation</a>',
                        'exercise': {
                            'title': 'Configure URL Pattern',
                            'instructions': 'Write a function `format_slug_url(slug: str) -> str` that formats an endpoint string `/courses/<slug>/`.',
                            'starter_code': "def format_slug_url(slug: str) -> str:\n    # Return path string with slug\n    return ''\n",
                            'expected_output': "format_slug_url('python-basics') == '/courses/python-basics/'",
                            'hints': "Use f'/courses/{slug}/'."
                        }
                    }
                ]
            },
            {
                'order': 2,
                'title': 'Database Modeling & ORM Performance',
                'description': 'ForeignKeys, ManyToMany, indexing, select_related, and prefetch_related.',
                'lessons': [
                    {
                        'order': 2,
                        'chapter': 'Database & ORM',
                        'title': 'Relational Modeling & Query Optimization',
                        'minutes': 25,
                        'video_url': 'https://www.youtube.com/watch?v=rHux0gMZ3Eg',
                        'video_duration': 820,
                        'content': """<h3>Django ORM Performance: Preventing N+1 Queries</h3>
<p>QuerySets are lazy. Calling related foreign keys inside template loops can cause hundreds of database queries (N+1 problem).</p>
<pre><code class="language-python"># Fix N+1 queries with select_related (SQL JOIN)
enrollments = Enrollment.objects.filter(user=request.user).select_related('course', 'course__category')

# Fix ManyToMany / Reverse ForeignKey with prefetch_related (SQL IN clause)
courses = Course.objects.prefetch_related('lessons').all()
</code></pre>""",
                        'key_takeaways': [
                            "Use `select_related` for single-valued relationships (ForeignKey, OneToOne).",
                            "Use `prefetch_related` for multi-valued relationships (ManyToMany, reverse ForeignKey)."
                        ],
                        'common_mistakes': [
                            "Triggering evaluation of QuerySets prematurely by casting to list() before filtering.",
                            "Overlooking database index creation for frequently searched fields."
                        ],
                        'resources': '<a href="https://docs.djangoproject.com/en/4.2/topics/db/optimization/" target="_blank" class="text-primary-accent-light">Django Database Optimization</a>',
                        'exercise': {
                            'title': 'QuerySet Calculation',
                            'instructions': 'Write a function `calculate_pass_rate(total: int, passed: int) -> int` returning the integer percentage rounded.',
                            'starter_code': "def calculate_pass_rate(total: int, passed: int) -> int:\n    if total <= 0:\n        return 0\n    return int(round((passed / total) * 100))\n",
                            'expected_output': 'calculate_pass_rate(20, 16) == 80',
                            'hints': 'Divide passed by total, multiply by 100, round to int.'
                        }
                    }
                ]
            }
        ],
        'assessments': [
            {
                'type': 'final_quiz',
                'title': 'Django Full-Stack Final Course Quiz',
                'description': 'Test your understanding of Django ORM, authentication, CSRF security, and template rendering.',
                'duration': 20,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'Which method optimizes single-valued ForeignKey queries using an SQL INNER JOIN?',
                        'a': 'prefetch_related()', 'b': 'select_related()', 'c': 'join_related()', 'd': 'aggregate()',
                        'correct': 'B', 'topic': 'Django ORM Optimization',
                        'explanation': 'select_related follows foreign-key relationships, performing an SQL JOIN to populate related objects in a single query.'
                    },
                    {
                        'text': 'What is the purpose of the {% csrf_token %} tag in Django forms?',
                        'a': 'It encrypts database passwords',
                        'b': 'It protects against Cross-Site Request Forgery attacks',
                        'c': 'It caches form fields in browser storage',
                        'd': 'It compresses form payloads for mobile networks',
                        'correct': 'B', 'topic': 'Security',
                        'explanation': 'Django verifies a unique token to guarantee that POST submissions originated from the authentic user rather than a malicious site.'
                    },
                    {
                        'text': 'When are Django QuerySets evaluated (executed against the database)?',
                        'a': 'Immediately when defined',
                        'b': 'Only when iterated over, sliced, or evaluated by list() / len()',
                        'c': 'During project deployment',
                        'd': 'Whenever a new model instance is created',
                        'correct': 'B', 'topic': 'ORM Mechanics',
                        'explanation': 'Django QuerySets are lazy and remain unexecuted until their results are specifically iterated over or converted.'
                    },
                    {
                        'text': 'What command creates new database migration files based on changes detected in models.py?',
                        'a': 'python manage.py migrate',
                        'b': 'python manage.py makemigrations',
                        'c': 'python manage.py syncdb',
                        'd': 'python manage.py schemaupdate',
                        'correct': 'B', 'topic': 'Migrations',
                        'explanation': 'makemigrations inspects models and generates migration files; migrate executes those files against the database.'
                    },
                    {
                        'text': 'Where should sensitive API keys and database credentials be stored in production Django apps?',
                        'a': 'Directly hardcoded in settings.py',
                        'b': 'In environment variables or secret management vaults',
                        'c': 'In static/js/credentials.json',
                        'd': 'Inside SQLite schema files',
                        'correct': 'B', 'topic': 'Production Security',
                        'explanation': 'Secrets should always be decoupled from source control using environment variables (e.g., .env or platform secrets).'
                    }
                ]
            },
            {
                'type': 'final_mock',
                'title': 'Django Backend Engineer Mock Examination',
                'description': 'Simulated industry technical interview evaluating web architecture, session management, and database indexes.',
                'duration': 30,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'What is the difference between select_related and prefetch_related?',
                        'a': 'select_related uses Python loops, prefetch_related uses SQL JOINs',
                        'b': 'select_related uses SQL JOIN for 1-to-1/1-to-many; prefetch_related does separate queries with SQL IN for many-to-many',
                        'c': 'They are identical and execute identical SQL',
                        'd': 'prefetch_related only works with NoSQL databases',
                        'correct': 'B', 'topic': 'Database Querying',
                        'explanation': 'select_related creates a single SQL JOIN query, while prefetch_related performs a separate query and joins the results in Python.'
                    },
                    {
                        'text': 'How does Django manage user authentication state across HTTP requests?',
                        'a': 'By storing username and password in browser cookies',
                        'b': 'Using signed session cookies linking to server-side or cached session data',
                        'c': 'Through continuous WebSocket pings',
                        'd': 'By re-authenticating every request against database credentials',
                        'correct': 'B', 'topic': 'Authentication & Sessions',
                        'explanation': 'Django sets a secure session ID cookie in the client browser, matching it to session data on the backend.'
                    },
                    {
                        'text': 'What HTTP status code should be returned when a resource is successfully created via POST?',
                        'a': '200 OK', 'b': '201 Created', 'c': '204 No Content', 'd': '301 Moved',
                        'correct': 'B', 'topic': 'HTTP & REST APIs',
                        'explanation': 'HTTP status 201 Created signifies that the request succeeded and led to the creation of a new resource.'
                    },
                    {
                        'text': 'Why is Django’s `F()` expression useful in database updates?',
                        'a': 'It enables formatting strings in views',
                        'b': 'It allows database-level operations avoiding Python memory race conditions',
                        'c': 'It forces SQL database rollbacks',
                        'd': 'It compresses file uploads automatically',
                        'correct': 'B', 'topic': 'ORM Concurrency',
                        'explanation': '`F()` expressions let the database update a field directly (e.g. counter = counter + 1) without fetching the value to Python, preventing race conditions.'
                    },
                    {
                        'text': 'What tool does Django production deployments use to serve static files efficiently without web server config?',
                        'a': 'Gunicorn', 'b': 'WhiteNoise', 'c': 'Celery', 'd': 'Memcached',
                        'correct': 'B', 'topic': 'Production Deployment',
                        'explanation': 'WhiteNoise allows Django web apps to serve their own static files directly with caching and compression headers.'
                    }
                ]
            }
        ]
    },
    'mastering-dsa-with-python': {
        'modules': [
            {
                'order': 1,
                'title': 'Complexity Analysis & Linear Data Structures',
                'description': 'Big-O notation, arrays, linked lists, stacks, and queues.',
                'lessons': [
                    {
                        'order': 1,
                        'chapter': 'Complexity Analysis',
                        'title': 'Asymptotic Analysis & Big-O Notation',
                        'minutes': 20,
                        'video_url': 'https://www.youtube.com/watch?v=__vX2sjlpXU',
                        'video_duration': 680,
                        'content': """<h3>Asymptotic Complexity</h3>
<p>Big-O notation describes the upper bound of algorithm growth as input size n approaches infinity.</p>
<h4>Common Complexities</h4>
<ul>
    <li>O(1): Constant time (Hash map lookup)</li>
    <li>O(log n): Logarithmic (Binary search)</li>
    <li>O(n): Linear (Single loop over array)</li>
    <li>O(n log n): Linearithmic (Merge sort, Timsort)</li>
    <li>O(n^2): Quadratic (Nested loops, Bubble sort)</li>
</ul>""",
                        'key_takeaways': [
                            "Always evaluate both worst-case and average-case complexity.",
                            "Space complexity measures additional auxiliary memory required by the algorithm."
                        ],
                        'common_mistakes': [
                            "Assuming smaller constant factors beat lower asymptotic complexity at scale.",
                            "Ignoring space complexity added by recursion call stacks."
                        ],
                        'resources': '<a href="https://www.bigocheatsheet.com/" target="_blank" class="text-primary-accent-light">Big-O Cheat Sheet</a>',
                        'exercise': {
                            'title': 'Binary Search Implementation',
                            'instructions': 'Write a function `binary_search(arr: list, target: int) -> int` returning the target index or -1 if not found.',
                            'starter_code': "def binary_search(arr: list, target: int) -> int:\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n",
                            'expected_output': 'binary_search([1, 3, 5, 7, 9], 7) == 3',
                            'hints': 'Update low = mid + 1 when arr[mid] < target.'
                        }
                    }
                ]
            }
        ],
        'assessments': [
            {
                'type': 'final_quiz',
                'title': 'DSA with Python Final Course Quiz',
                'description': 'Evaluate your knowledge of data structures, search algorithms, sorting, and graph traversals.',
                'duration': 20,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'What is the time complexity of searching in a balanced Binary Search Tree (AVL / Red-Black)?',
                        'a': 'O(1)', 'b': 'O(n)', 'c': 'O(log n)', 'd': 'O(n^2)',
                        'correct': 'C', 'topic': 'Trees',
                        'explanation': 'In a balanced BST, tree height is bounded by O(log n), making search, insertion, and deletion O(log n).'
                    },
                    {
                        'text': 'Which data structure follows the First-In, First-Out (FIFO) principle?',
                        'a': 'Stack', 'b': 'Queue', 'c': 'Max-Heap', 'd': 'Hash Map',
                        'correct': 'B', 'topic': 'Queues',
                        'explanation': 'Queues process elements in the order they arrive (FIFO), whereas Stacks are LIFO.'
                    },
                    {
                        'text': 'What is the worst-case time complexity of QuickSort?',
                        'a': 'O(n log n)', 'b': 'O(n)', 'c': 'O(n^2)', 'd': 'O(log n)',
                        'correct': 'C', 'topic': 'Sorting',
                        'explanation': 'When the pivot selected is consistently the minimum or maximum element (e.g. on sorted input with naive pivot), QuickSort degrades to O(n^2).'
                    },
                    {
                        'text': 'Which graph traversal algorithm uses a Queue to explore neighboring nodes level-by-level?',
                        'a': 'Depth-First Search (DFS)', 'b': 'Breadth-First Search (BFS)', 'c': 'Dijkstra’s Algorithm with Heap', 'd': 'Kruskal’s Algorithm',
                        'correct': 'B', 'topic': 'Graphs',
                        'explanation': 'BFS systematically explores all neighbor nodes at current depth before moving deeper using a FIFO queue.'
                    },
                    {
                        'text': 'What is the space complexity of Depth-First Search on a tree of height h?',
                        'a': 'O(1)', 'b': 'O(h)', 'c': 'O(2^h)', 'd': 'O(n^2)',
                        'correct': 'B', 'topic': 'Recursion & Trees',
                        'explanation': 'DFS stores active ancestor frames on the recursion stack, bounded by the maximum tree height h.'
                    }
                ]
            },
            {
                'type': 'final_mock',
                'title': 'DSA Coding Interview Mock Examination',
                'description': 'Industry mock exam with real algorithmic scenarios and optimization challenges.',
                'duration': 30,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'Given an unsorted array of n integers, what is the best achievable time complexity to find two numbers that sum to a target k?',
                        'a': 'O(n^2) time, O(1) space', 'b': 'O(n) time, O(n) space using a hash set', 'c': 'O(n log n) time, O(n^2) space', 'd': 'O(log n) time',
                        'correct': 'B', 'topic': 'Hash Tables & Two Sum',
                        'explanation': 'Storing complements in a hash set achieves optimal O(n) linear time with O(n) space.'
                    },
                    {
                        'text': 'How does Python’s heapq module implement priority queues?',
                        'a': 'Max-heap by default', 'b': 'Min-heap where arr[0] is always the smallest element', 'c': 'Doubly-linked list', 'd': 'Binary Search Tree',
                        'correct': 'B', 'topic': 'Heaps',
                        'explanation': 'Python’s heapq module implements a binary min-heap where the smallest element is at index 0.'
                    },
                    {
                        'text': 'Which algorithm finds the shortest path from a single source node in a weighted graph with non-negative edge weights?',
                        'a': 'Prim’s Algorithm', 'b': 'Dijkstra’s Algorithm', 'c': 'Floyd-Warshall Algorithm', 'd': 'Topological Sort',
                        'correct': 'B', 'topic': 'Shortest Path',
                        'explanation': 'Dijkstra’s algorithm finds shortest paths in O((V + E) log V) time using a min-priority queue for non-negative weights.'
                    },
                    {
                        'text': 'What is memoization in dynamic programming?',
                        'a': 'Compiling recursive code into bytecode',
                        'b': 'Caching overlapping subproblem results to avoid redundant recomputations',
                        'c': 'Converting depth-first search into breadth-first search',
                        'd': 'Freeing unused pointers in linked lists',
                        'correct': 'B', 'topic': 'Dynamic Programming',
                        'explanation': 'Memoization is top-down caching of expensive function call results based on identical arguments.'
                    },
                    {
                        'text': 'In a cyclic graph with n vertices and m edges, what time complexity does Kahn’s algorithm or DFS topological sort achieve?',
                        'a': 'O(V + E)', 'b': 'O(V^2)', 'c': 'It detects the cycle because DAGs cannot contain cycles', 'd': 'O(log V)',
                        'correct': 'C', 'topic': 'Graph Cycles',
                        'explanation': 'Topological ordering is only defined for Directed Acyclic Graphs (DAGs); Kahn’s algorithm detects cycles when remaining in-degrees cannot reach zero.'
                    }
                ]
            }
        ]
    },
    'relational-databases-sql-postgresql': {
        'modules': [
            {
                'order': 1,
                'title': 'Relational Modeling & Core SQL',
                'description': 'Schemas, foreign keys, normalization, joins, and aggregates.',
                'lessons': [
                    {
                        'order': 1,
                        'chapter': 'SQL Foundations',
                        'title': 'ACID Transactions & PostgreSQL Schema Design',
                        'minutes': 20,
                        'video_url': 'https://www.youtube.com/watch?v=qw--VYLpxG4',
                        'video_duration': 700,
                        'content': """<h3>PostgreSQL & ACID Guarantees</h3>
<p>Relational databases ensure data integrity via ACID properties: Atomicity, Consistency, Isolation, and Durability.</p>
<h4>B-Tree Indexing</h4>
<pre><code class="language-sql">-- Creating high-performance composite indexes
CREATE INDEX idx_enrollment_user_course ON courses_enrollment(user_id, course_id);
</code></pre>""",
                        'key_takeaways': [
                            "Foreign keys enforce referential integrity at the database engine level.",
                            "Indexes speed up reads but add overhead to INSERT and UPDATE operations."
                        ],
                        'common_mistakes': [
                            "Storing unindexed foreign keys causing full table scans during JOIN operations.",
                            "Ignoring NULL comparisons (e.g. `col = NULL` instead of `col IS NULL`)."
                        ],
                        'resources': '<a href="https://www.postgresql.org/docs/" target="_blank" class="text-primary-accent-light">PostgreSQL Official Manual</a>',
                        'exercise': {
                            'title': 'Write SQL Query',
                            'instructions': 'Write a function `build_select_query(table: str, limit: int) -> str` that produces `SELECT * FROM <table> LIMIT <limit>;`.',
                            'starter_code': "def build_select_query(table: str, limit: int) -> str:\n    return f'SELECT * FROM {table} LIMIT {limit};'\n",
                            'expected_output': "build_select_query('students', 10) == 'SELECT * FROM students LIMIT 10;'",
                            'hints': 'Use string formatting.'
                        }
                    }
                ]
            }
        ],
        'assessments': [
            {
                'type': 'final_quiz',
                'title': 'PostgreSQL & SQL Final Course Quiz',
                'description': 'Test your mastery of SQL joins, indexing, ACID transactions, and normalization.',
                'duration': 20,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'What does the "I" in ACID stand for?',
                        'a': 'Indexing', 'b': 'Isolation', 'c': 'Integrity', 'd': 'Iteration',
                        'correct': 'B', 'topic': 'ACID Transactions',
                        'explanation': 'Isolation ensures concurrent transactions execute without interfering with one another.'
                    },
                    {
                        'text': 'Which SQL JOIN returns all rows from the left table and matched rows from the right table?',
                        'a': 'INNER JOIN', 'b': 'LEFT OUTER JOIN', 'c': 'FULL OUTER JOIN', 'd': 'CROSS JOIN',
                        'correct': 'B', 'topic': 'SQL Joins',
                        'explanation': 'A LEFT JOIN returns all records from the left table, and the matched records from the right table (with NULLs for unmatched).'
                    },
                    {
                        'text': 'What is the standard index type created by PostgreSQL for primary keys and unique constraints?',
                        'a': 'Hash Index', 'b': 'B-Tree Index', 'c': 'GIN Index', 'd': 'GiST Index',
                        'correct': 'B', 'topic': 'PostgreSQL Indexes',
                        'explanation': 'PostgreSQL defaults to B-Tree indexes for primary keys and standard columns, supporting equality and range queries.'
                    },
                    {
                        'text': 'How do you check for NULL values in SQL?',
                        'a': 'WHERE col == NULL', 'b': 'WHERE col = NULL', 'c': 'WHERE col IS NULL', 'd': 'WHERE col.null()',
                        'correct': 'C', 'topic': 'SQL Syntax',
                        'explanation': 'In standard SQL, comparisons with NULL using = yield UNKNOWN; `IS NULL` is the required syntax.'
                    },
                    {
                        'text': 'What normal form eliminates transitive dependencies between non-key attributes?',
                        'a': '1NF', 'b': '2NF', 'c': '3NF', 'd': 'BCNF',
                        'correct': 'C', 'topic': 'Database Normalization',
                        'explanation': 'Third Normal Form (3NF) requires 2NF and mandates that no non-prime attribute is transitively dependent on the primary key.'
                    }
                ]
            },
            {
                'type': 'final_mock',
                'title': 'Database Administrator & SQL Mock Examination',
                'description': 'Scenario-based exam covering execution plans, lock contention, and query optimization.',
                'duration': 30,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'What command analyzes and prints the execution plan of a PostgreSQL query?',
                        'a': 'DESCRIBE SELECT ...', 'b': 'EXPLAIN ANALYZE SELECT ...', 'c': 'SHOW PLAN SELECT ...', 'd': 'PROFILE SELECT ...',
                        'correct': 'B', 'topic': 'Query Planning',
                        'explanation': 'EXPLAIN ANALYZE executes the statement and displays actual run times and planning metrics.'
                    },
                    {
                        'text': 'What is the risk of executing SELECT * without WHERE on a table with 50 million rows?',
                        'a': 'SQL syntax error', 'b': 'Excessive memory exhaustion, full table scan, and network congestion', 'c': 'Database index corruption', 'd': 'Loss of ACID durability',
                        'correct': 'B', 'topic': 'Query Optimization',
                        'explanation': 'Full table scans on unconstrained large tables deplete server buffer memory and saturate network throughput.'
                    },
                    {
                        'text': 'What transaction isolation level prevents dirty reads, non-repeatable reads, and phantom reads?',
                        'a': 'Read Uncommitted', 'b': 'Read Committed', 'c': 'Repeatable Read', 'd': 'Serializable',
                        'correct': 'D', 'topic': 'Transactions',
                        'explanation': 'Serializable is the highest isolation level, guaranteeing execution equivalent to completely serial execution.'
                    },
                    {
                        'text': 'Which PostgreSQL feature allows indexing semi-structured JSON documents efficiently?',
                        'a': 'JSONB data type with GIN index', 'b': 'VARCHAR with B-Tree', 'c': 'TEXT with Hash index', 'd': 'XML column',
                        'correct': 'A', 'topic': 'JSONB & Indexing',
                        'explanation': 'JSONB stores parsed binary JSON, which can be indexed using Generalized Inverted Indexes (GIN) for high-speed key/value lookups.'
                    },
                    {
                        'text': 'What does connection pooling (e.g. pgBouncer or Supabase pooler) accomplish?',
                        'a': 'Compresses table backups', 'b': 'Reuses database server worker processes to avoid connection handshake overhead', 'c': 'Converts SQL to GraphQL', 'd': 'Prevents SQL injection',
                        'correct': 'B', 'topic': 'Database Infrastructure',
                        'explanation': 'Connection pooling reuses established database connections, preventing memory exhaustion when handling thousands of concurrent requests.'
                    }
                ]
            }
        ]
    },
    'applied-ai-machine-learning': {
        'modules': [
            {
                'order': 1,
                'title': 'Machine Learning Fundamentals & Neural Networks',
                'description': 'Supervised learning, loss functions, gradient descent, and neural architectures.',
                'lessons': [
                    {
                        'order': 1,
                        'chapter': 'AI Foundations',
                        'title': 'Supervised Learning & Gradient Descent',
                        'minutes': 25,
                        'video_url': 'https://www.youtube.com/watch?v=aircAruvnKk',
                        'video_duration': 850,
                        'content': """<h3>Supervised Learning Core Concepts</h3>
<p>In supervised learning, models learn mapping functions from labeled input-output pairs (X -> y) by minimizing empirical risk.</p>
<h4>Gradient Descent Update Rule</h4>
<pre><code class="language-python"># Weight update step
# w = w - learning_rate * dL_dw
</code></pre>""",
                        'key_takeaways': [
                            "Gradient descent updates model weights in the direction opposite the gradient of the loss.",
                            "Overfitting occurs when a model learns noise in training data and fails to generalize."
                        ],
                        'common_mistakes': [
                            "Training on test data (data leakage).",
                            "Selecting an excessively large learning rate leading to divergence."
                        ],
                        'resources': '<a href="https://scikit-learn.org/stable/" target="_blank" class="text-primary-accent-light">Scikit-Learn Documentation</a>',
                        'exercise': {
                            'title': 'Mean Squared Error Calculation',
                            'instructions': 'Write a function `mse(y_true: list, y_pred: list) -> float` returning the mean squared error rounded to 2 decimals.',
                            'starter_code': "def mse(y_true: list, y_pred: list) -> float:\n    n = len(y_true)\n    if n == 0:\n        return 0.0\n    return round(sum((y_true[i] - y_pred[i]) ** 2 for i in range(n)) / n, 2)\n",
                            'expected_output': 'mse([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 0.0',
                            'hints': 'Compute squared differences, sum them, divide by n.'
                        }
                    }
                ]
            }
        ],
        'assessments': [
            {
                'type': 'final_quiz',
                'title': 'Applied AI & ML Final Course Quiz',
                'description': 'Conceptual test on model training, regularization, metrics, and transformers.',
                'duration': 20,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'Which metric is most appropriate for evaluating a highly imbalanced binary classification dataset?',
                        'a': 'Accuracy', 'b': 'F1-Score / Precision-Recall AUC', 'c': 'Mean Squared Error', 'd': 'R-squared',
                        'correct': 'B', 'topic': 'Evaluation Metrics',
                        'explanation': 'Accuracy is misleading on imbalanced data (e.g. 99% negative class); F1-Score balances precision and recall.'
                    },
                    {
                        'text': 'What technique adds an L2 penalty on weight magnitudes to prevent overfitting?',
                        'a': 'Ridge Regularization (Weight Decay)', 'b': 'Lasso Regularization (L1)', 'c': 'Batch Normalization', 'd': 'Gradient Clipping',
                        'correct': 'A', 'topic': 'Regularization',
                        'explanation': 'L2 regularization adds the sum of squared weights to the loss function, shrinking weights smoothly.'
                    },
                    {
                        'text': 'What is the attention mechanism in Transformer models?',
                        'a': 'A technique that discards unused tokens',
                        'b': 'A mathematical mapping allowing tokens to dynamically attend to all other tokens based on Query, Key, and Value matrices',
                        'c': 'A convolutional kernel for 1D text',
                        'd': 'A recurrent loop identical to LSTMs',
                        'correct': 'B', 'topic': 'Transformers & NLP',
                        'explanation': 'Transformers compute Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V across tokens.'
                    },
                    {
                        'text': 'What is data leakage in machine learning?',
                        'a': 'A database security breach exposing user records',
                        'b': 'Information from outside the training dataset being inadvertently used to create the model',
                        'c': 'Compressing model weights for mobile phones',
                        'd': 'Gradient values disappearing to zero',
                        'correct': 'B', 'topic': 'ML Engineering',
                        'explanation': 'Data leakage occurs when test or future target information leaks into the training pipeline, yielding artificially high training metrics.'
                    },
                    {
                        'text': 'What activation function outputs values in the range (0, 1), often used for binary probability outputs?',
                        'a': 'ReLU', 'b': 'Sigmoid', 'c': 'Linear', 'd': 'LeakyReLU',
                        'correct': 'B', 'topic': 'Neural Networks',
                        'explanation': 'The Sigmoid function maps real numbers into the range (0, 1), representing probabilities.'
                    }
                ]
            },
            {
                'type': 'final_mock',
                'title': 'Machine Learning Engineer Mock Examination',
                'description': 'Industry screening for ML practitioners on pipelines, fine-tuning, and inference latency.',
                'duration': 30,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'What causes the vanishing gradient problem in deep neural networks?',
                        'a': 'Excessively high learning rate',
                        'b': 'Repeated multiplication of small derivatives through many layers using saturating activations like sigmoid or tanh',
                        'c': 'Overfitting on small datasets',
                        'd': 'Using ReLU activations exclusively',
                        'correct': 'B', 'topic': 'Deep Learning',
                        'explanation': 'Saturating activation functions have small derivatives; chained backpropagation through many layers drives gradients toward zero.'
                    },
                    {
                        'text': 'What is the primary benefit of LoRA (Low-Rank Adaptation) in LLM fine-tuning?',
                        'a': 'It trains all model parameters from scratch',
                        'b': 'It freezes pre-trained weights and injects trainable rank-decomposition matrices, drastically reducing GPU memory requirements',
                        'c': 'It converts LLMs into decision trees',
                        'd': 'It eliminates the need for prompt tokens',
                        'correct': 'B', 'topic': 'LLM Fine-Tuning',
                        'explanation': 'LoRA decomposes weight updates into two smaller low-rank matrices, saving over 80% of VRAM during fine-tuning.'
                    },
                    {
                        'text': 'What is the role of temperature in generative AI sampling?',
                        'a': 'It cools the GPU hardware',
                        'b': 'It scales logits prior to softmax; lower temperature produces deterministic outputs, higher produces creative diversity',
                        'c': 'It sets the maximum token length',
                        'd': 'It controls network bandwidth',
                        'correct': 'B', 'topic': 'Generative AI',
                        'explanation': 'Temperature controls the flatness of the softmax probability distribution over vocabulary logits.'
                    },
                    {
                        'text': 'In Retrieval-Augmented Generation (RAG), what is used to retrieve relevant context chunks?',
                        'a': 'Random sampling', 'b': 'Dense vector embeddings and cosine similarity search', 'c': 'Regex pattern matching only', 'd': 'JSON file parsing',
                        'correct': 'B', 'topic': 'RAG Architectures',
                        'explanation': 'RAG embeds documents into high-dimensional vector spaces and retrieves semantically similar chunks via cosine or dot-product distance.'
                    },
                    {
                        'text': 'What is quantization in machine learning inference (e.g. INT8 or INT4)?',
                        'a': 'Converting code to quantum computing circuits',
                        'b': 'Reducing the precision of weights from FP32/FP16 to lower bit-widths to decrease memory usage and latency',
                        'c': 'Pruning all attention heads',
                        'd': 'Removing bias terms from linear layers',
                        'correct': 'B', 'topic': 'Model Optimization',
                        'explanation': 'Quantization maps floating-point parameters to lower bit integers, cutting memory footprint with minimal accuracy loss.'
                    }
                ]
            }
        ]
    },
    'data-science-with-python-pandas': {
        'modules': [
            {
                'order': 1,
                'title': 'Data Wrangling & Statistical Analysis with Pandas',
                'description': 'DataFrames, Series, filtering, missing value imputation, and groupby aggregations.',
                'lessons': [
                    {
                        'order': 1,
                        'chapter': 'Data Analysis',
                        'title': 'Pandas DataFrames & Aggregations',
                        'minutes': 20,
                        'video_url': 'https://www.youtube.com/watch?v=vmEHCJofslg',
                        'video_duration': 720,
                        'content': """<h3>Pandas DataFrames for Analytics</h3>
<p>Pandas provides vectorized, columnar data processing built on top of NumPy arrays.</p>
<h4>Split-Apply-Combine with groupby</h4>
<pre><code class="language-python">import pandas as pd
# Grouping and aggregating data
df.groupby('category')['revenue'].agg(['mean', 'sum', 'count'])
</code></pre>""",
                        'key_takeaways': [
                            "Vectorized operations in Pandas and NumPy outperform explicit Python for-loops by orders of magnitude.",
                            "Use `.loc[]` for label-based indexing and `.iloc[]` for integer position-based indexing."
                        ],
                        'common_mistakes': [
                            "Chained assignment warnings (e.g. `df[df['a'] > 1]['b'] = 2`) instead of `.loc`.",
                            "Imputing missing values using the entire dataset before train/test splitting."
                        ],
                        'resources': '<a href="https://pandas.pydata.org/docs/" target="_blank" class="text-primary-accent-light">Pandas Documentation</a>',
                        'exercise': {
                            'title': 'Calculate Mean Value',
                            'instructions': 'Write a function `calculate_mean(values: list) -> float` returning the arithmetic mean rounded to 2 decimal places.',
                            'starter_code': "def calculate_mean(values: list) -> float:\n    if not values:\n        return 0.0\n    return round(sum(values) / len(values), 2)\n",
                            'expected_output': 'calculate_mean([10, 20, 30, 40]) == 25.0',
                            'hints': 'Sum values and divide by len(values).'
                        }
                    }
                ]
            }
        ],
        'assessments': [
            {
                'type': 'final_quiz',
                'title': 'Data Science & Analytics Final Course Quiz',
                'description': 'Assess your knowledge of Pandas, statistics, data cleaning, and visualization.',
                'duration': 20,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'What is the primary difference between Pandas loc and iloc?',
                        'a': 'loc is label-based, iloc is integer index-based',
                        'b': 'loc is integer-based, iloc is label-based',
                        'c': 'loc is for columns, iloc is for rows only',
                        'd': 'They are identical',
                        'correct': 'A', 'topic': 'Pandas Indexing',
                        'explanation': 'loc selects rows and columns by labels/names, while iloc selects strictly by zero-based integer index positions.'
                    },
                    {
                        'text': 'What does df.dropna() do in Pandas?',
                        'a': 'Drops columns with duplicate names',
                        'b': 'Removes rows (or columns) containing missing / NaN values',
                        'c': 'Deletes the database table',
                        'd': 'Replaces nulls with zeros',
                        'correct': 'B', 'topic': 'Data Cleaning',
                        'explanation': 'dropna() filters out rows or columns containing missing values (NaN/None).'
                    },
                    {
                        'text': 'Which statistical measure indicates the spread of data points around their mean?',
                        'a': 'Median', 'b': 'Standard Deviation', 'c': 'Mode', 'd': 'Skewness',
                        'correct': 'B', 'topic': 'Statistics',
                        'explanation': 'Standard deviation quantifies the average dispersion of data points relative to the mean.'
                    },
                    {
                        'text': 'What is the purpose of the groupby operation in Pandas?',
                        'a': 'To sort rows alphabetically',
                        'b': 'To split data into groups, apply functions, and combine aggregate metrics',
                        'c': 'To connect to a SQL database',
                        'd': 'To generate random samples',
                        'correct': 'B', 'topic': 'Aggregation',
                        'explanation': 'groupby implements the Split-Apply-Combine paradigm for calculating group-level summary statistics.'
                    },
                    {
                        'text': 'What chart type is best suited to display the distribution and median of a continuous numerical variable?',
                        'a': 'Pie Chart', 'b': 'Box Plot / Histogram', 'c': 'Scatter Plot', 'd': 'Network Graph',
                        'correct': 'B', 'topic': 'Visualization',
                        'explanation': 'Box plots and histograms display quartiles, medians, spread, and outlier distributions effectively.'
                    }
                ]
            },
            {
                'type': 'final_mock',
                'title': 'Data Scientist Technical Mock Examination',
                'description': 'Simulated case study exam covering hypothesis testing, feature engineering, and statistical inference.',
                'duration': 30,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'In hypothesis testing, what does a p-value less than alpha (e.g. 0.05) indicate?',
                        'a': 'The null hypothesis is proven unconditionally true',
                        'b': 'Reject the null hypothesis in favor of the alternative hypothesis as the observed result is statistically significant',
                        'c': 'The experiment has zero statistical power',
                        'd': 'The dataset must be discarded',
                        'correct': 'B', 'topic': 'Hypothesis Testing',
                        'explanation': 'A p-value < 0.05 indicates the observed data is sufficiently unlikely under the null hypothesis to warrant rejecting it.'
                    },
                    {
                        'text': 'What is multicollinearity in linear regression?',
                        'a': 'Missing target values',
                        'b': 'High inter-correlation among two or more independent predictor features',
                        'c': 'Non-linear decision boundaries',
                        'd': 'Outliers in the test split',
                        'correct': 'B', 'topic': 'Statistical Modeling',
                        'explanation': 'Multicollinearity occurs when independent variables are highly correlated, inflating variance in estimated coefficients.'
                    },
                    {
                        'text': 'What technique transforms skewed positive numerical distributions into approximately normal distributions?',
                        'a': 'One-hot encoding', 'b': 'Log transform or Box-Cox transformation', 'c': 'Min-Max scaling between 0 and 1', 'd': 'Principal Component Analysis',
                        'correct': 'B', 'topic': 'Feature Engineering',
                        'explanation': 'Logarithmic or power transformations compress right-skewed heavy tails, stabilizing variance.'
                    },
                    {
                        'text': 'What is the Central Limit Theorem?',
                        'a': 'All datasets are normally distributed',
                        'b': 'The sampling distribution of the sample mean approaches a normal distribution as sample size increases, regardless of population distribution',
                        'c': 'Large datasets require GPU clusters',
                        'd': 'Correlation implies causation for sample sizes > 1000',
                        'correct': 'B', 'topic': 'Probability & Statistics',
                        'explanation': 'The CLT guarantees that sample means are normally distributed given a sufficiently large sample size.'
                    },
                    {
                        'text': 'Which metric measures the linear relationship between two continuous variables between -1 and +1?',
                        'a': 'Gini Impurity', 'b': 'Pearson Correlation Coefficient', 'c': 'Euclidean Distance', 'd': 'Silhouette Score',
                        'correct': 'B', 'topic': 'Bivariate Analysis',
                        'explanation': 'Pearson r quantifies the direction and strength of linear relationships between -1 (perfect inverse) and +1 (perfect positive).'
                    }
                ]
            }
        ]
    },
    'cs-fundamentals-os-networks': {
        'modules': [
            {
                'order': 1,
                'title': 'Operating Systems & Concurrency',
                'description': 'Process scheduling, virtual memory, threads, synchronization primitives, and deadlocks.',
                'lessons': [
                    {
                        'order': 1,
                        'chapter': 'Operating Systems',
                        'title': 'Processes, Threads, and Concurrency',
                        'minutes': 20,
                        'video_url': 'https://www.youtube.com/watch?v=26QPDBe-NB8',
                        'video_duration': 780,
                        'content': """<h3>Processes vs Threads</h3>
<p>A process is an instance of an executing program with isolated virtual address space. Threads are execution contexts within a process that share heap memory.</p>
<h4>Concurrency Primitives</h4>
<ul>
    <li><strong>Mutex:</strong> Mutual exclusion lock guaranteeing single-thread execution in critical sections.</li>
    <li><strong>Semaphore:</strong> Counting primitive controlling access to finite pooled resources.</li>
</ul>""",
                        'key_takeaways': [
                            "Processes provide memory isolation; threads share memory and require explicit synchronization.",
                            "Deadlocks require four Coffman conditions: Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait."
                        ],
                        'common_mistakes': [
                            "Assuming multi-threaded operations are thread-safe without atomic primitives or mutexes.",
                            "Failing to release locks in exception paths, causing deadlocks."
                        ],
                        'resources': '<a href="https://pages.cs.wisc.edu/~remzi/OSTEP/" target="_blank" class="text-primary-accent-light">Operating Systems: Three Easy Pieces</a>',
                        'exercise': {
                            'title': 'Check Coffman Conditions',
                            'instructions': 'Write a function `is_deadlock_possible(mutual_exclusion: bool, hold_and_wait: bool, no_preemption: bool, circular_wait: bool) -> bool` returning True only if all 4 Coffman conditions hold.',
                            'starter_code': "def is_deadlock_possible(me: bool, hw: bool, np: bool, cw: bool) -> bool:\n    return me and hw and np and cw\n",
                            'expected_output': 'is_deadlock_possible(True, True, True, True) is True and is_deadlock_possible(True, False, True, True) is False',
                            'hints': 'All 4 conditions must be True.'
                        }
                    }
                ]
            }
        ],
        'assessments': [
            {
                'type': 'final_quiz',
                'title': 'Computer Science Fundamentals Final Course Quiz',
                'description': 'Evaluate core concepts across OS processes, virtual memory, TCP/IP networking, and system architecture.',
                'duration': 20,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'What is the primary difference between a process and a thread?',
                        'a': 'Threads have isolated memory spaces; processes share heap memory',
                        'b': 'Processes have isolated virtual address spaces; threads share the address space of their parent process',
                        'c': 'Processes are managed by hardware; threads by compilers',
                        'd': 'Threads cannot run on multi-core CPUs',
                        'correct': 'B', 'topic': 'OS Processes',
                        'explanation': 'Processes enjoy private address spaces for security and fault isolation; threads share address space within the same process.'
                    },
                    {
                        'text': 'Which layer of the OSI model handles end-to-end reliable transmission using TCP?',
                        'a': 'Physical Layer', 'b': 'Network Layer', 'c': 'Transport Layer', 'd': 'Application Layer',
                        'correct': 'C', 'topic': 'Networking & OSI',
                        'explanation': 'The Transport Layer (Layer 4) handles end-to-end communication, flow control, and reliability via TCP.'
                    },
                    {
                        'text': 'What mechanism does the CPU use to translate virtual memory addresses to physical RAM addresses?',
                        'a': 'Memory Management Unit (MMU) with Page Tables',
                        'b': 'Software loop in Python',
                        'c': 'BIOS ROM',
                        'd': 'Direct Memory Access controller',
                        'correct': 'A', 'topic': 'Virtual Memory',
                        'explanation': 'The hardware MMU translates virtual page addresses into physical frames via Page Tables and the TLB.'
                    },
                    {
                        'text': 'What are the three packets exchanged during a standard TCP handshake?',
                        'a': 'PING, PONG, ACK', 'b': 'SYN, SYN-ACK, ACK', 'c': 'GET, POST, ACK', 'd': 'HELLO, READY, GO',
                        'correct': 'B', 'topic': 'TCP Protocol',
                        'explanation': 'TCP establishes connections via a 3-way handshake: SYN from client, SYN-ACK from server, ACK from client.'
                    },
                    {
                        'text': 'What is a race condition in concurrent software?',
                        'a': 'When a thread executes faster than the clock rate',
                        'b': 'When software behavior depends unpredictably on the non-deterministic timing or interleaving of concurrent execution threads',
                        'c': 'A benchmark competition between algorithms',
                        'd': 'When memory runs out of heap space',
                        'correct': 'B', 'topic': 'Concurrency',
                        'explanation': 'Race conditions occur when multiple threads access shared mutable state without proper synchronization.'
                    }
                ]
            },
            {
                'type': 'final_mock',
                'title': 'Systems Engineer & CS Fundamentals Mock Examination',
                'description': 'Advanced systems examination on scheduling algorithms, page faults, and socket programming.',
                'duration': 30,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'What is a page fault in virtual memory systems?',
                        'a': 'A hardware crash requiring reboot',
                        'b': 'An interrupt raised when an executing program accesses a memory page not currently mapped into physical RAM',
                        'c': 'A syntax error in source code',
                        'd': 'A corrupt hard drive block',
                        'correct': 'B', 'topic': 'Virtual Memory',
                        'explanation': 'A page fault triggers the OS kernel to swap or load the missing page from disk into a physical RAM frame.'
                    },
                    {
                        'text': 'Which of the following is NOT one of the four Coffman conditions required for deadlocks?',
                        'a': 'Mutual Exclusion', 'b': 'Hold and Wait', 'c': 'Preemption Allowed', 'd': 'Circular Wait',
                        'correct': 'C', 'topic': 'Deadlocks',
                        'explanation': 'The condition is No Preemption; if preemption is allowed, deadlocks cannot occur.'
                    },
                    {
                        'text': 'Why is UDP preferred over TCP for live video streaming and competitive online gaming?',
                        'a': 'UDP encrypts packets automatically',
                        'b': 'UDP has lower latency by omitting connection establishment, retransmissions, and head-of-line blocking',
                        'c': 'UDP guarantees 100% packet delivery without loss',
                        'd': 'UDP runs at the physical hardware layer',
                        'correct': 'B', 'topic': 'Networking',
                        'explanation': 'UDP sacrifices guaranteed delivery and ordering to achieve minimum latency without head-of-line retransmission stalls.'
                    },
                    {
                        'text': 'What happens during a context switch in an operating system?',
                        'a': 'The CPU powers off and on',
                        'b': 'The OS saves the state (registers, program counter) of the running process and restores the state of the scheduled process',
                        'c': 'The compiler optimizes machine code',
                        'd': 'Virtual memory is deleted',
                        'correct': 'B', 'topic': 'OS Scheduling',
                        'explanation': 'A context switch saves CPU register context and loads another process context, introducing small CPU overhead.'
                    },
                    {
                        'text': 'What does the Translation Lookaside Buffer (TLB) cache?',
                        'a': 'Web browser cookies',
                        'b': 'Recent virtual-to-physical address translations to accelerate memory access',
                        'c': 'Compiled Python bytecode',
                        'd': 'DNS domain name lookups',
                        'correct': 'B', 'topic': 'Hardware Architecture',
                        'explanation': 'The TLB is a high-speed hardware cache on the CPU that stores recent virtual-to-physical address page translations.'
                    }
                ]
            }
        ]
    },
    'tech-career-accelerator': {
        'modules': [
            {
                'order': 1,
                'title': 'High-Impact Technical Portfolios & ATS Resumes',
                'description': 'Showcasing full-stack engineering depth, ATS formatting, and recruiter outreach.',
                'lessons': [
                    {
                        'order': 1,
                        'chapter': 'Portfolio & Resume',
                        'title': 'Building Standout Portfolios & Crafting ATS Resumes',
                        'minutes': 20,
                        'video_url': 'https://www.youtube.com/watch?v=ttWkL4nU2qY',
                        'video_duration': 650,
                        'content': """<h3>Engineering Portfolios & ATS Resume Strategies</h3>
<p>Tech recruiters and hiring managers review resumes in seconds. Your resume must clearly articulate impact, technologies, and measurable results.</p>
<h4>The Google XYZ Formula</h4>
<p>Accomplished [X], as measured by [Y], by doing [Z].</p>
<pre><code class="language-markdown">Built high-concurrency microservices platform, handling 20,000 req/sec with < 50ms latency, utilizing Django, PostgreSQL, and Redis caching.
</code></pre>""",
                        'key_takeaways': [
                            "Format resumes using clean single-column layouts for maximum ATS compatibility.",
                            "Focus on measurable technical impact and architectural decisions, not just duty lists."
                        ],
                        'common_mistakes': [
                            "Using graphical skill bars (e.g. '80% Python') which confuse parsing algorithms.",
                            "Linking to broken or unfinished project repositories."
                        ],
                        'resources': '<a href="https://careercup.com" target="_blank" class="text-primary-accent-light">Tech Interview Insights</a>',
                        'exercise': {
                            'title': 'Validate Resume Bullet Format',
                            'instructions': 'Write a function `validate_bullet(bullet: str) -> bool` returning True if the bullet string is non-empty, starts with a capital letter, and ends with a period.',
                            'starter_code': "def validate_bullet(bullet: str) -> bool:\n    if not bullet:\n        return False\n    return bullet[0].isupper() and bullet.endswith('.')\n",
                            'expected_output': "validate_bullet('Engineered real-time analytics pipeline.') is True",
                            'hints': 'Check bullet[0].isupper() and bullet.endswith(".").'
                        }
                    }
                ]
            }
        ],
        'assessments': [
            {
                'type': 'final_quiz',
                'title': 'Career Accelerator Final Course Quiz',
                'description': 'Assess your readiness for tech applications, portfolio showcasing, and resume screening.',
                'duration': 20,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'What does "ATS" stand for in tech recruiting?',
                        'a': 'Automatic Test System', 'b': 'Applicant Tracking System', 'c': 'Application Transfer Socket', 'd': 'Algorithm Timing Suite',
                        'correct': 'B', 'topic': 'Recruiting Systems',
                        'explanation': 'Applicant Tracking Systems are software used by employers to parse, filter, and rank job applications.'
                    },
                    {
                        'text': 'Which resume bullet point follows the recommended Google XYZ formula best?',
                        'a': 'Worked on Python backend code',
                        'b': 'Responsible for database tables',
                        'c': 'Reduced database query latency by 45%, as measured by Datadog APM, by introducing composite PostgreSQL indexes and connection pooling',
                        'd': 'Helped team with various sprint tasks',
                        'correct': 'C', 'topic': 'Resume Crafting',
                        'explanation': 'Option C specifies the exact accomplishment [X], metric [Y], and technical solution [Z].'
                    },
                    {
                        'text': 'What should be prioritized at the top of a developer project showcase in a portfolio?',
                        'a': 'A 10-page essay',
                        'b': 'Live demo URL, GitHub repository link, technology tags, and key architectural highlights',
                        'c': 'A blurry screenshot',
                        'd': 'Personal contact phone number only',
                        'correct': 'B', 'topic': 'Portfolio Architecture',
                        'explanation': 'Hiring managers need quick access to the live application, clean source code, and key technical highlights.'
                    },
                    {
                        'text': 'Why should multi-column table layouts and complex graphic icons be avoided on ATS resumes?',
                        'a': 'They make file sizes too large',
                        'b': 'Many ATS parsers read columns horizontally across lines, scrambling text sections and work history',
                        'c': 'PDF documents cannot contain tables',
                        'd': 'It is illegal under hiring regulations',
                        'correct': 'B', 'topic': 'ATS Optimization',
                        'explanation': 'Complex columns and graphics frequently cause ATS parsing engines to misinterpret section order.'
                    },
                    {
                        'text': 'What is the STAR framework for behavioral interviews?',
                        'a': 'Speed, Timing, Action, Reward',
                        'b': 'Situation, Task, Action, Result',
                        'c': 'Software, Technology, Architecture, Release',
                        'd': 'Syntax, Types, Algorithms, Recursion',
                        'correct': 'B', 'topic': 'Interview Preparation',
                        'explanation': 'STAR structures behavioral responses into Situation, Task, Action, and measurable Result.'
                    }
                ]
            },
            {
                'type': 'final_mock',
                'title': 'Technical Behavioral & Interview Mock Examination',
                'description': 'Simulated hiring committee interview on conflict resolution, system trade-offs, and technical communication.',
                'duration': 30,
                'pass_pct': 70,
                'questions': [
                    {
                        'text': 'When asked "Tell me about a time you made a technical mistake", what is the hiring team assessing?',
                        'a': 'Whether you have ever written a syntax error',
                        'b': 'Self-awareness, accountability, root-cause analysis, and how you improved systems or processes as a result',
                        'c': 'If you can blame coworkers convincingly',
                        'd': 'How quickly you hide errors from production logs',
                        'correct': 'B', 'topic': 'Behavioral Interviews',
                        'explanation': 'Interviewers look for mature ownership, blameless post-mortem reflection, and systemic preventative measures.'
                    },
                    {
                        'text': 'In a system design interview, what should you do first after receiving a prompt like "Design Twitter"?',
                        'a': 'Immediately write database schemas',
                        'b': 'Clarify scope, functional and non-functional requirements, traffic scale, and read-to-write ratios',
                        'c': 'Choose a specific cloud vendor',
                        'd': 'Draw UI wireframes',
                        'correct': 'B', 'topic': 'System Design',
                        'explanation': 'Always clarify requirements, operational scale, latency constraints, and feature scope before proposing architectures.'
                    },
                    {
                        'text': 'How should you discuss technical trade-offs between technologies (e.g. SQL vs NoSQL)?',
                        'a': 'State that NoSQL is always superior because it is newer',
                        'b': 'Evaluate against specific access patterns, consistency requirements (ACID vs eventual), query flexibility, and scaling needs',
                        'c': 'Refuse to compare them',
                        'd': 'Choose the technology with the most stars on GitHub',
                        'correct': 'B', 'topic': 'Architectural Evaluation',
                        'explanation': 'Senior engineers evaluate architectural trade-offs based on data access patterns, consistency, and operational requirements.'
                    },
                    {
                        'text': 'What is the most effective approach when you get stuck during a live coding interview?',
                        'a': 'Stay completely silent for 15 minutes',
                        'b': 'Communicate your thought process out loud, identify assumptions, test with a small input example, and discuss possible paths with the interviewer',
                        'c': 'Give up and terminate the call',
                        'd': 'Blame the programming language',
                        'correct': 'B', 'topic': 'Live Coding Strategy',
                        'explanation': 'Interviewers evaluate problem-solving clarity and collaboration; thinking aloud allows them to provide subtle guidance.'
                    },
                    {
                        'text': 'What should you prepare to ask the interviewers at the end of an engineering interview?',
                        'a': '"How much will you pay me?"',
                        'b': 'Insightful questions about engineering culture, deployment pipelines, team challenges, and code review practices',
                        'c': '"Can I skip writing tests?"',
                        'd': 'Say "I have no questions"',
                        'correct': 'B', 'topic': 'Reverse Interviewing',
                        'explanation': 'Thoughtful questions demonstrate genuine professional curiosity, engineering standards, and career engagement.'
                    }
                ]
            }
        ]
    }
}
