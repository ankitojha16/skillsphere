from django.core.management.base import BaseCommand
from django.db import transaction
from careers.models import CareerTrack, CareerSkillRequirement


CURATED_TRACKS = [
    {
        'slug': 'frontend-developer',
        'title': 'Frontend Developer',
        'icon': 'layout',
        'badge': 'UI & Web Client',
        'summary': 'Build fluid, accessible, high-performance web user interfaces with modern CSS and JavaScript frameworks.',
        'overview': 'Frontend Developers are responsible for the client-side architecture of modern web applications. They transform complex design systems into fast, accessible, and responsive user experiences across mobile and desktop devices. Key responsibilities include managing client state, optimizing Core Web Vitals, and consuming REST/GraphQL APIs.',
        'difficulty_level': 'Beginner',
        'average_salary_range': '₹5.5L - ₹16L / $75k - $130k',
        'market_demand': 'High',
        'display_order': 1,
        'primary_skills': [
            'Modern JavaScript (ES6+)',
            'React.js / Next.js',
            'HTML5 Semantic Markup',
            'CSS3, Flexbox & Grid',
            'Responsive Web Design',
            'State Management',
            'Web Accessibility (WCAG 2.1)',
            'Web Performance & Core Web Vitals',
        ],
        'tools_and_technologies': [
            'React', 'Vite', 'Tailwind CSS', 'Bootstrap 5', 'TypeScript', 'Jest', 'Chrome DevTools', 'Figma'
        ],
        'suggested_projects': [
            {
                'title': 'Interactive Analytics Dashboard',
                'description': 'Real-time telemetry dashboard with SVG charts, dark mode toggle, and accessible data grids.',
                'difficulty': 'Intermediate'
            },
            {
                'title': 'Accessible SaaS Design System',
                'description': 'Modular component library with full keyboard navigation, screen reader ARIA roles, and micro-interactions.',
                'difficulty': 'Advanced'
            },
            {
                'title': 'Collaborative Kanban Board',
                'description': 'Drag-and-drop task workflow with optimistic UI updates and local persistence.',
                'difficulty': 'Intermediate'
            }
        ],
        'interview_topics': [
            'Event Bubbling, Capturing, and Delegation',
            'Virtual DOM Reconciliation & React Fiber',
            'CSS Specificity, BEM, and CSS-in-JS trade-offs',
            'Web Performance (LCP, FID/INP, CLS)',
            'Cross-Browser Compatibility & Polyfills'
        ],
        'learning_milestones': [
            {'order': 1, 'title': 'HTML5 & Modern CSS Layouts', 'weeks': 2, 'topics': ['Flexbox', 'CSS Grid', 'Media Queries'], 'mini_project': 'Responsive Landing Page'},
            {'order': 2, 'title': 'JavaScript Deep Dive & DOM', 'weeks': 3, 'topics': ['ES6+', 'Async/Await', 'Fetch API', 'DOM Manipulation'], 'mini_project': 'Dynamic Quiz Application'},
            {'order': 3, 'title': 'React.js Component Architecture', 'weeks': 4, 'topics': ['Hooks', 'Context API', 'Component Lifecycle', 'Router'], 'mini_project': 'Course Catalog Explorer'},
            {'order': 4, 'title': 'State, Testing & Performance', 'weeks': 3, 'topics': ['Lighthouse Audits', 'Unit Testing', 'Accessibility'], 'mini_project': 'Production Developer Portfolio'}
        ],
        'skills': [
            ('Modern JavaScript (ES6+)', 'frontend', 'essential', 3, 'Language core, closures, asynchronous promises, and prototypes.'),
            ('React.js / Next.js', 'frontend', 'essential', 3, 'Component composition, custom hooks, and state lifecycles.'),
            ('HTML5 & Responsive CSS', 'frontend', 'essential', 3, 'Semantic markup, mobile-first responsive layouts, and grid systems.'),
            ('Web Accessibility (a11y)', 'frontend', 'recommended', 2, 'ARIA roles, color contrast, keyboard tab navigation.'),
            ('State Management', 'frontend', 'recommended', 2, 'Redux Toolkit, Zustand, or Context API state flows.'),
            ('TypeScript Basics', 'frontend', 'bonus', 1, 'Typed JavaScript interfaces, generics, and compile-time safety.'),
        ]
    },
    {
        'slug': 'backend-developer',
        'title': 'Backend Developer',
        'icon': 'server',
        'badge': 'APIs & Architecture',
        'summary': 'Architect high-throughput server backends, microservices, databases, authentication, and secure APIs.',
        'overview': 'Backend Developers build the engine that powers modern applications. They design relational database schemas, construct scalable RESTful and GraphQL APIs, enforce security and authentication protocols, and optimize query latency for high-concurrency workloads.',
        'difficulty_level': 'Intermediate',
        'average_salary_range': '₹6.5L - ₹20L / $90k - $150k',
        'market_demand': 'Surging',
        'display_order': 2,
        'primary_skills': [
            'Python / Node.js / Go',
            'Django & REST Framework',
            'PostgreSQL & Relational Design',
            'Authentication & JWT / OAuth2',
            'Redis Caching & Pub/Sub',
            'API Security & Rate Limiting',
            'Docker & Containerization',
            'Unit & Integration Testing',
        ],
        'tools_and_technologies': [
            'Django', 'FastAPI', 'PostgreSQL', 'Redis', 'Docker', 'Postman', 'pytest', 'Nginx'
        ],
        'suggested_projects': [
            {
                'title': 'High-Throughput Payment & Billing API',
                'description': 'Idempotent transaction gateway with webhook verification, ledger durability, and rate limiting.',
                'difficulty': 'Advanced'
            },
            {
                'title': 'Distributed Job Queue & Worker Daemon',
                'description': 'Durable background task manager with heartbeat fencing, dead-letter recovery, and retry backoff.',
                'difficulty': 'Advanced'
            },
            {
                'title': 'Role-Based Authentication & RBAC Engine',
                'description': 'Secure identity server with JWT tokens, refresh rotation, and fine-grained permission checks.',
                'difficulty': 'Intermediate'
            }
        ],
        'interview_topics': [
            'Database Indexing (B-Tree, Hash, GIN) & Query Plans',
            'ACID Transactions & Isolation Levels (Read Committed vs Serializable)',
            'RESTful Idempotency & HTTP Status Codes',
            'CAP Theorem & Distributed Consistency',
            'Connection Pooling & Memory Management'
        ],
        'learning_milestones': [
            {'order': 1, 'title': 'Backend Fundamentals & Python', 'weeks': 2, 'topics': ['OOP', 'Modules', 'Exception Handling'], 'mini_project': 'CLI File Parser & Validator'},
            {'order': 2, 'title': 'RESTful API Engineering (Django/DRF)', 'weeks': 4, 'topics': ['Serializers', 'Generic Views', 'Permissions', 'Pagination'], 'mini_project': 'E-Commerce Storefront API'},
            {'order': 3, 'title': 'Relational Database Mastery', 'weeks': 3, 'topics': ['Normalization', 'EXPLAIN ANALYZE', 'Constraints', 'Migrations'], 'mini_project': 'Multi-Tenant SaaS Schema'},
            {'order': 4, 'title': 'Caching, Queues & Production Readiness', 'weeks': 3, 'topics': ['Redis Caching', 'Background Tasks', 'Docker Deployment'], 'mini_project': 'High-Throughput Notification Engine'}
        ],
        'skills': [
            ('Django & REST Framework', 'backend', 'essential', 3, 'REST API endpoints, serialization, viewsets, and middleware.'),
            ('PostgreSQL & SQL Tuning', 'database', 'essential', 3, 'Query plan optimization, indexes, and transactional consistency.'),
            ('API Security & Auth (JWT/OAuth)', 'security', 'essential', 3, 'Secure session handling, token rotation, and password hashing.'),
            ('Redis & Distributed Caching', 'backend', 'recommended', 2, 'Key-value caching, atomic counters, and TTL management.'),
            ('Docker Containerization', 'devops', 'recommended', 2, 'Multi-stage Docker builds, container networking, and healthchecks.'),
            ('Asynchronous Task Processing', 'backend', 'bonus', 1, 'Worker daemon loops, job queues, and recovery mechanics.'),
        ]
    },
    {
        'slug': 'fullstack-developer',
        'title': 'Full Stack Developer',
        'icon': 'layers',
        'badge': 'End-to-End',
        'summary': 'Engineer complete web products from interactive frontends to scalable databases, backend APIs, and cloud services.',
        'overview': 'Full Stack Developers bridge the entire lifecycle of software creation. They possess the versatility to craft polished user experiences, architect robust backend business logic, write relational database queries, and automate deployment pipelines.',
        'difficulty_level': 'Intermediate',
        'average_salary_range': '₹7L - ₹22L / $95k - $160k',
        'market_demand': 'Surging',
        'display_order': 3,
        'primary_skills': [
            'JavaScript / TypeScript',
            'React.js',
            'Python / Django',
            'REST APIs',
            'PostgreSQL',
            'Git & CI/CD Pipelines',
            'Web Security (CSRF, XSS, CORS)',
            'System Deployment',
        ],
        'tools_and_technologies': [
            'Python', 'Django', 'React', 'PostgreSQL', 'Tailwind', 'Docker', 'GitHub Actions', 'VS Code'
        ],
        'suggested_projects': [
            {
                'title': 'Full-Stack EdTech Learning Platform',
                'description': 'End-to-end platform with video lessons, quiz evaluations, gamified XP, and certificate PDF generation.',
                'difficulty': 'Advanced'
            },
            {
                'title': 'Real-Time Team Collaboration Hub',
                'description': 'Project management portal with task boards, activity feeds, and real-time chat updates.',
                'difficulty': 'Advanced'
            }
        ],
        'interview_topics': [
            'Client-Server Architecture & Latency Optimization',
            'Web Security: XSS, CSRF, and SQL Injection Prevention',
            'State Synchronization between Frontend and Backend',
            'Full Stack Performance Profiling'
        ],
        'learning_milestones': [
            {'order': 1, 'title': 'Frontend Foundations (HTML/CSS/JS)', 'weeks': 3, 'topics': ['Responsive UI', 'Fetch API', 'DOM Manipulation'], 'mini_project': 'Client Portal'},
            {'order': 2, 'title': 'Backend Systems & Database Design', 'weeks': 4, 'topics': ['Django Models', 'PostgreSQL', 'REST Endpoints'], 'mini_project': 'RESTful Store API'},
            {'order': 3, 'title': 'Full-Stack Integration & Auth', 'weeks': 4, 'topics': ['Token Authentication', 'Single-Page Apps', 'API Consumption'], 'mini_project': 'SkillSphere Clone'},
            {'order': 4, 'title': 'CI/CD, Docker & Cloud Deployment', 'weeks': 3, 'topics': ['Containers', 'GitHub Actions', 'Monitoring'], 'mini_project': 'Live Production SaaS'}
        ],
        'skills': [
            ('React.js & Frontend UI', 'frontend', 'essential', 3, 'Interactive components, state management, and modern CSS.'),
            ('Python & Django Backend', 'backend', 'essential', 3, 'Model design, ORM queries, REST endpoints, and authentication.'),
            ('PostgreSQL Schema & Queries', 'database', 'essential', 3, 'Relational normalization, foreign keys, and indexes.'),
            ('Web Security Fundamentals', 'security', 'recommended', 2, 'CORS, CSRF tokens, secure cookies, and input sanitization.'),
            ('Git & CI/CD Automation', 'devops', 'recommended', 2, 'Branching models, automated test workflows, and deployments.'),
            ('Cloud Deployment & Docker', 'devops', 'bonus', 1, 'Containers, reverse proxies, and cloud runtime configurations.'),
        ]
    },
    {
        'slug': 'python-developer',
        'title': 'Python Developer',
        'icon': 'terminal',
        'badge': 'High Demand',
        'summary': 'Develop server-side logic, automation pipelines, web frameworks, and robust backends with modern Python 3.12+.',
        'overview': 'Python Developers leverage the power and elegance of Python to solve computational problems, build enterprise backends, orchestrate automated data pipelines, and develop script utilities for high-productivity engineering organizations.',
        'difficulty_level': 'Beginner',
        'average_salary_range': '₹6L - ₹18L / $85k - $140k',
        'market_demand': 'High',
        'display_order': 4,
        'primary_skills': [
            'Python 3.12+ Syntax & Idioms',
            'Object-Oriented Programming (OOP)',
            'Decorators, Generators & Context Managers',
            'Data Structures & Algorithms',
            'Django / Flask / FastAPI',
            'SQL & Relational Databases',
            'pytest & Test-Driven Development',
            'Virtual Environments & Dependency Pinning',
        ],
        'tools_and_technologies': [
            'Python 3.12', 'pytest', 'Black / Flake8', 'Pip / Poetry', 'PostgreSQL', 'SQLite', 'Git'
        ],
        'suggested_projects': [
            {
                'title': 'High-Throughput Log Aggregator & Parser',
                'description': 'CLI utility that streams, filters, and parses GB-scale server logs with generators and multiprocessing.',
                'difficulty': 'Intermediate'
            },
            {
                'title': 'Automated Web Scraping & Data Pipeline',
                'description': 'Scraper engine with polite rate-limiting, error retries, and clean SQLite storage.',
                'difficulty': 'Intermediate'
            }
        ],
        'interview_topics': [
            'Python GIL (Global Interpreter Lock) & Concurrency (Threading vs Multiprocessing vs Asyncio)',
            'Memory Management & Garbage Collection in CPython',
            'Decorators, Closures, and Class Metaprogramming',
            'Magic Methods (__getitem__, __enter__, __exit__)'
        ],
        'learning_milestones': [
            {'order': 1, 'title': 'Python Fundamentals & Idioms', 'weeks': 2, 'topics': ['Control Flow', 'Data Types', 'List Comprehensions'], 'mini_project': 'CLI Contact Manager'},
            {'order': 2, 'title': 'OOP, Metaprogramming & File I/O', 'weeks': 3, 'topics': ['Classes', 'Inheritance', 'Decorators', 'Generators'], 'mini_project': 'Custom CSV Processor'},
            {'order': 3, 'title': 'Testing, Packaging & Libraries', 'weeks': 2, 'topics': ['pytest', 'Virtualenvs', 'boto3 / requests'], 'mini_project': 'Automated API Client'},
            {'order': 4, 'title': 'Web Frameworks & Database Integration', 'weeks': 4, 'topics': ['Django ORM', 'SQLAlchemy', 'Async Views'], 'mini_project': 'Full Web Application'}
        ],
        'skills': [
            ('Python 3.12+ Core', 'backend', 'essential', 3, 'Generators, list comprehensions, type hinting, and standard libraries.'),
            ('Object-Oriented Design', 'methodology', 'essential', 3, 'Inheritance, polymorphism, encapsulation, and SOLID principles.'),
            ('pytest & Automated Testing', 'methodology', 'essential', 3, 'Unit testing, test fixtures, mocking, and coverage analysis.'),
            ('Relational Databases & SQL', 'database', 'recommended', 2, 'CRUD operations, joins, group by, and query tuning.'),
            ('Asynchronous Python (asyncio)', 'backend', 'bonus', 1, 'Async/await syntax, event loops, and non-blocking I/O.'),
        ]
    },
    {
        'slug': 'data-analyst',
        'title': 'Data Analyst',
        'icon': 'bar-chart-2',
        'badge': 'Insights & BI',
        'summary': 'Analyze business datasets, create actionable reports, and uncover trends using SQL, Python, and BI dashboards.',
        'overview': 'Data Analysts translate data into actionable commercial insights. They cleanse raw telemetry, execute complex analytical queries with window functions, formulate key performance indicators (KPIs), and present executive dashboards.',
        'difficulty_level': 'Beginner',
        'average_salary_range': '₹5L - ₹15L / $70k - $120k',
        'market_demand': 'High',
        'display_order': 5,
        'primary_skills': [
            'Advanced SQL (Window Functions, CTEs)',
            'Python (Pandas, NumPy)',
            'Data Cleaning & Wrangling',
            'Data Visualization (Matplotlib, Seaborn)',
            'Business Intelligence (PowerBI / Tableau)',
            'Exploratory Data Analysis (EDA)',
            'Statistical Aggregations',
        ],
        'tools_and_technologies': [
            'SQL', 'Pandas', 'Jupyter Notebook', 'Tableau', 'PowerBI', 'PostgreSQL', 'Excel'
        ],
        'suggested_projects': [
            {
                'title': 'Customer Retention & Churn Analysis',
                'description': 'Cohort-based retention analysis identifying friction points and predicting subscriber churn.',
                'difficulty': 'Intermediate'
            },
            {
                'title': 'E-Commerce Sales Performance Dashboard',
                'description': 'Interactive revenue breakdown by product category, regional geography, and seasonality.',
                'difficulty': 'Intermediate'
            }
        ],
        'interview_topics': [
            'SQL Window Functions: ROW_NUMBER(), RANK(), DENSE_RANK()',
            'Common Table Expressions (CTEs) vs Subqueries',
            'Dealing with Missing Values and Skewed Distributions',
            'A/B Testing Metrics & Statistical Significance'
        ],
        'learning_milestones': [
            {'order': 1, 'title': 'SQL Analytics Foundations', 'weeks': 3, 'topics': ['Joins', 'Aggregations', 'Window Functions'], 'mini_project': 'Sales Query Suite'},
            {'order': 2, 'title': 'Python for Data Analysis (Pandas/NumPy)', 'weeks': 3, 'topics': ['DataFrames', 'Imputation', 'Groupby'], 'mini_project': 'EDA Dataset Notebook'},
            {'order': 3, 'title': 'Data Visualization & Storytelling', 'weeks': 2, 'topics': ['Seaborn', 'Matplotlib', 'Dashboard Layouts'], 'mini_project': 'Executive Chart Deck'},
            {'order': 4, 'title': 'Business Analytics & Capstone', 'weeks': 3, 'topics': ['KPI Formulation', 'Cohort Analysis'], 'mini_project': 'Complete Industry Report'}
        ],
        'skills': [
            ('Advanced SQL & Window Functions', 'database', 'essential', 3, 'Multi-table joins, subqueries, partitions, and window aggregations.'),
            ('Python (Pandas & NumPy)', 'data_ai', 'essential', 3, 'DataFrame filtering, transformation, reshaping, and calculations.'),
            ('Data Cleaning & Imputation', 'data_ai', 'essential', 3, 'Detecting anomalies, handling nulls, and formatting schema types.'),
            ('Data Visualization & Storytelling', 'data_ai', 'recommended', 2, 'Creating clear, unskewed charts with Matplotlib/Seaborn.'),
            ('Statistical Analysis Basics', 'data_ai', 'recommended', 2, 'Mean, median, standard deviation, percentile distributions.'),
        ]
    },
    {
        'slug': 'data-scientist',
        'title': 'Data Scientist',
        'icon': 'pie-chart',
        'badge': 'Predictive Modeling',
        'summary': 'Build predictive models, statistical frameworks, and machine learning pipelines to extract deep insights from data.',
        'overview': 'Data Scientists design mathematical algorithms that predict future outcomes and identify non-obvious patterns in vast datasets. They formulate hypotheses, engineer novel features, train regression and classification models, and validate robustness against overfitting.',
        'difficulty_level': 'Advanced',
        'average_salary_range': '₹8L - ₹25L / $105k - $175k',
        'market_demand': 'Surging',
        'display_order': 6,
        'primary_skills': [
            'Applied Probability & Statistics',
            'Machine Learning (Scikit-Learn)',
            'Feature Engineering & Selection',
            'Supervised & Unsupervised Learning',
            'Model Evaluation Metrics (ROC-AUC, F1)',
            'Python Data Ecosystem (Pandas, SciPy)',
            'Hypothesis Testing & A/B Testing',
        ],
        'tools_and_technologies': [
            'Python', 'Scikit-Learn', 'Pandas', 'Jupyter', 'SciPy', 'Statsmodels', 'Git'
        ],
        'suggested_projects': [
            {
                'title': 'Credit Default Risk Predictive Classifier',
                'description': 'Supervised classification model predicting loan defaults with balanced precision-recall trade-offs.',
                'difficulty': 'Advanced'
            },
            {
                'title': 'Personalized Student Recommendation Engine',
                'description': 'Collaborative filtering model suggesting courses based on historical enrollment affinity.',
                'difficulty': 'Advanced'
            }
        ],
        'interview_topics': [
            'Bias-Variance Tradeoff & Regularization (L1 Lasso vs L2 Ridge)',
            'Precision, Recall, ROC-AUC, and Confusion Matrix interpretation',
            'Central Limit Theorem, p-values, and Type I/II errors',
            'Tree Ensembles: Random Forest vs XGBoost / LightGBM'
        ],
        'learning_milestones': [
            {'order': 1, 'title': 'Applied Math & Statistical Foundations', 'weeks': 3, 'topics': ['Distributions', 'Hypothesis Testing', 'Linear Algebra'], 'mini_project': 'Statistical Analysis Notebook'},
            {'order': 2, 'title': 'Supervised Machine Learning', 'weeks': 4, 'topics': ['Linear Regression', 'Logistic Regression', 'Decision Trees'], 'mini_project': 'Housing Price Predictor'},
            {'order': 3, 'title': 'Ensembles & Unsupervised Learning', 'weeks': 4, 'topics': ['Random Forest', 'XGBoost', 'K-Means Clustering', 'PCA'], 'mini_project': 'Customer Segmentation Model'},
            {'order': 4, 'title': 'Model Validation, Tuning & Deployment', 'weeks': 3, 'topics': ['Cross-Validation', 'Hyperparameter Tuning', 'Model Serializing'], 'mini_project': 'Production Prediction API'}
        ],
        'skills': [
            ('Statistical Inference & Probability', 'data_ai', 'essential', 3, 'Hypothesis tests, distributions, p-values, and confidence intervals.'),
            ('Scikit-Learn Machine Learning', 'data_ai', 'essential', 3, 'Training, cross-validating, and tuning regression and classification models.'),
            ('Feature Engineering', 'data_ai', 'essential', 3, 'Scaling, one-hot encoding, polynomial features, and dimension reduction.'),
            ('Model Evaluation & Metrics', 'data_ai', 'recommended', 2, 'ROC-AUC, precision-recall curve, mean squared error.'),
            ('Unsupervised Learning (Clustering/PCA)', 'data_ai', 'bonus', 1, 'K-means, hierarchical clustering, and principal component analysis.'),
        ]
    },
    {
        'slug': 'ai-ml-engineer',
        'title': 'AI/ML Engineer',
        'icon': 'cpu',
        'badge': 'Cutting Edge',
        'summary': 'Develop and deploy intelligent machine learning systems, deep learning architectures, and LLM applications in production.',
        'overview': 'AI/ML Engineers transform theoretical models into scalable production systems. They train deep neural networks, build Retrieval-Augmented Generation (RAG) pipelines with vector databases, fine-tune open weights models, and optimize inference latency.',
        'difficulty_level': 'Advanced',
        'average_salary_range': '₹9L - ₹28L / $115k - $190k',
        'market_demand': 'Surging',
        'display_order': 7,
        'primary_skills': [
            'Deep Learning (PyTorch / TensorFlow)',
            'Large Language Models (LLMs) & Prompts',
            'RAG Pipelines & Vector Databases',
            'Model Serving (FastAPI, ONNX, TorchServe)',
            'Neural Network Optimization',
            'Transformers & Attention Mechanisms',
            'MLOps & Containerized Inference',
        ],
        'tools_and_technologies': [
            'PyTorch', 'Hugging Face', 'ChromaDB', 'FastAPI', 'Docker', 'LangChain', 'Python'
        ],
        'suggested_projects': [
            {
                'title': 'Enterprise Technical Document Q&A (RAG)',
                'description': 'Semantic search and document synthesis using vector embeddings, hybrid search, and citation grounding.',
                'difficulty': 'Advanced'
            },
            {
                'title': 'Autonomous Code Review & Refactoring Assistant',
                'description': 'LLM-powered tool analyzing ASTs and generating automated pull request feedback with confidence scoring.',
                'difficulty': 'Advanced'
            }
        ],
        'interview_topics': [
            'Self-Attention Mechanism & Transformer Encoder/Decoder Architecture',
            'Mitigating LLM Hallucinations in Production Applications',
            'Vector Embeddings: Cosine Similarity vs Dot Product vs Euclidean Distance',
            'Model Quantization (FP16, INT8, GGUF) and Latency Bottlenecks'
        ],
        'learning_milestones': [
            {'order': 1, 'title': 'Deep Learning with PyTorch', 'weeks': 4, 'topics': ['Tensors', 'Autograd', 'Loss Functions', 'CNNs'], 'mini_project': 'Image Classifier from Scratch'},
            {'order': 2, 'title': 'Transformers & NLP Fundamentals', 'weeks': 4, 'topics': ['Tokenization', 'Attention', 'Hugging Face Transformers'], 'mini_project': 'Sentiment Classification Engine'},
            {'order': 3, 'title': 'LLM Application Engineering & RAG', 'weeks': 4, 'topics': ['Vector DBs', 'Embeddings', 'Chunking Strategies', 'Prompt Chains'], 'mini_project': 'SkillSphere AI Assistant Module'},
            {'order': 4, 'title': 'MLOps & High-Throughput Serving', 'weeks': 3, 'topics': ['Model Serving with FastAPI', 'Batching', 'GPU Utilization'], 'mini_project': 'Scalable Model Microservice'}
        ],
        'skills': [
            ('PyTorch & Neural Networks', 'data_ai', 'essential', 3, 'Building, training, and evaluating deep learning architectures.'),
            ('LLM Orchestration & RAG', 'data_ai', 'essential', 3, 'Vector search, embedding models, context window management, and prompting.'),
            ('Model Serving & Inference APIs', 'backend', 'essential', 3, 'Exposing PyTorch models via high-performance asynchronous REST endpoints.'),
            ('Hugging Face Transformers', 'data_ai', 'recommended', 2, 'Utilizing pre-trained foundation models for sequence classification and generation.'),
            ('Vector Databases (Chroma / Pinecone)', 'database', 'recommended', 2, 'Index structures, similarity search, and hybrid vector retrieval.'),
        ]
    },
    {
        'slug': 'cybersecurity-analyst',
        'title': 'Cybersecurity Analyst',
        'icon': 'shield-alert',
        'badge': 'Security & Defense',
        'summary': 'Protect digital infrastructure, conduct vulnerability assessments, and safeguard networks from cyber threats.',
        'overview': 'Cybersecurity Analysts protect networks, web applications, and sensitive student databases from adversarial attacks. They conduct penetration testing, configure web application firewalls (WAF), enforce encryption standards, and establish incident response protocols.',
        'difficulty_level': 'Intermediate',
        'average_salary_range': '₹6L - ₹19L / $85k - $145k',
        'market_demand': 'High',
        'display_order': 8,
        'primary_skills': [
            'Network Security & Protocols (TCP/IP, TLS)',
            'OWASP Top 10 Web Vulnerabilities',
            'Vulnerability Scanning & Penetration Testing',
            'Identity & Access Management (IAM)',
            'Cryptography & PKI Infrastructure',
            'Security Information & Event Management (SIEM)',
            'Linux Security Hardening',
        ],
        'tools_and_technologies': [
            'Wireshark', 'Burp Suite', 'Nmap', 'Linux', 'Metasploit', 'Snort', 'OpenSSL'
        ],
        'suggested_projects': [
            {
                'title': 'Automated Web Vulnerability Scanner',
                'description': 'Python scanner detecting SQL injection, missing security headers, and open CORS policies.',
                'difficulty': 'Advanced'
            },
            {
                'title': 'Network Intrusion Detection & Alerting System',
                'description': 'Packet sniffer that flags port scans, brute-force SSH attacks, and anomalous traffic spikes.',
                'difficulty': 'Advanced'
            }
        ],
        'interview_topics': [
            'OWASP Top 10: Mitigating SQL Injection, XSS, and SSRF',
            'Symmetric (AES) vs Asymmetric (RSA/ECC) Cryptography',
            'TLS Handshake & Certificate Verification Mechanics',
            'Principle of Least Privilege in Cloud IAM'
        ],
        'learning_milestones': [
            {'order': 1, 'title': 'Networking Foundations & Linux Security', 'weeks': 3, 'topics': ['OSI Model', 'Packet Analysis', 'Linux Permissions'], 'mini_project': 'Hardened Linux Bastion Host'},
            {'order': 2, 'title': 'Web Application Security (OWASP)', 'weeks': 4, 'topics': ['Injection Flaws', 'Broken Auth', 'CORS', 'CSRF'], 'mini_project': 'Vulnerable App Audit Report'},
            {'order': 3, 'title': 'Cryptography & Network Defense', 'weeks': 3, 'topics': ['TLS/SSL', 'Hashes', 'Firewalls', 'IDS/IPS'], 'mini_project': 'End-to-End Encrypted File Vault'},
            {'order': 4, 'title': 'Security Auditing & Incident Response', 'weeks': 3, 'topics': ['Log Analysis', 'Vulnerability Assessment', 'Threat Modeling'], 'mini_project': 'Automated Compliance Auditor'}
        ],
        'skills': [
            ('OWASP Top 10 Remediation', 'security', 'essential', 3, 'Detecting and mitigating web vulnerabilities (XSS, SQLi, CSRF, IDOR).'),
            ('Network Protocols & Wireshark', 'security', 'essential', 3, 'Packet inspection, subnetting, TCP/IP handshake, and DNS security.'),
            ('Cryptography & Public Key Infrastructure', 'security', 'essential', 3, 'Symmetric/asymmetric encryption, hashing algorithms, and SSL/TLS certificates.'),
            ('Linux System Hardening', 'security', 'recommended', 2, 'File permissions, firewall rules (iptables/ufw), and SSH key management.'),
            ('Vulnerability Assessment Tools', 'security', 'bonus', 1, 'Proficiency with Nmap, Burp Suite, and automated security scanners.'),
        ]
    },
    {
        'slug': 'cloud-engineer',
        'title': 'Cloud Engineer',
        'icon': 'cloud',
        'badge': 'Infrastructure & Scale',
        'summary': 'Design, provision, and maintain resilient multi-zone cloud infrastructure and automated delivery pipelines.',
        'overview': 'Cloud Engineers architect the foundations upon which modern software operates. They define infrastructure as code (IaC), establish virtual private clouds across multiple availability zones, automate container orchestration with ECS and Kubernetes, and monitor fleet reliability.',
        'difficulty_level': 'Intermediate',
        'average_salary_range': '₹7L - ₹21L / $95k - $155k',
        'market_demand': 'Surging',
        'display_order': 9,
        'primary_skills': [
            'Amazon Web Services (AWS) Core Services',
            'Infrastructure as Code (Terraform / OpenTofu)',
            'Container Orchestration (Docker, ECS Fargate)',
            'VPC Networking & Subnet Architecture',
            'CI/CD Pipelines (GitHub Actions)',
            'Cloud Monitoring & Observability (CloudWatch)',
            'High Availability & Disaster Recovery',
        ],
        'tools_and_technologies': [
            'Terraform', 'OpenTofu', 'AWS', 'Docker', 'GitHub Actions', 'Linux', 'CloudWatch', 'Bash'
        ],
        'suggested_projects': [
            {
                'title': 'Multi-AZ High Availability ECS Cluster (Terraform)',
                'description': 'Complete IaC configuration with VPC, NAT gateways, ALB, ECS Fargate, and auto-scaling.',
                'difficulty': 'Advanced'
            },
            {
                'title': 'Automated Zero-Downtime CI/CD Delivery Pipeline',
                'description': 'GitHub Actions workflow with OIDC authentication, automated regression tests, ECR push, and rolling updates.',
                'difficulty': 'Intermediate'
            }
        ],
        'interview_topics': [
            'Public vs Private Subnets & Route Tables in AWS VPC',
            'Terraform State Management, Locking, and Drift Detection',
            'ECS Task Definition vs Service vs Cluster Mechanics',
            'Multi-Region Disaster Recovery (RPO vs RTO)'
        ],
        'learning_milestones': [
            {'order': 1, 'title': 'Cloud Networking & AWS Foundations', 'weeks': 3, 'topics': ['VPC', 'Subnets', 'Gateways', 'Security Groups'], 'mini_project': 'Multi-Tier Cloud Network'},
            {'order': 2, 'title': 'Infrastructure as Code (Terraform/OpenTofu)', 'weeks': 4, 'topics': ['HCL Syntax', 'Modules', 'State Backends', 'Variables'], 'mini_project': 'Reusable Terraform Module Suite'},
            {'order': 3, 'title': 'Containers & Orchestration (Fargate/ECS)', 'weeks': 3, 'topics': ['Dockerfiles', 'Task Definitions', 'ALB Health Checks'], 'mini_project': 'Scalable Web App Deployment'},
            {'order': 4, 'title': 'Observability, Security & Cost Control', 'weeks': 3, 'topics': ['CloudWatch Alarms', 'IAM Least Privilege', 'Billing Budgets'], 'mini_project': 'Production Observability Stack'}
        ],
        'skills': [
            ('Infrastructure as Code (Terraform/OpenTofu)', 'devops', 'essential', 3, 'Writing declarative HCL modules, state management, and plan verification.'),
            ('AWS VPC & Networking', 'devops', 'essential', 3, 'Configuring subnets, NAT gateways, internet gateways, and security groups.'),
            ('Docker & Container Orchestration', 'devops', 'essential', 3, 'Building minimal container images, configuring ECS task definitions and services.'),
            ('IAM Role & Security Architecture', 'security', 'recommended', 2, 'Least-privilege role policies, OIDC trust federation, and secret rotation.'),
            ('Cloud Monitoring & Alerting', 'devops', 'recommended', 2, 'CloudWatch metrics, log groups, and synthetic health checks.'),
        ]
    },
    {
        'slug': 'ui-ux-designer',
        'title': 'UI/UX Designer',
        'icon': 'figma',
        'badge': 'Product & Visual',
        'summary': 'Craft intuitive user journeys, wireframes, interactive design prototypes, and design systems for web products.',
        'overview': 'UI/UX Designers define how users perceive and interact with software. They conduct user research, map complex user flows, develop cohesive design systems with typography and color hierarchies in Figma, and evaluate usability.',
        'difficulty_level': 'Beginner',
        'average_salary_range': '₹5L - ₹15L / $70k - $125k',
        'market_demand': 'High',
        'display_order': 10,
        'primary_skills': [
            'Figma & Advanced Prototyping',
            'Design Systems & Component Variables',
            'User Journey Mapping & Wireframing',
            'Typography, Spacing & Color Theory',
            'Usability Testing & Heuristic Evaluation',
            'Web Accessibility (Color Contrast, Text Scaling)',
            'Frontend Design Handoff (HTML/CSS basics)',
        ],
        'tools_and_technologies': [
            'Figma', 'FigJam', 'Pen & Paper', 'Contrast Checker', 'HTML5', 'CSS3'
        ],
        'suggested_projects': [
            {
                'title': 'SkillSphere Complete Design System in Figma',
                'description': 'Tokens, dark-mode color palettes, button variants, and responsive modal components.',
                'difficulty': 'Intermediate'
            },
            {
                'title': 'Mobile Learning App UX Redesign & Usability Study',
                'description': 'Comprehensive user research, persona creation, wireframing, and interactive prototype testing.',
                'difficulty': 'Intermediate'
            }
        ],
        'interview_topics': [
            'Design Tokens and Figma Variable Architecture',
            'Jakob Nielsen’s 10 Usability Heuristics',
            'Balancing Aesthetic Polish with WCAG Accessibility Standards',
            'Effective Collaboration and Handoff with Frontend Developers'
        ],
        'learning_milestones': [
            {'order': 1, 'title': 'Design Fundamentals & Figma Basics', 'weeks': 2, 'topics': ['Frames', 'Vector Tools', 'Auto Layout'], 'mini_project': 'Mobile App Screen Redesign'},
            {'order': 2, 'title': 'UX Research, Personas & Wireframes', 'weeks': 3, 'topics': ['User Flows', 'Information Architecture', 'Lo-Fi Wireframes'], 'mini_project': 'Interactive Wireframe Flow'},
            {'order': 3, 'title': 'Design Systems & Component Libraries', 'weeks': 4, 'topics': ['Tokens', 'Variants', 'Micro-interactions', 'Accessibility'], 'mini_project': 'SaaS Component System'},
            {'order': 4, 'title': 'High-Fidelity Prototyping & Portfolio', 'weeks': 3, 'topics': ['Figma Smart Animate', 'Case Study Writing'], 'mini_project': 'Complete Product Case Study'}
        ],
        'skills': [
            ('Figma & Component Systems', 'frontend', 'essential', 3, 'Auto-layout, nested components, interactive states, and design tokens.'),
            ('User Flow & Wireframing', 'methodology', 'essential', 3, 'Mapping intuitive customer journeys and low-fidelity prototypes.'),
            ('Visual Hierarchy & Typography', 'frontend', 'essential', 3, 'Type scales, grid alignment, spacing rhythm, and dark-mode contrast.'),
            ('Accessibility & Contrast Standards', 'frontend', 'recommended', 2, 'WCAG 2.1 AA compliant color ratios and readable layouts.'),
            ('HTML & CSS Layout Awareness', 'frontend', 'recommended', 2, 'Understanding flexbox, grid, and DOM structure for developer handoff.'),
        ]
    },
    {
        'slug': 'fintech-analyst',
        'title': 'FinTech Analyst',
        'icon': 'trending-up',
        'badge': 'Finance & Tech',
        'summary': 'Bridge financial modeling, algorithmic trading logic, payments infrastructure, and automated market analytics.',
        'overview': 'FinTech Analysts operate at the intersection of modern finance and software engineering. They model quantitative financial assets, evaluate high-frequency transactions and payment gateways, audit blockchain ledger interactions, and build automated risk management dashboards.',
        'difficulty_level': 'Intermediate',
        'average_salary_range': '₹7L - ₹22L / $90k - $160k',
        'market_demand': 'Surging',
        'display_order': 11,
        'primary_skills': [
            'Financial Modeling & Quantitative Metrics',
            'Python for Finance (Pandas, NumPy, yfinance)',
            'Algorithmic Trading Strategies & Backtesting',
            'Payment Gateway Protocols & Ledger Accounting',
            'Risk Management & Value-at-Risk (VaR)',
            'SQL Financial Database Querying',
            'Regulatory Compliance (PCI-DSS, AML, KYC)',
        ],
        'tools_and_technologies': [
            'Python', 'Pandas', 'PostgreSQL', 'Jupyter', 'QuantConnect', 'Excel', 'Git'
        ],
        'suggested_projects': [
            {
                'title': 'Algorithmic Portfolio Backtesting Engine',
                'description': 'Python backtester evaluating moving-average cross strategies against historical equities data with Sharpe Ratio calculation.',
                'difficulty': 'Advanced'
            },
            {
                'title': 'Double-Entry Ledger & Payment Reconciliation Service',
                'description': 'ACID transaction ledger tracking multi-currency deposits, fees, and transfers with zero floating-point discrepancies.',
                'difficulty': 'Advanced'
            }
        ],
        'interview_topics': [
            'Double-Entry Bookkeeping & Preventing Floating-Point Currency Errors',
            'Sharpe Ratio, Maximum Drawdown, and Risk-Adjusted Returns',
            'Idempotency in Payment Processing and Webhook Verifications',
            'Financial Regulations and Security (PCI-DSS, Tokenization)'
        ],
        'learning_milestones': [
            {'order': 1, 'title': 'Financial Foundations & Time Value of Money', 'weeks': 2, 'topics': ['Discounted Cash Flow', 'Compound Interest', 'Financial Statements'], 'mini_project': 'Valuation Calculator'},
            {'order': 2, 'title': 'Python Quantitative Analysis', 'weeks': 4, 'topics': ['Stock Price Timeseries', 'Returns Calculation', 'Volatility'], 'mini_project': 'Market Performance Dashboard'},
            {'order': 3, 'title': 'Ledgers, Payments & FinTech Architecture', 'weeks': 3, 'topics': ['Double Entry', 'Stripe/Razorpay API', 'PCI Compliance'], 'mini_project': 'Payment Gateway Simulator'},
            {'order': 4, 'title': 'Portfolio Optimization & Risk Modeling', 'weeks': 3, 'topics': ['Monte Carlo Simulations', 'Value-at-Risk (VaR)', 'Backtesting'], 'mini_project': 'Algorithmic Trading Bot'}
        ],
        'skills': [
            ('Quantitative Financial Modeling', 'data_ai', 'essential', 3, 'Time value of money, risk metrics, Sharpe ratio, and volatility analysis.'),
            ('Python for Financial Analysis', 'backend', 'essential', 3, 'Time-series analysis with Pandas, return calculations, and plotting.'),
            ('Double-Entry Ledger & Transaction Systems', 'database', 'essential', 3, 'ACID relational modeling of financial debits and credits.'),
            ('SQL Financial Querying', 'database', 'recommended', 2, 'Rolling balances, date-trunc aggregations, and reconciliation checks.'),
            ('Payment Protocols & PCI Compliance', 'security', 'recommended', 2, 'Tokenization, webhook verification, and payment gateway flows.'),
        ]
    }
]


class Command(BaseCommand):
    help = 'Seeds all 11 curated Career Studio tracks and their granular skill requirements.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding SkillSphere Career Studio Tracks..."))

        tracks_created = 0
        requirements_created = 0

        for track_data in CURATED_TRACKS:
            skills = track_data.pop('skills')
            
            track, created = CareerTrack.objects.update_or_create(
                slug=track_data['slug'],
                defaults=track_data
            )
            if created:
                tracks_created += 1

            # Seed granular skill requirements
            for skill_name, category, importance, weight, desc in skills:
                _, req_created = CareerSkillRequirement.objects.update_or_create(
                    track=track,
                    skill_name=skill_name,
                    defaults={
                        'category': category,
                        'importance': importance,
                        'weight': weight,
                        'description': desc,
                        'benchmark_description': f"Demonstrated proficiency in {skill_name} via coursework, assessment, or project."
                    }
                )
                if req_created:
                    requirements_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {len(CURATED_TRACKS)} Career Tracks ({tracks_created} new) "
            f"and their Skill Requirements ({requirements_created} new)."
        ))
