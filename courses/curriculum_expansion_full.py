"""
Comprehensive Curriculum Expansion Module for SkillSphere.
Defines Modules and Lessons (orders 1..16) across 6 learning stages:
- Module 1 (Lessons 1-4): Level 1 - Foundations
- Module 2 (Lessons 5-8): Level 2 - Core Skills
- Module 3 (Lessons 9-12): Level 3 - Intermediate Mastery
- Module 4 (Lessons 13-14): Level 4 - Advanced & Performance
- Module 4 (Lessons 15-16): Level 5 - Practical Deliverable
- Module 4 Gateway: Level 6 - Final Assessments (Final Quiz & Final Mock Exam)
"""

# New Course Definitions
NEW_COURSES_DATA = [
    {
        'title': 'Modern JavaScript & Asynchronous Programming',
        'slug': 'modern-javascript-deep-dive',
        'category': 'programming',
        'difficulty': 'Beginner',
        'instructor_name': 'Marcus Vance',
        'instructor_title': 'Senior Frontend Architect',
        'estimated_duration': '12 hours',
        'thumbnail_url': 'https://images.unsplash.com/photo-1579468118864-ddb62129e11d?auto=format&fit=crop&w=800&q=80',
        'description': 'Master modern ECMAScript standards (ES6+), event loop concurrency, promises, async/await, DOM APIs, and modular JavaScript architecture.',
        'short_description': 'Master modern JavaScript, the event loop, async/await, and browser DOM engineering.',
        'learning_objectives': "Master modern ES6+ syntax, scope, and closures\nUnderstand the JavaScript Event Loop, microtasks, and macrotasks\nWrite asynchronous code with Promises and async/await\nBuild dynamic browser applications manipulating the DOM safely"
    },
    {
        'title': 'Modern React & Frontend Engineering',
        'slug': 'modern-react-frontend-engineering',
        'category': 'web-development',
        'difficulty': 'Intermediate',
        'instructor_name': 'Elena Chen',
        'instructor_title': 'Staff UI Engineer',
        'estimated_duration': '14 hours',
        'thumbnail_url': 'https://images.unsplash.com/photo-1633356122544-f134324a6cee?auto=format&fit=crop&w=800&q=80',
        'description': 'Comprehensive modern React 18+ courseware. Covers JSX, functional components, hooks (useState, useEffect, useMemo, useCallback), Context API, and state machines.',
        'short_description': 'Build responsive, accessible, and high-performance user interfaces with React 18+.',
        'learning_objectives': "Master React 18 component lifecycle and fiber reconciliation\nImplement custom hooks and performance memoization\nManage global client state with Context API and state machines\nBuild and deploy a production-grade single-page application"
    },
    {
        'title': 'Software Engineering, Git & GitHub Workflows',
        'slug': 'software-engineering-git-github',
        'category': 'career-development',
        'difficulty': 'Beginner',
        'instructor_name': 'David Kim',
        'instructor_title': 'Principal DevOps & Release Engineer',
        'estimated_duration': '10 hours',
        'thumbnail_url': 'https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?auto=format&fit=crop&w=800&q=80',
        'description': 'Master professional software engineering practices: distributed version control with Git, branching strategies, interactive rebasing, merge conflict resolution, CI/CD pipelines, and pull request reviews.',
        'short_description': 'Learn industry-standard Git workflows, PR reviews, CI/CD, and release engineering.',
        'learning_objectives': "Understand Git internal DAG object storage (blobs, trees, commits, tags)\nExecute feature branching, rebasing, and merge resolution\nAutomate workflows with GitHub Actions CI/CD pipelines\nConduct professional peer code reviews and maintain changelogs"
    },
    {
        'title': 'C Systems Programming & Memory Architecture',
        'slug': 'c-systems-programming-memory',
        'category': 'cs-fundamentals',
        'difficulty': 'Intermediate',
        'instructor_name': 'Prof. Dev Patel',
        'instructor_title': 'Systems & Compilers Researcher',
        'estimated_duration': '16 hours',
        'thumbnail_url': 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80',
        'description': 'Low-level systems programming in C. Master raw memory layouts, pointer arithmetic, dynamic heap management (malloc/free), stack frames, structs, and POSIX system calls.',
        'short_description': 'Master C pointers, manual memory allocation, POSIX system calls, and hardware architecture.',
        'learning_objectives': "Understand computer memory architecture, stack frames, and heap allocation\nMaster pointers, double pointers, pointer arithmetic, and void pointers\nPrevent buffer overflows, use-after-free bugs, and memory leaks with Valgrind\nInterface with the Linux kernel using POSIX system calls (read, write, fork, pipe)"
    }
]
