"""
Curriculum Builder Script for SkillSphere.
Generates comprehensive 16-lesson curriculum hierarchies across 4 modules for all 12 courses:
- Module 1 (Lessons 1-4): Level 1 - Foundations
- Module 2 (Lessons 5-8): Level 2 - Core Skills
- Module 3 (Lessons 9-12): Level 3 - Intermediate Mastery
- Module 4 (Lessons 13-14): Level 4 - Advanced & Performance
- Module 4 (Lessons 15-16): Level 5 - Practical Deliverable
- Level 6: Final Assessments (Final Quiz & Final Mock Exam)
"""

import json

COURSES_METADATA = [
    {
        'slug': 'python-programming-from-scratch',
        'title': 'Python Programming from Scratch to OOP',
        'category': 'programming',
        'topic_prefix': 'Python',
        'lang': 'python',
        'modules': [
            {
                'order': 1,
                'title': 'Module 1: Foundations & Control Structures',
                'description': 'Master variable binding, scalar types, operators, branching logic, and iterative control flow.',
                'lessons': [
                    ('Variables, Types, and Expressions', 'Syntax & Types', 15, 'Understanding variable binding, scalar types (int, float, bool, str), dynamic typing, and operator precedence in Python 3.'),
                    ('Control Flow: If-Else & Loops', 'Control Flow', 25, 'Master deterministic conditional branching with if-elif-else, boolean truthiness, short-circuit logic, and bounded loops.'),
                    ('Functions, Scope & Lexical Closures', 'Functions & Scope', 20, 'Define reusable functions, parameter contracts (*args, **kwargs), LEGB scope resolution, and lexical closures.'),
                    ('Modules, Packages & Namespaces', 'Modular Python', 20, 'Understand CPython import resolution, sys.path, __init__.py, relative vs absolute imports, and virtual environment isolation.')
                ]
            },
            {
                'order': 2,
                'title': 'Module 2: Core Data Structures & Functional Patterns',
                'description': 'Master built-in collections, high-performance comprehensions, and functional programming constructs.',
                'lessons': [
                    ('Lists, Tuples & Sequence Unpacking', 'Linear Sequences', 20, 'Deep dive into dynamic arrays (list), immutable sequences (tuple), slicing semantics, and extended iterable unpacking.'),
                    ('Dictionaries, Hash Maps & Set Operations', 'Hash Collections', 25, 'Master hash table collision resolution, dict comprehension, key mutability invariants, and set mathematical operations.'),
                    ('Comprehensions & Generator Expressions', 'Iterables & Memory', 20, 'Optimize memory consumption using list, dict, and set comprehensions alongside lazy generator expressions.'),
                    ('First-Class Functions, Lambdas & Decorators', 'Functional Patterns', 25, 'Treat functions as first-class citizens: higher-order functions (map, filter), lambda expressions, and parameterized decorators.')
                ]
            },
            {
                'order': 3,
                'title': 'Module 3: Object-Oriented Programming & Design Patterns',
                'description': 'Master classes, inheritance, dunder protocols, polymorphism, and solid architectural principles.',
                'lessons': [
                    ('Classes, Instances & Attribute Binding', 'OOP Foundations', 25, 'Understand the class keyword, self parameter, class vs instance attributes, and method resolution order (MRO).'),
                    ('Inheritance, Polymorphism & Abstract Base Classes', 'Class Hierarchies', 25, 'Implement single and multiple inheritance, super() cooperative method calls, and abc.ABC interface contracts.'),
                    ('Dunder Protocols & Operator Overloading', 'Python Data Model', 25, 'Master the Python data model protocols: __repr__, __str__, __eq__, __len__, __getitem__, and arithmetic overloading.'),
                    ('Properties, Descriptors & Metaclasses', 'Advanced Metaprogramming', 30, 'Enforce encapsulation using @property getters/setters, reusable descriptor protocols (__get__, __set__), and class factories.')
                ]
            },
            {
                'order': 4,
                'title': 'Module 4: Advanced Engineering & Production Deliverable',
                'description': 'Error handling, context managers, async I/O, profiling, and an end-to-end production deliverable.',
                'lessons': [
                    ('Defensive Exception Handling & Context Managers', 'Resilience', 25, 'Master custom exception hierarchies, try-except-else-finally blocks, and context managers using with statements and contextlib.'),
                    ('Concurrency Foundations: Threading & Asyncio', 'Concurrency', 30, 'Understand the Global Interpreter Lock (GIL), preemptive threading vs cooperative multitasking with asyncio and coroutines.'),
                    ('Production Profiling, Benchmarking & Packaging', 'Performance', 30, 'Profile memory and CPU bottlenecks with cProfile and tracemalloc, write pyproject.toml packaging configurations.'),
                    ('Capstone Project: Enterprise CLI Task Automation Engine', 'Practical Deliverable', 45, 'Synthesize all concepts to build a production-grade CLI task manager with JSON persistence, dataclasses, and automated unit tests.')
                ]
            }
        ]
    },
    {
        'slug': 'full-stack-django-web-dev',
        'title': 'Full Stack Web Development with Django & Python',
        'category': 'web-development',
        'topic_prefix': 'Django',
        'lang': 'python',
        'modules': [
            {
                'order': 1,
                'title': 'Module 1: Django Architecture & Request Lifecycle',
                'description': 'Master MVC/MVT architecture, WSGI/ASGI servers, URL dispatching, and view controllers.',
                'lessons': [
                    ('Django Architecture & Project Structure', 'Core Architecture', 20, 'Understand Django MVT paradigm, settings configuration, secret management, and WSGI/ASGI entry points.'),
                    ('URL Routing, Path Converters & View Controllers', 'Routing & Views', 20, 'Design deterministic URL hierarchies using path(), re_path(), custom path converters, and HTTP request/response lifecycles.'),
                    ('Django Template Engine (DTL) & Inheritance', 'Templates & UI', 20, 'Construct maintainable frontend layouts using template inheritance ({% extends %}, {% block %}), filters, and custom tags.'),
                    ('Static Files Management & CDN Deployment', 'Assets & Delivery', 20, 'Configure STATIC_URL, STATIC_ROOT, WhiteNoise middleware, and cloud storage buckets for high-performance static delivery.')
                ]
            },
            {
                'order': 2,
                'title': 'Module 2: Django ORM, Models & Database Migrations',
                'description': 'Relational data modeling, migrations engine, query optimization, and relationships.',
                'lessons': [
                    ('Model Definitions, Fields & Schema Constraints', 'Data Modeling', 25, 'Define models with typed fields, default values, validators, UniqueConstraint, and database indexes.'),
                    ('Relationships: ForeignKey, ManyToMany & OneToOne', 'Relational Schemas', 25, 'Model complex domain relationships with related_name, on_delete cascades, and intermediary through tables.'),
                    ('QuerySets, Lookups & Lazy Evaluation', 'QuerySet Mechanics', 25, 'Master lazy QuerySet evaluation, chaining filters, Q objects for complex boolean queries, and F expressions for atomic database updates.'),
                    ('Migrations Engine & Safe Schema Evolution', 'Database Migrations', 25, 'Understand makemigrations, migrate, dependency graphs, data migrations, and zero-downtime database deployments.')
                ]
            },
            {
                'order': 3,
                'title': 'Module 3: Forms, Authentication & Security Engineering',
                'description': 'User auth, session management, CSRF protection, and form validation.',
                'lessons': [
                    ('Django Forms & ModelForms Validation', 'Form Handling', 25, 'Construct secure forms, handle CSRF tokens, implement clean_<field>() and clean() cross-field validation rules.'),
                    ('Authentication, Sessions & Permission Groups', 'Identity & Access', 25, 'Manage user registration, password hashing (PBKDF2/Argon2), login sessions, permission decorators, and user groups.'),
                    ('Middleware Pipeline & Custom Request Interception', 'Middleware', 25, 'Deconstruct Django middleware execution order, process_request/process_response hooks, and custom request auditing.'),
                    ('Django Security Hardening: XSS, CSRF & SQLi', 'Web Security', 30, 'Harden production apps against Cross-Site Scripting, SQL Injection, Clickjacking, and configure strict Security Headers.')
                ]
            },
            {
                'order': 4,
                'title': 'Module 4: Django REST Framework & Production Delivery',
                'description': 'REST APIs, serializers, JWT authentication, caching, and container deployment.',
                'lessons': [
                    ('Django REST Framework: Serializers & ViewSets', 'REST APIs', 30, 'Build RESTful JSON APIs using ModelSerializers, APIView, ViewSets, and DefaultRouter.'),
                    ('API Authentication: JWT & Token Security', 'API Security', 25, 'Secure API endpoints with JSON Web Tokens (simplejwt), access/refresh token rotation, and permission classes.'),
                    ('ORM Optimization: select_related & prefetch_related', 'Performance', 30, 'Eliminate N+1 database queries using select_related (SQL JOIN) and prefetch_related (batch querying), profiling with django-debug-toolbar.'),
                    ('Capstone Project: Multi-Tenant SaaS Portal Deployment', 'Practical Deliverable', 45, 'Deploy a full-stack Django SaaS application with PostgreSQL, Redis caching, Gunicorn, Docker, and CI/CD automation.')
                ]
            }
        ]
    },
    {
        'slug': 'mastering-dsa-with-python',
        'title': 'Mastering Data Structures & Algorithms with Python',
        'category': 'dsa',
        'topic_prefix': 'DSA',
        'lang': 'python',
        'modules': [
            {
                'order': 1,
                'title': 'Module 1: Complexity Analysis & Linear Data Structures',
                'description': 'Asymptotic analysis, arrays, linked lists, stacks, and queues.',
                'lessons': [
                    ('Big-O Notation & Asymptotic Complexity', 'Complexity Analysis', 20, 'Analyze time and space complexity: Big-O, Big-Omega, Big-Theta, master theorem, and amortized runtime analysis.'),
                    ('Dynamic Arrays & String Manipulation', 'Arrays & Strings', 20, 'Internal mechanics of dynamic arrays, memory reallocation, two-pointer techniques, and prefix sum optimizations.'),
                    ('Singly & Doubly Linked Lists', 'Linked Lists', 25, 'Implement linked lists from scratch, pointer manipulation, fast and slow pointers, and cycle detection (Floyd\'s algorithm).'),
                    ('Stacks, Queues & Monotonic Deques', 'Linear Structures', 20, 'LIFO and FIFO data structures, stack-based bracket validation, and monotonic queues for sliding window maximums.')
                ]
            },
            {
                'order': 2,
                'title': 'Module 2: Sorting, Searching & Hash Tables',
                'description': 'Divide-and-conquer algorithms, binary search variations, and hash collision mechanics.',
                'lessons': [
                    ('Recursion & Divide-and-Conquer Paradigms', 'Recursion', 25, 'Recursive call stack mechanics, base cases, recurrence relations, and divide-and-conquer strategy.'),
                    ('Binary Search & Search Space Reduction', 'Binary Search', 25, 'Master classic binary search, finding rotated array pivots, bisect module, and binary search on solution spaces.'),
                    ('Sorting Algorithms: Merge Sort & Quick Sort', 'Sorting Algorithms', 30, 'Implement Merge Sort (stable O(N log N)) and Quick Sort (in-place partitioning), analyzing worst-case pivots.'),
                    ('Hash Tables & Collision Resolution Strategies', 'Hash Tables', 25, 'Hash function design, load factors, separate chaining vs open addressing (linear probing), and Robin Hood hashing.')
                ]
            },
            {
                'order': 3,
                'title': 'Module 3: Non-Linear Structures: Trees & Graphs',
                'description': 'Binary trees, BSTs, heaps, graph traversals, and shortest path algorithms.',
                'lessons': [
                    ('Binary Trees & Depth-First Traversals', 'Trees', 25, 'Binary tree representations, recursive and iterative preorder, inorder, and postorder traversals, and maximum depth calculations.'),
                    ('Binary Search Trees (BST) & Balanced Trees', 'Search Trees', 30, 'BST invariant properties, search, insertion, deletion, and introduction to self-balancing AVL and Red-Black trees.'),
                    ('Heaps & Priority Queues', 'Priority Queues', 25, 'Binary heap array representation, heapify-up and heapify-down operations, and using Python\'s heapq for top-K problems.'),
                    ('Graph Representations & Traversals (BFS & DFS)', 'Graph Theory', 30, 'Adjacency list vs matrix representations, Breadth-First Search (shortest path in unweighted graphs), and Depth-First Search with topological sorting.')
                ]
            },
            {
                'order': 4,
                'title': 'Module 4: Advanced Algorithms & Technical Interview Mastery',
                'description': 'Shortest path, greedy algorithms, dynamic programming, and interview problem sets.',
                'lessons': [
                    ('Shortest Paths: Dijkstra\'s Algorithm & Bellman-Ford', 'Network Algorithms', 30, 'Compute single-source shortest paths in weighted graphs using Dijkstra with min-heaps and Bellman-Ford for negative weights.'),
                    ('Greedy Algorithms & Minimum Spanning Trees', 'Greedy Paradigms', 25, 'Greedy choice property, interval scheduling, Huffman coding, and Kruskal\'s/Prim\'s algorithms with Union-Find (Disjoint Set).'),
                    ('Dynamic Programming: Memoization & Tabulation', 'Dynamic Programming', 35, 'Optimal substructure and overlapping subproblems: 1D DP (Fibonacci, Climbing Stairs) and 2D DP (0/1 Knapsack, Longest Common Subsequence).'),
                    ('Capstone Problem Set: Top FAANG Interview Challenges', 'Interview Mastery', 45, 'Solve complex multi-concept challenges combining trees, graphs, heaps, and dynamic programming under strict time constraints.')
                ]
            }
        ]
    },
    {
        'slug': 'relational-databases-sql-postgresql',
        'title': 'Relational Databases & SQL Mastery with PostgreSQL',
        'category': 'database-management',
        'topic_prefix': 'PostgreSQL',
        'lang': 'sql',
        'modules': [
            {
                'order': 1,
                'title': 'Module 1: Relational Modeling & Core SQL Syntax',
                'description': 'Schema normalization, DDL, DML, filtering, and aggregate operations.',
                'lessons': [
                    ('Relational Schema Design & Normalization (1NF to 3NF)', 'Schema Design', 20, 'Understand entities, attributes, primary keys, foreign keys, functional dependencies, and normalizing schemas up to 3NF.'),
                    ('DDL Statements: Tables, Constraints & Datatypes', 'Data Definition', 20, 'Create, alter, and drop tables with strict constraints: NOT NULL, CHECK, UNIQUE, and PostgreSQL datatypes (UUID, JSONB, TIMESTAMP).'),
                    ('DML Queries: SELECT, WHERE, ORDER BY & LIMIT', 'Basic Queries', 20, 'Execute data retrieval queries with logical filtering, pattern matching (LIKE, ILIKE), sorting, and pagination.'),
                    ('Aggregate Functions & GROUP BY Aggregations', 'Aggregations', 20, 'Summarize data using COUNT, SUM, AVG, MIN, MAX, GROUP BY grouping, and HAVING post-aggregation filters.')
                ]
            },
            {
                'order': 2,
                'title': 'Module 2: Relational Joins & Subquery Architecture',
                'description': 'Join algorithms, correlated subqueries, set operations, and views.',
                'lessons': [
                    ('Mastering Relational JOINs: INNER, LEFT, RIGHT & FULL', 'Relational Joins', 25, 'Combine tables across relationships: INNER JOIN, LEFT OUTER JOIN, FULL OUTER JOIN, and self-joins for hierarchical models.'),
                    ('Subqueries, EXISTS & Correlated Queries', 'Subqueries', 25, 'Write scalar subqueries, IN/NOT IN subqueries, correlated subqueries, and compare performance against JOINs.'),
                    ('Set Operations: UNION, INTERSECT & EXCEPT', 'Set Theory', 20, 'Perform relational set operations across compatible query outputs, evaluating duplicate retention (UNION vs UNION ALL).'),
                    ('Database Views & Materialized Views', 'Views & Caching', 25, 'Encapsulate complex query logic in standard views and accelerate analytical queries using REFRESH MATERIALIZED VIEW.')
                ]
            },
            {
                'order': 3,
                'title': 'Module 3: Advanced SQL: Window Functions & Transactions',
                'description': 'Analytical window functions, CTEs, transactions, ACID, and isolation levels.',
                'lessons': [
                    ('Window Functions: OVER, PARTITION BY & RANK', 'Analytical SQL', 30, 'Perform analytical computations without collapsing rows: ROW_NUMBER(), RANK(), DENSE_RANK(), LAG(), LEAD(), and running totals.'),
                    ('Common Table Expressions (CTEs) & Recursive SQL', 'CTEs', 25, 'Write modular SQL using WITH clauses and traverse organizational charts or graph structures with RECURSIVE CTEs.'),
                    ('ACID Transactions & PostgreSQL Isolation Levels', 'Transactions', 30, 'Master Atomicity, Consistency, Isolation, and Durability. Compare Read Committed, Repeatable Read, and Serializable isolation.'),
                    ('PostgreSQL Concurrency: Row Locks & Deadlocks', 'Concurrency', 25, 'Understand SELECT FOR UPDATE pessimistic locking, optimistic locking with version columns, and debugging transaction deadlocks.')
                ]
            },
            {
                'order': 4,
                'title': 'Module 4: Performance Tuning & Production Administration',
                'description': 'Indexing strategies, query execution plans, vacuuming, and replication.',
                'lessons': [
                    ('Indexing Strategies: B-Tree, Hash, GIN & GiST', 'Indexing', 30, 'Design optimal index structures: B-Tree indexes for ranges, GIN indexes for JSONB and full-text search, and partial/composite indexes.'),
                    ('Query Profiling: EXPLAIN ANALYZE & Cost Estimates', 'Query Optimization', 30, 'Deconstruct execution plans: Sequential Scans vs Index Scans, Hash Joins vs Nested Loops, and optimizing high-cost query nodes.'),
                    ('PostgreSQL MVCC Architecture & VACUUM Maintenance', 'Engine Internals', 25, 'Understand Multiversion Concurrency Control, xmin/xmax tuple headers, table bloat, and configuring autovacuum for high-throughput tables.'),
                    ('Capstone Project: Enterprise Database Schema & Migration Suite', 'Practical Deliverable', 45, 'Design and optimize an enterprise e-commerce PostgreSQL schema with partitioning, JSONB catalogs, stored procedures, and migration tests.')
                ]
            }
        ]
    },
    {
        'slug': 'applied-ai-machine-learning',
        'title': 'Applied AI & Machine Learning Systems',
        'category': 'artificial-intelligence',
        'topic_prefix': 'Machine Learning',
        'lang': 'python',
        'modules': [
            {
                'order': 1,
                'title': 'Module 1: Machine Learning Foundations & Math',
                'description': 'Linear algebra, calculus foundations, supervised vs unsupervised paradigms, and regression.',
                'lessons': [
                    ('Machine Learning Paradigms & Workflow', 'ML Foundations', 20, 'Understand supervised, unsupervised, and reinforcement learning paradigms, feature representations, and the ML lifecycle.'),
                    ('Linear Algebra & Matrix Operations for AI', 'Math Foundations', 25, 'Master vectors, matrices, dot products, matrix multiplications, eigenvalues, and NumPy vectorization.'),
                    ('Linear Regression & Ordinary Least Squares', 'Regression', 25, 'Formulate linear regression mathematically, derive ordinary least squares (OLS), and compute MSE loss.'),
                    ('Gradient Descent & Optimization Algorithms', 'Optimization', 25, 'Understand batch gradient descent, stochastic gradient descent (SGD), learning rates, momentum, and Adam optimization.')
                ]
            },
            {
                'order': 2,
                'title': 'Module 2: Supervised Learning & Classification',
                'description': 'Logistic regression, decision trees, support vector machines, and ensemble methods.',
                'lessons': [
                    ('Logistic Regression & Binary Classification', 'Classification', 25, 'Model probability with the sigmoid activation function, binary cross-entropy loss, and decision boundary thresholds.'),
                    ('Decision Trees & Information Gain Metrics', 'Tree Models', 25, 'Construct decision trees using recursive partitioning, Shannon entropy, Gini impurity, and pruning to prevent overfitting.'),
                    ('Random Forests & Ensemble Bagging', 'Ensemble Learning', 25, 'Combine multiple decision trees using bootstrap aggregating (bagging), random feature subsampling, and out-of-bag validation.'),
                    ('Gradient Boosted Trees: XGBoost & LightGBM', 'Boosting', 30, 'Understand sequential error correction via gradient boosting, residual fitting, and hyperparameters in modern gradient boosted trees.')
                ]
            },
            {
                'order': 3,
                'title': 'Module 3: Deep Learning & Neural Networks',
                'description': 'Perceptrons, backpropagation, convolutional networks, and regularizers.',
                'lessons': [
                    ('Perceptrons & Multi-Layer Neural Networks', 'Neural Networks', 30, 'Understand artificial neurons, forward propagation, activation functions (ReLU, Sigmoid, Tanh, Softmax), and universal approximation.'),
                    ('The Backpropagation Algorithm & Chain Rule', 'Backpropagation', 30, 'Derive backpropagation using multivariable chain rule calculus to compute analytical gradients across network layers.'),
                    ('Overfitting Mitigation: Dropout & Batch Normalization', 'Regularization', 25, 'Prevent co-adaptation using inverted dropout, stabilize internal covariate shift with batch normalization, and L1/L2 weight decay.'),
                    ('Convolutional Neural Networks (CNN) for Vision', 'Computer Vision', 30, 'Understand convolution filters, kernel strides, padding modes, max-pooling operations, and feature hierarchy in computer vision.')
                ]
            },
            {
                'order': 4,
                'title': 'Module 4: Modern AI, LLMs & Production Deployment',
                'description': 'Transformers, attention mechanisms, embeddings, and model serving.',
                'lessons': [
                    ('The Transformer Architecture & Self-Attention', 'Transformers', 35, 'Deconstruct scaled dot-product attention, multi-head attention projections, positional encodings, and encoder-decoder topologies.'),
                    ('Vector Embeddings & Semantic Search Pipelines', 'Embeddings', 25, 'Generate dense vector embeddings with language models, compute cosine similarity, and query vector databases (pgvector/Pinecone).'),
                    ('Large Language Model Orchestration & RAG Systems', 'LLM Engineering', 30, 'Design Retrieval-Augmented Generation (RAG) pipelines, manage context windows, and implement hallucination mitigation guardrails.'),
                    ('Capstone Project: End-to-End Production AI Microservice', 'Practical Deliverable', 45, 'Train, serialize (ONNX), containerize, and deploy a real-time machine learning prediction API with FastAPI, Docker, and monitoring.')
                ]
            }
        ]
    },
    {
        'slug': 'data-science-with-python-pandas',
        'title': 'Data Science with Python, Pandas & EDA',
        'category': 'data-science',
        'topic_prefix': 'Data Science',
        'lang': 'python',
        'modules': [
            {
                'order': 1,
                'title': 'Module 1: High-Performance Numerical Computing with NumPy',
                'description': 'N-dimensional arrays, vectorization, broadcasting, and numerical slicing.',
                'lessons': [
                    ('NumPy Arrays, Shapes & Memory Layouts', 'NumPy Foundations', 20, 'Understand ndarray memory strides, contiguous memory buffers, C vs Fortran order, and dtype memory allocations.'),
                    ('Array Indexing, Slicing & Boolean Masking', 'Array Operations', 20, 'Perform multidimensional slicing, fancy indexing, and boolean mask filtering for vector operations.'),
                    ('Broadcasting Rules & Mathematical Operations', 'Vectorization', 25, 'Master NumPy broadcasting semantics across incompatible shapes, universal functions (ufuncs), and vector math.'),
                    ('Statistical Reductions & Linear Algebra Routines', 'Numerical Stats', 20, 'Compute statistical summaries across axes (mean, std, median) and execute matrix factorizations using np.linalg.')
                ]
            },
            {
                'order': 2,
                'title': 'Module 2: Data Manipulation & Wrangling with Pandas',
                'description': 'Series, DataFrames, indexing, filtering, merging, and reshaping.',
                'lessons': [
                    ('Pandas Series & DataFrame Architecture', 'Pandas Core', 20, 'Understand Series and DataFrame structures, explicit index alignment, loc[] label-based vs iloc[] integer-based indexing.'),
                    ('Data Cleaning: Missing Values, Types & Outliers', 'Data Cleaning', 25, 'Detect null values (isna), implement imputation strategies (median/mode), cast data types, and identify IQR outliers.'),
                    ('Filtering, Sorting & Conditional Transformations', 'Data Wrangling', 20, 'Query data with boolean filters, df.query(), sort_values(), and apply vectorized lambda transformations with apply() and map().'),
                    ('Merging, Joining & Concatenating Datasets', 'Dataset Operations', 25, 'Combine heterogeneous datasets using pd.merge() (inner, left, right, outer joins), pd.concat(), and index alignment.')
                ]
            },
            {
                'order': 3,
                'title': 'Module 3: Aggregations, Time Series & Visualization',
                'description': 'Split-apply-combine, pivot tables, temporal data, and visual storytelling.',
                'lessons': [
                    ('Groupby Mechanics & Split-Apply-Combine', 'Groupby & Aggs', 25, 'Master df.groupby(), multi-level aggregation dictionaries, transform() for group-level normalization, and custom aggregators.'),
                    ('Reshaping Data: Pivot Tables, Melt & Stacking', 'Data Reshaping', 25, 'Reshape data between wide and long formats using pivot_table(), melt(), stack(), unstack(), and crosstab().'),
                    ('Time Series Analysis & Resampling Techniques', 'Time Series', 30, 'Parse DatetimeIndex, handle time zones, calculate rolling window statistics, and downsample/upsample with resample().'),
                    ('Exploratory Visualization with Matplotlib & Seaborn', 'Data Visualization', 25, 'Construct publication-quality statistical charts: histograms, KDE plots, box plots, scatter plots, and correlation heatmaps.')
                ]
            },
            {
                'order': 4,
                'title': 'Module 4: Statistical Inference & Practical Deliverable',
                'description': 'Hypothesis testing, probability distributions, feature engineering, and analytics capstone.',
                'lessons': [
                    ('Probability Distributions & Central Limit Theorem', 'Probability', 25, 'Understand Normal, Binomial, and Poisson distributions, standard error, z-scores, and the Central Limit Theorem.'),
                    ('Hypothesis Testing: T-Tests, Chi-Square & ANOVA', 'Hypothesis Testing', 30, 'Formulate null/alternative hypotheses, compute p-values with SciPy, run two-sample t-tests, Chi-square tests, and one-way ANOVA.'),
                    ('Feature Engineering: Encoding, Scaling & Interaction Terms', 'Feature Prep', 30, 'Prepare datasets for modeling: one-hot encoding, target encoding, standard vs min-max scaling, and polynomial features.'),
                    ('Capstone Project: Comprehensive Enterprise Analytics Case Study', 'Practical Deliverable', 45, 'Execute an end-to-end exploratory data analysis on a messy multi-million row business dataset with automated reporting and statistical verification.')
                ]
            }
        ]
    },
    {
        'slug': 'cs-fundamentals-os-networks',
        'title': 'Computer Science Fundamentals: OS, Concurrency & Networks',
        'category': 'cs-fundamentals',
        'topic_prefix': 'Computer Science',
        'lang': 'c',
        'modules': [
            {
                'order': 1,
                'title': 'Module 1: Computer Architecture & Assembly Foundations',
                'description': 'Von Neumann architecture, CPU registers, instruction cycles, and binary representation.',
                'lessons': [
                    ('Von Neumann Architecture & The Instruction Cycle', 'Hardware Architecture', 20, 'Understand CPU registers (PC, SP, IR), ALU, data/address buses, cache hierarchy (L1/L2/L3), and the Fetch-Decode-Execute cycle.'),
                    ('Binary Arithmetic, Two\'s Complement & Bitwise Logic', 'Binary Systems', 20, 'Master binary, hexadecimal, signed integer two\'s complement representation, bitwise operators, and bit masking.'),
                    ('Memory Hierarchy: Registers, Cache, RAM & Storage', 'Memory Hierarchy', 20, 'Analyze access latencies across registers, SRAM cache, DRAM main memory, and SSD storage, understanding locality of reference.'),
                    ('x86-64 Assembly Basics & Calling Conventions', 'Assembly & Machine Code', 25, 'Read basic x86-64 assembly instructions (mov, add, cmp, jmp), CPU flags, and System V AMD64 function calling conventions.')
                ]
            },
            {
                'order': 2,
                'title': 'Module 2: Operating Systems: Processes & Virtual Memory',
                'description': 'Processes, threads, CPU scheduling, and page translation.',
                'lessons': [
                    ('Process Lifecycle, States & Context Switching', 'Process Management', 25, 'Understand process control blocks (PCB), process state transitions, context switching mechanics, and fork()/exec() system calls.'),
                    ('Threads, Multi-Threading & Concurrency Models', 'Threading', 25, 'Compare user-level vs kernel-level threads, POSIX pthreads, thread pools, and shared-memory concurrency risks.'),
                    ('CPU Scheduling Algorithms: FCFS, Round Robin & Priority', 'CPU Scheduling', 25, 'Evaluate scheduling algorithms: First-Come First-Served, Shortest Job First, Round Robin time-slicing, and multi-level feedback queues.'),
                    ('Virtual Memory, Paging & Translation Lookaside Buffers (TLB)', 'Memory Management', 30, 'Deconstruct virtual address spaces, page tables, page faults, demand paging, and hardware TLB cache translation.')
                ]
            },
            {
                'order': 3,
                'title': 'Module 3: Concurrency Synchronization & File Systems',
                'description': 'Race conditions, mutexes, semaphores, deadlocks, and file storage.',
                'lessons': [
                    ('Race Conditions, Mutex Locks & Critical Sections', 'Synchronization', 25, 'Identify data races in shared memory, implement mutual exclusion with mutexes, and understand test-and-set atomic CPU instructions.'),
                    ('Semaphores, Condition Variables & Producer-Consumer', 'Coordination', 25, 'Implement counting and binary semaphores, condition variables, and solve the classic bounded-buffer producer-consumer problem.'),
                    ('Deadlocks: Conditions, Prevention & Banker\'s Algorithm', 'Deadlock Theory', 25, 'Analyze Coffman\'s four deadlock conditions, deadlock prevention strategies, resource allocation graphs, and Banker\'s algorithm.'),
                    ('File System Architecture: Inodes, Directories & Journaling', 'Storage Systems', 25, 'Understand Unix file systems: inode structures, hard links vs symbolic links, file descriptors, and write-ahead journaling for crash recovery.')
                ]
            },
            {
                'order': 4,
                'title': 'Module 4: Computer Networking & Distributed Systems',
                'description': 'OSI model, TCP/IP, sockets, DNS, and distributed fundamentals.',
                'lessons': [
                    ('The OSI Model & TCP/IP Protocol Stack', 'Networking Models', 25, 'Deconstruct protocol layers: Physical, Data Link, Network (IP), Transport (TCP/UDP), and Application (HTTP/DNS).'),
                    ('TCP Mechanics: 3-Way Handshake, Flow Control & Congestion', 'Transport Layer', 30, 'Understand TCP reliable transmission: SYN/ACK connection establishment, sliding window flow control, and slow-start congestion control.'),
                    ('Network Sockets & POSIX Client-Server Programming', 'Socket Programming', 30, 'Implement low-level TCP network sockets in C/Python: socket(), bind(), listen(), accept(), and non-blocking I/O multiplexing with select/epoll.'),
                    ('Capstone Project: Concurrent Multi-Threaded HTTP Web Server', 'Practical Deliverable', 45, 'Build a high-performance HTTP/1.1 web server from raw POSIX sockets supporting concurrent client requests, static routing, and thread pooling.')
                ]
            }
        ]
    },
    {
        'slug': 'tech-career-accelerator',
        'title': 'Tech Career Accelerator, Resumes & Interview Engineering',
        'category': 'career-development',
        'topic_prefix': 'Career',
        'lang': 'python',
        'modules': [
            {
                'order': 1,
                'title': 'Module 1: ATS Resume Engineering & Personal Branding',
                'description': 'Applicant tracking systems, impact-driven bullet points, and portfolio branding.',
                'lessons': [
                    ('Applicant Tracking Systems (ATS) & Resume Parsing', 'Resume Architecture', 20, 'Understand how modern ATS parsers extract work experience, keywords, formatting pitfalls, and single-column layout requirements.'),
                    ('Crafting High-Impact STAR Resume Bullet Points', 'Bullet Point Mastery', 20, 'Structure engineering bullet points using the Google XYZ formula: "Accomplished [X] as measured by [Y] by doing [Z]".'),
                    ('LinkedIn Optimization & Developer Visibility', 'Online Presence', 20, 'Optimize LinkedIn headline, summary, featured projects, and cultivate organic recruiter reach out strategies.'),
                    ('GitHub Profile Architecture & README Storytelling', 'Portfolio Foundations', 20, 'Transform your GitHub profile with pinned repositories, automated stats widgets, and comprehensive architectural READMEs.')
                ]
            },
            {
                'order': 2,
                'title': 'Module 2: Production Portfolio Projects That Get Interviews',
                'description': 'Project selection, full-stack architecture, deployment, and testing showcases.',
                'lessons': [
                    ('Selecting Portfolio Projects Recruiters Care About', 'Project Strategy', 20, 'Differentiate between tutorial clones and production-grade software: solving real problems, multi-service architecture, and test coverage.'),
                    ('Full-Stack Project Documentation & Architecture Diagrams', 'Technical Writing', 25, 'Create system architecture diagrams (Mermaid/C4 model), API documentation, and technical challenge retrospective sections.'),
                    ('Cloud Deployment, Custom Domains & Live Demos', 'Deployment', 25, 'Deploy projects to production cloud infrastructure (Vercel, AWS, Render) with custom SSL domains and populated realistic seed data.'),
                    ('Automated Testing & CI/CD Badges as Credibility Signals', 'Engineering Rigor', 25, 'Integrate automated GitHub Actions CI pipelines with unit test badges and code coverage reports to signal engineering maturity.')
                ]
            },
            {
                'order': 3,
                'title': 'Module 3: Behavioral Interviews & The STAR Method',
                'description': 'Behavioral frameworks, leadership principles, conflict resolution, and storytelling.',
                'lessons': [
                    ('Deconstructing Behavioral Interview Frameworks', 'Behavioral Strategy', 20, 'Understand what hiring managers evaluate: ownership, bias for action, dealing with ambiguity, and technical communication.'),
                    ('The STAR Method: Situation, Task, Action & Result', 'STAR Method', 25, 'Formulate compelling stories: quantifying results, focusing 70% of time on specific technical Actions taken, and lessons learned.'),
                    ('Mastering Tough Questions: Conflicts, Failures & Deadlines', 'Complex Scenarios', 25, 'Answer difficult behavioral questions: resolving technical disagreements with peers, post-mortems on failed deployments, and missed deadlines.'),
                    ('Reverse Interviewing: Asking Standout Questions to Leadership', 'Candidate Evaluation', 20, 'Evaluate prospective engineering teams: assessing on-call burden, technical debt management, promotion velocity, and engineering culture.')
                ]
            },
            {
                'order': 4,
                'title': 'Module 4: Technical Interview Negotiation & Offer Strategy',
                'description': 'System design communication, live coding strategy, compensation negotiation, and capstone.',
                'lessons': [
                    ('Live Coding Psychology & Whiteboard Communication', 'Interview Execution', 25, 'Think out loud effectively: clarifying constraints, discussing trade-offs before writing code, writing test cases, and handling hints.'),
                    ('System Design Interview Framework for Juniors & Mid-Levels', 'System Design Intro', 30, 'Structure 45-minute system design interviews: requirements clarification, capacity estimation, high-level design, and deep-dive bottlenecks.'),
                    ('Tech Compensation: Salary, Equity (RSUs/Options) & Negotiation', 'Negotiation Strategy', 25, 'Understand base salary, annual bonuses, equity vesting schedules, competing offer leverage, and counter-offer negotiation scripts.'),
                    ('Capstone Deliverable: Career Portfolio & Interview Master Dossier', 'Practical Deliverable', 45, 'Assemble an end-to-end career portfolio: ATS-formatted PDF resume, verified GitHub portfolio repository, and 5 polished STAR story scripts.')
                ]
            }
        ]
    },
    {
        'slug': 'modern-javascript-deep-dive',
        'title': 'Modern JavaScript & Asynchronous Programming',
        'category': 'programming',
        'topic_prefix': 'JavaScript',
        'lang': 'javascript',
        'modules': [
            {
                'order': 1,
                'title': 'Module 1: ECMAScript Standards, Scope & Data Types',
                'description': 'Modern JS fundamentals, primitive vs reference types, lexical scoping, and closures.',
                'lessons': [
                    ('Modern JavaScript Standards & Execution Contexts', 'JS Foundations', 15, 'Understand the ECMAScript specification, V8 engine compilation, execution contexts, and the call stack.'),
                    ('Variables & Scoping: var, let, const & The TDZ', 'Scoping & Declarations', 20, 'Compare function scope vs block scope, variable hoisting, and the Temporal Dead Zone (TDZ).'),
                    ('Primitive Types, Reference Types & Type Coercion', 'Types & Memory', 20, 'Deep dive into JS primitives, object heap references, explicit vs implicit type coercion, and strict equality (===).'),
                    ('Lexical Scope, Closures & The Module Pattern', 'Closures & Scope', 25, 'Master lexical scoping, closure memory retention, private state encapsulation, and IIFE module patterns.')
                ]
            },
            {
                'order': 2,
                'title': 'Module 2: Functions, Objects & The Prototype Chain',
                'description': 'First-class functions, arrow functions, this binding, and prototypal inheritance.',
                'lessons': [
                    ('Function Declarations, Expressions & Arrow Functions', 'Functions in JS', 20, 'Contrast function declarations, expressions, arrow functions, implicit returns, and arguments object.'),
                    ('The "this" Keyword: Call, Apply & Bind Mechanics', 'Execution Contexts', 25, 'Demystify "this": default binding, implicit object binding, explicit binding (call/apply/bind), and lexical arrow this.'),
                    ('Prototypal Inheritance & The Prototype Chain', 'Prototypes', 25, 'Understand __proto__, prototype properties, Object.create(), and how JavaScript resolves property lookups via prototypes.'),
                    ('ES6 Classes, Inheritance & Private Class Fields', 'Modern Classes', 20, 'Syntax sugar vs prototypes: class declarations, constructor methods, super(), static methods, and #private fields.')
                ]
            },
            {
                'order': 3,
                'title': 'Module 3: Asynchronous JavaScript & The Event Loop',
                'description': 'The event loop, microtasks vs macrotasks, Promises, and async/await.',
                'lessons': [
                    ('The Event Loop, Microtask Queue & Macrotask Queue', 'Event Loop Internals', 30, 'Understand single-threaded concurrency: call stack, Web APIs, Task Queue, Microtask Queue (Promises, queueMicrotask), and render cycle.'),
                    ('Promises: States, Chaining & Error Propagation', 'Promise Architecture', 25, 'Master Promise states (pending, fulfilled, rejected), then/catch chaining, Promise.all, Promise.race, and Promise.allSettled.'),
                    ('Async/Await Syntax & Syntactic Sugar for Promises', 'Async/Await', 20, 'Write synchronous-looking asynchronous code with async/await, try-catch error boundaries, and sequential vs parallel execution.'),
                    ('The Fetch API, HTTP Requests & AbortController', 'Network I/O', 25, 'Execute asynchronous HTTP network requests with fetch(), handle JSON payloads, error status codes, and cancel requests with AbortController.')
                ]
            },
            {
                'order': 4,
                'title': 'Module 4: DOM APIs, Modern Tooling & Capstone App',
                'description': 'Browser DOM manipulation, event delegation, ES modules, and a capstone application.',
                'lessons': [
                    ('DOM Traversal, Manipulation & DocumentFragment', 'DOM Engineering', 25, 'Query and manipulate the DOM tree efficiently: querySelector, createElement, batching DOM updates with DocumentFragment to prevent reflows.'),
                    ('Event Bubbling, Capturing & Event Delegation', 'Event Architecture', 25, 'Understand the 3 phases of event propagation (capture, target, bubble), stopPropagation(), and high-performance event delegation.'),
                    ('JavaScript Modules (ESM): Imports, Exports & Bundlers', 'Module Systems', 20, 'Compare CommonJS vs ES Modules, named and default exports, dynamic import(), and bundler concepts (Vite/Webpack).'),
                    ('Capstone Project: Real-Time Asynchronous Currency Tracker', 'Practical Deliverable', 45, 'Build a modern vanilla JS single-page application integrating asynchronous APIs, debounced inputs, localStorage persistence, and DOM state updates.')
                ]
            }
        ]
    },
    {
        'slug': 'modern-react-frontend-engineering',
        'title': 'Modern React & Frontend Engineering',
        'category': 'web-development',
        'topic_prefix': 'React',
        'lang': 'javascript',
        'modules': [
            {
                'order': 1,
                'title': 'Module 1: React Foundations & JSX Architecture',
                'description': 'Virtual DOM, JSX compilation, functional components, and props.',
                'lessons': [
                    ('React Philosophy, Virtual DOM & Fiber Reconciliation', 'React Core', 20, 'Understand why React exists, declarative UI, the Virtual DOM diffing algorithm, and React Fiber reconciliation architecture.'),
                    ('JSX Syntax, Expressions & Component Decomposition', 'JSX Foundations', 20, 'Write JSX correctly: expressions, conditional rendering, list keys, and decomposing UIs into atomic functional components.'),
                    ('Component Props, Children & Interface Contracts', 'Props & Composition', 20, 'Pass data with unidirectional props, prop destructuring, default values, children prop composition, and TypeScript interfaces.'),
                    ('Event Handling & Synthetic Events in React', 'Event System', 20, 'Handle UI interactions: SyntheticEvent cross-browser wrappers, event handler binding, and passing callbacks to child components.')
                ]
            },
            {
                'order': 2,
                'title': 'Module 2: State Management & The Hook Paradigm',
                'description': 'useState, useEffect lifecycle synchronization, and controlled forms.',
                'lessons': [
                    ('Stateful Components with the useState Hook', 'State Management', 25, 'Manage local component state: immutable state updates, updater functions (prev => next), and avoiding direct state mutation.'),
                    ('Side Effects & Lifecycle Management with useEffect', 'Lifecycle & Effects', 30, 'Synchronize with external systems: dependency arrays, effect cleanup functions, avoiding infinite loops, and strict mode double-invocations.'),
                    ('Controlled vs Uncontrolled Form Components & useRef', 'Forms & DOM Refs', 25, 'Build robust forms with controlled inputs, manage form state, and access raw DOM nodes directly using useRef without triggering re-renders.'),
                    ('Lifting State Up & Component Composition Patterns', 'Component Patterns', 20, 'Share state across sibling components by lifting state to common ancestors, container/presentational separation, and slot composition.')
                ]
            },
            {
                'order': 3,
                'title': 'Module 3: Advanced Hooks & Global State Systems',
                'description': 'useMemo, useCallback, custom hooks, and Context API.',
                'lessons': [
                    ('Performance Optimization: useMemo & useCallback', 'Performance', 30, 'Prevent unnecessary re-renders: React.memo shallow comparisons, memoizing expensive computations with useMemo, and caching callbacks with useCallback.'),
                    ('Complex State Reducers with useReducer', 'State Reducers', 25, 'Manage complex, multi-action state transitions predictably using useReducer, action dispatchers, and pure reducer functions.'),
                    ('Global State Management with React Context API', 'Context API', 25, 'Eliminate prop drilling: createContext, Context.Provider, useContext hook, and splitting context to prevent widespread re-renders.'),
                    ('Authoring Reusable Custom React Hooks', 'Custom Hooks', 25, 'Abstract and reuse stateful logic: authoring custom hooks (useLocalStorage, useFetch, useDebounce) following the Rules of Hooks.')
                ]
            },
            {
                'order': 4,
                'title': 'Module 4: Routing, Server Communication & Capstone App',
                'description': 'Client-side routing, optimistic UI updates, error boundaries, and capstone app.',
                'lessons': [
                    ('Client-Side Routing with React Router v6', 'SPA Routing', 25, 'Implement Single Page Application routing: BrowserRouter, Routes, Route, dynamic params with useParams, and programmatic navigation with useNavigate.'),
                    ('Asynchronous Data Fetching & Optimistic UI Updates', 'Data Fetching', 30, 'Fetch remote data reliably: loading/error states, race condition cancellation with AbortController, and optimistic UI updates.'),
                    ('Error Boundaries & Production Performance Profiling', 'Resilience & Audit', 25, 'Catch runtime component crashes with Error Boundaries, fallback UIs, code splitting with React.lazy and Suspense, and the React DevTools Profiler.'),
                    ('Capstone Project: Enterprise Kanban Project Management Dashboard', 'Practical Deliverable', 45, 'Architect and deploy an interactive Kanban board with drag-and-drop state, Context API global store, custom hooks, and responsive design.')
                ]
            }
        ]
    },
    {
        'slug': 'software-engineering-git-github',
        'title': 'Software Engineering, Git & GitHub Workflows',
        'category': 'career-development',
        'topic_prefix': 'Git',
        'lang': 'bash',
        'modules': [
            {
                'order': 1,
                'title': 'Module 1: Version Control Fundamentals & Git Internals',
                'description': 'Distributed version control, repository initialization, commits, and the DAG object model.',
                'lessons': [
                    ('Distributed Version Control & Git Mental Model', 'Git Core', 15, 'Compare centralized vs distributed version control, Git snapshots vs delta-based systems, and repository configuration (git config).'),
                    ('The Three Trees: Working Directory, Staging & Repository', 'Git Plumbing', 20, 'Understand file status lifecycle (untracked, modified, staged, committed), git add, git status, and git diff mechanics.'),
                    ('Commits, SHA-1 Hashes & Atomic Commit Hygiene', 'Commit Standards', 20, 'Create meaningful atomic commits, craft conventional commit messages (feat, fix, refactor), and inspect history with git log.'),
                    ('Git Internals: Blobs, Trees, Commits & The Object Database', 'Internal Architecture', 25, 'Explore .git directory: SHA-1 hashing, blob objects for file content, tree objects for directories, commit objects, and the index file.')
                ]
            },
            {
                'order': 2,
                'title': 'Module 2: Branching Strategies & Conflict Resolution',
                'description': 'Branch pointers, merge algorithms, fast-forward vs 3-way merges, and conflict resolution.',
                'lessons': [
                    ('Branching Mechanics: Pointers, HEAD & Switching', 'Branching', 20, 'Understand branches as lightweight movable pointers to commits, HEAD reference, git branch, and git switch/checkout.'),
                    ('Merging Algorithms: Fast-Forward vs Three-Way Merges', 'Merging', 25, 'Execute branch merges: fast-forward merges, three-way merges with common ancestor commit, and merge commit creation.'),
                    ('Merge Conflict Diagnosis & Systematic Resolution', 'Conflict Resolution', 25, 'Demystify merge conflicts: conflict markers (<<<<<<<, =======, >>>>>>>), resolving differences manually, and completing merges.'),
                    ('Git Stash & Worktree: Managing In-Flight Changes', 'Context Switching', 20, 'Save temporary uncommitted changes with git stash (push/pop/apply), and work on multiple branches simultaneously with git worktree.')
                ]
            },
            {
                'order': 3,
                'title': 'Module 3: History Rewriting & Remote Collaboration',
                'description': 'Interactive rebasing, cherry-picking, remotes, and pull request workflows.',
                'lessons': [
                    ('Interactive Rebasing: Squashing, Rewording & Dropping', 'History Rewriting', 30, 'Master git rebase -i: clean up commit history, squash WIP commits, edit commit messages, and understand the Golden Rule of Rebasing.'),
                    ('Surgical History Tools: Cherry-Pick, Revert & Reset', 'History Management', 25, 'Apply specific commits with git cherry-pick, safely undo shared commits with git revert, and understand git reset (--soft, --mixed, --hard).'),
                    ('Remote Repositories: Fetch, Pull, Push & Tracking Branches', 'Remote Collaboration', 25, 'Synchronize with remote servers: git remote, tracking branches, git fetch vs git pull, and tracking upstream repositories.'),
                    ('Pull Request Architecture & Professional Code Reviews', 'Code Review', 25, 'Structure production pull requests: PR descriptions, link issues, conduct constructive code reviews, request changes, and approval workflows.')
                ]
            },
            {
                'order': 4,
                'title': 'Module 4: CI/CD Automation, Release Engineering & Capstone',
                'description': 'GitHub Actions, automated testing, semantic versioning, and release pipelines.',
                'lessons': [
                    ('GitHub Actions: Workflows, Triggers & Runners', 'CI/CD Automation', 30, 'Automate software checks: write .github/workflows YAML files, configure push/pull_request triggers, and execute on virtual runners.'),
                    ('Automated Testing & Linting Pipelines in CI', 'Quality Gates', 25, 'Configure automated CI quality gates: run linter checks, execute unit test suites, and report coverage before allowing PR merges.'),
                    ('Semantic Versioning, Git Tags & Release Notes', 'Release Engineering', 25, 'Implement Semantic Versioning (MAJOR.MINOR.PATCH), create lightweight and annotated git tags, and automate GitHub Releases with changelogs.'),
                    ('Capstone Project: Production Open-Source Repository Architecture', 'Practical Deliverable', 45, 'Initialize and release a professional open-source project repository with branch protection rules, PR templates, CI/CD pipelines, and semantic releases.')
                ]
            }
        ]
    },
    {
        'slug': 'c-systems-programming-memory',
        'title': 'C Systems Programming & Memory Architecture',
        'category': 'cs-fundamentals',
        'topic_prefix': 'C Programming',
        'lang': 'c',
        'modules': [
            {
                'order': 1,
                'title': 'Module 1: C Language Foundations & Memory Layout',
                'description': 'Compilation toolchain, primitive datatypes, memory layout, and stack frames.',
                'lessons': [
                    ('The C Compilation Pipeline: Preprocessor, Compiler & Linker', 'Toolchain & Build', 20, 'Understand gcc/clang toolchains: preprocessing (#include, #define), compilation to assembly, assembling to object files (.o), and linking.'),
                    ('Primitive Types, Bit Widths & Memory Representations', 'Data Representation', 20, 'Examine integer and floating-point representations: char (1 byte), int, long, size_t, signed vs unsigned overflow, and IEEE 754 floats.'),
                    ('Memory Layout of a C Program: Text, Data, BSS, Heap & Stack', 'Process Memory', 25, 'Deconstruct a virtual memory address space: text segment (code), initialized data, uninitialized BSS, dynamic heap growth, and call stack.'),
                    ('Functions, Stack Frames & The Call Stack', 'Stack Mechanics', 25, 'Understand activation records: stack pointer (SP), base/frame pointer (BP), return addresses, local variable allocation, and stack buffer safety.')
                ]
            },
            {
                'order': 2,
                'title': 'Module 2: Pointers, Arrays & Dynamic Memory Management',
                'description': 'Pointer arithmetic, heap allocation, malloc/free, and memory leak prevention.',
                'lessons': [
                    ('Pointers Demystified: Addresses, Dereferencing & Indirection', 'Pointer Fundamentals', 30, 'Understand memory addresses, the address-of operator (&), dereference operator (*), NULL pointers, and void* generic pointers.'),
                    ('Pointer Arithmetic & Array Pointer Equivalence', 'Arrays & Pointers', 25, 'Master pointer arithmetic (ptr + 1 offsets by sizeof(type)), array decay to pointers, string literals as char*, and multidimensional arrays.'),
                    ('Dynamic Memory Allocation: malloc, calloc, realloc & free', 'Heap Allocation', 30, 'Allocate dynamic heap memory: malloc() uninitialized buffers, calloc() zero-cleared memory, realloc() resizing, and mandatory free() cleanups.'),
                    ('Memory Safety: Valgrind, Memory Leaks & Dangling Pointers', 'Memory Safety', 30, 'Diagnose critical memory vulnerabilities: buffer overflows, off-by-one errors, use-after-free, double-free bugs, and profiling with Valgrind Memcheck.')
                ]
            },
            {
                'order': 3,
                'title': 'Module 3: User-Defined Types & File I/O',
                'description': 'Structs, memory alignment, unions, function pointers, and streams.',
                'lessons': [
                    ('Structs, Typedef & Structure Memory Alignment (Padding)', 'Structures', 25, 'Define compound types with struct and typedef, member access (. and ->), and compiler padding/data alignment for hardware bus efficiency.'),
                    ('Unions, Bitfields & Low-Level Hardware Registers', 'Bitfields & Unions', 25, 'Share memory across variables using union, optimize flag storage with bitfields, and model low-level hardware memory registers.'),
                    ('Function Pointers & Callback Architectures', 'Function Pointers', 30, 'Treat functions as addressable pointers: function pointer syntax, implementing qsort() comparison callbacks, and jump tables.'),
                    ('Standard I/O Streams & Binary File Operations', 'File I/O', 25, 'Open, read, write, and close files with fopen, fread, fwrite, fseek, ftell, and managing buffered FILE* streams.')
                ]
            },
            {
                'order': 4,
                'title': 'Module 4: POSIX System Calls & Practical Deliverable',
                'description': 'System calls, process management, inter-process communication, and systems capstone.',
                'lessons': [
                    ('POSIX System Calls vs C Standard Library', 'System Interface', 25, 'Differentiate user-space library functions (printf) from kernel system calls (write), examining errno and strerr() error reporting.'),
                    ('Process Control: fork(), exec(), waitpid() & Zombie Processes', 'Process Control', 30, 'Create child processes with fork(), replace address space with execvp(), synchronize with waitpid(), and eliminate zombie processes.'),
                    ('Inter-Process Communication: POSIX Pipes & Signals', 'IPC & Signals', 30, 'Coordinate processes using unidirectional pipes (pipe()), redirect file descriptors with dup2(), and catch OS signals (SIGINT, SIGCHLD).'),
                    ('Capstone Project: Custom Unix Shell Implementation', 'Practical Deliverable', 45, 'Synthesize all low-level concepts to build a working Unix shell in C supporting command execution, argument parsing, backgrounding (&), and pipe redirection.')
                ]
            }
        ]
    }
]

print(f"Loaded metadata for {len(COURSES_METADATA)} primary courses.")

VIDEO_EMBEDS = [
    "https://www.youtube.com/embed/kqtD5dpn9C8?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/PqFKRqpHrjw?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/daefaLgNkw0?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/ZDa-Z5JzLYM?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/8DvywoWv6fI?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/fSytzGwwBVw?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/ZyhVh-qRZPA?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/GPVsHOlRBBI?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/wjZofJX0v4U?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/0pd36apRe34?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/W6NZfCO5SIk?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/bMknfKXIFA8?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/rfscVS0vtbw?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/DHvZLI7Db8E?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/8ext9G7xspg?enablejsapi=1&rel=0",
    "https://www.youtube.com/embed/1vR3W4666RQ?enablejsapi=1&rel=0"
]

def build_lesson_content(course_title, lesson_title, topic, summary, lang):
    code_samples = {
        'python': f"""# Production implementation: {lesson_title}
from typing import Dict, Any, List

def process_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"{summary}\"\"\"
    if not payload:
        raise ValueError("Payload cannot be empty")
    return {{"status": "SUCCESS", "topic": "{lesson_title}", "data": payload}}

# Execution trace
result = process_data({{"key": "test_metric", "val": 100}})
print("Result:", result)""",
        'sql': f"""-- Production schema & query: {lesson_title}
-- {summary}
BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED;

SELECT id, name, status, created_at
FROM records
WHERE is_active = TRUE
ORDER BY created_at DESC
LIMIT 50;

COMMIT;""",
        'javascript': f"""// Production implementation: {lesson_title}
// {summary}
export async function executeOperation(payload) {{
    if (!payload) throw new Error("Invalid payload");
    console.log(`[INFO] Processing ${{payload.id}} for {lesson_title}`);
    return {{ status: 200, topic: "{lesson_title}", timestamp: Date.now() }};
}}""",
        'bash': f"""#!/usr/bin/env bash
# Production automation: {lesson_title}
# {summary}
set -euo pipefail

echo "[INFO] Executing {lesson_title} workflow..."
git status --porcelain
echo "[SUCCESS] Verification passed." """,
        'c': f"""/* Production systems implementation: {lesson_title}
 * {summary}
 */
#include <stdio.h>
#include <stdlib.h>

int main(void) {{
    printf("[INFO] Executing {lesson_title} architecture\\n");
    return 0;
}}"""
    }

    selected_code = code_samples.get(lang, code_samples['python'])

    content_html = f"""<h3>{lesson_title}</h3>
<p>{summary}</p>
<h4>Theoretical Principles & Production Mechanics</h4>
<p>Understanding <strong>{lesson_title}</strong> is essential for architecting reliable, maintainable software systems within the <em>{course_title}</em> curriculum. By adhering to defensive engineering practices and analyzing runtime trade-offs, developers ensure deterministic behavior and optimal resource consumption.</p>
<h4>Code Implementation & Annotations</h4>
<pre><code class="language-{lang}">{selected_code}</code></pre>
<h4>System Architecture & Production Guidelines</h4>
<p>In high-throughput environments, enforce parameter validation before state modification, profile computational complexity, and maintain defensive logging boundaries.</p>"""
    return content_html


def build_curriculum_catalog():
    catalog = {}

    for c_idx, c_data in enumerate(COURSES_METADATA):
        slug = c_data['slug']
        course_title = c_data['title']
        lang = c_data['lang']

        modules_list = []
        global_lesson_order = 1

        for m_idx, m_info in enumerate(c_data['modules']):
            lessons_list = []

            for l_tuple in m_info['lessons']:
                l_title, l_chapter, l_mins, l_summary = l_tuple
                video_url = VIDEO_EMBEDS[(global_lesson_order - 1) % len(VIDEO_EMBEDS)]

                content = build_lesson_content(course_title, l_title, l_chapter, l_summary, lang)

                takeaways = [
                    f"Understand the core architecture and execution semantics of {l_title}.",
                    f"Implement defensive validation and error handling to ensure determinism.",
                    f"Profile memory allocation and runtime complexity before deploying to production."
                ]

                mistakes = [
                    f"Overlooking edge case boundary inputs or unvalidated parameters in {l_title}.",
                    f"Failing to account for thread contention, race conditions, or unhandled exceptions."
                ]

                exercise = {
                    'title': f'Implement {l_title[:30]} Handler',
                    'instructions': f'Write a function or query fulfilling the requirements for {l_title}. Ensure valid edge cases are handled.',
                    'starter_code': f"# Starter code for {l_title}\ndef handle_solution(input_data):\n    # Return expected solution\n    return input_data\n" if lang != 'sql' else f"-- SQL query for {l_title}\nSELECT * FROM records WHERE is_active = TRUE;\n",
                    'expected_output': 'handle_solution(True) == True' if lang != 'sql' else 'SELECT *',
                    'hints': f'Review the core syntax and parameters discussed in {l_title}.'
                }

                lesson_dict = {
                    'order': global_lesson_order,
                    'chapter': l_chapter,
                    'title': l_title,
                    'minutes': l_mins,
                    'video_url': video_url,
                    'video_duration': l_mins * 60,
                    'content': content,
                    'key_takeaways': takeaways,
                    'common_mistakes': mistakes,
                    'resources': f'<a href="https://docs.skillsphere.org" target="_blank" class="text-primary-accent-light">{course_title} Reference Documentation</a>',
                    'exercise': exercise
                }

                lessons_list.append(lesson_dict)
                global_lesson_order += 1

            modules_list.append({
                'order': m_info['order'],
                'title': m_info['title'],
                'description': m_info['description'],
                'lessons': lessons_list
            })

        # Assessments: Final Quiz & Final Mock
        final_quiz_questions = []
        final_mock_questions = []

        for q_idx in range(1, 11):
            q_text = f"Regarding {course_title}, which statement best describes the core architectural requirement in Question #{q_idx}?"
            opt_a = f"Deterministic execution with explicit invariant validation and defensive error bounds."
            opt_b = f"Unchecked runtime mutations across shared global state without synchronization."
            opt_c = f"Ignoring boundary edge conditions and relying solely on optimistic execution."
            opt_d = f"Bypassing interface contracts and hardcoding environment parameters."
            corr = 'A'
            expl = f"Option A is correct: {course_title} mandates deterministic execution, defensive error checking, and adherence to strict interface contracts."

            final_quiz_questions.append({
                'text': q_text,
                'question_text': q_text,
                'topic': f"Core Concepts - Part {q_idx}",
                'a': opt_a,
                'option_a': opt_a,
                'b': opt_b,
                'option_b': opt_b,
                'c': opt_c,
                'option_c': opt_c,
                'd': opt_d,
                'option_d': opt_d,
                'correct': corr,
                'correct_answer': corr,
                'explanation': expl
            })

            m_text = f"In an enterprise production scenario under heavy load, how should an engineer optimize {course_title} (Scenario #{q_idx})?"
            m_a = f"Profile time/space complexity, implement bounded caching, and enforce graceful error degradation."
            m_b = f"Spawn unbounded threads without pooling and swallow unexpected exceptions."
            m_c = f"Disable database transaction isolation levels and rely on local in-memory dictionaries."
            m_d = f"Increase CPU clock cycles without investigating underlying algorithmic inefficiencies."
            m_corr = 'A'
            m_expl = f"Option A is correct: Scalable enterprise deployments require systematic complexity profiling, bounded resource pools, and graceful failure boundaries."

            final_mock_questions.append({
                'text': m_text,
                'question_text': m_text,
                'topic': f"Production Engineering - Part {q_idx}",
                'a': m_a,
                'option_a': m_a,
                'b': m_b,
                'option_b': m_b,
                'c': m_c,
                'option_c': m_c,
                'd': m_d,
                'option_d': m_d,
                'correct': m_corr,
                'correct_answer': m_corr,
                'explanation': m_expl
            })

        assessments_list = [
            {
                'type': 'final_quiz',
                'title': f'{course_title} - Final Course Quiz',
                'description': f'Official comprehensive assessment for {course_title}. 10 questions covering all 4 modules. Passing score: 70%.',
                'duration': 30,
                'duration_minutes': 30,
                'pass_pct': 70,
                'passing_percentage': 70,
                'questions': final_quiz_questions
            },
            {
                'type': 'final_mock',
                'title': f'{course_title} - Final Mock Examination',
                'description': f'Proctored practical examination simulating senior technical interview problems for {course_title}. Passing score: 70%.',
                'duration': 45,
                'duration_minutes': 45,
                'pass_pct': 70,
                'passing_percentage': 70,
                'questions': final_mock_questions
            }
        ]

        catalog[slug] = {
            'modules': modules_list,
            'assessments': assessments_list
        }

    # Add aliases
    catalog['applied-data-science-eda'] = catalog['data-science-with-python-pandas']
    catalog['intro-to-ai-and-neural-networks'] = catalog['applied-ai-machine-learning']
    catalog['postgresql-database-mastery'] = catalog['relational-databases-sql-postgresql']

    return catalog


if __name__ == '__main__':
    catalog = build_curriculum_catalog()
    output_path = '/Users/ankitkumar/Desktop/wealthtrack/AnkitPortfolio/skill sphare/courses/curriculum_catalog.py'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Auto-generated authoritative SkillSphere Curriculum Catalog\n")
        f.write("# 12 Courses, 48 Modules, 192 Lessons (16 per course)\n\n")
        f.write("COURSES_CURRICULUM_CATALOG = ")
        f.write(repr(catalog))
        f.write("\n")
    print(f"Successfully generated curriculum catalog at {output_path} with {len(catalog)} courses.")

