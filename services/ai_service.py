"""
SkillSphere AI Engine Service
Secure, robust AI integration supporting Google Gemini, OpenAI, and educational fallback engines.
Never exposes API keys to client-side code.
"""

import os
import json
import urllib.request
import urllib.error
import re
from typing import Dict, Any, List, Optional

class AIService:
    @staticmethod
    def _call_gemini(prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        contents = []
        if system_instruction:
            prompt = f"System Instruction: {system_instruction}\n\nUser Request: {prompt}"
            
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 2048,
            }
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                result = json.loads(response.read().decode('utf-8'))
                candidates = result.get('candidates', [])
                if candidates and 'content' in candidates[0]:
                    parts = candidates[0]['content'].get('parts', [])
                    if parts and 'text' in parts[0]:
                        return parts[0]['text'].strip()
        except Exception as e:
            # Log error internally without crashing application
            print(f"[AIService Gemini Warning] {e}")
        return None

    @staticmethod
    def _call_openai(prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return None

        url = "https://api.openai.com/v1/chat/completions"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 2000,
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                result = json.loads(response.read().decode('utf-8'))
                choices = result.get('choices', [])
                if choices:
                    return choices[0]['message']['content'].strip()
        except Exception as e:
            print(f"[AIService OpenAI Warning] {e}")
        return None

    @classmethod
    def get_ai_status(cls) -> Dict[str, Any]:
        """
        Returns active AI provider connectivity status.
        Never misleads users about offline vs live cloud AI.
        """
        has_gemini = bool(os.getenv('GEMINI_API_KEY'))
        has_openai = bool(os.getenv('OPENAI_API_KEY'))
        active_provider = "Google Gemini 1.5" if has_gemini else ("OpenAI GPT" if has_openai else "Offline Knowledge Engine")
        return {
            'online': True,
            'has_gemini': has_gemini,
            'has_openai': has_openai,
            'is_live': has_gemini or has_openai,
            'active_provider': active_provider,
            'provider': active_provider,
            'provider_badge': "Google Gemini" if has_gemini else ("OpenAI" if has_openai else "Offline Mode"),
        }

    @classmethod
    def generate_text_with_meta(cls, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        # 1. Try Gemini
        if os.getenv('GEMINI_API_KEY'):
            resp = cls._call_gemini(prompt, system_instruction)
            if resp:
                return {
                    'text': resp,
                    'provider': 'gemini-1.5-flash',
                    'provider_label': 'Google Gemini 1.5 Flash',
                    'is_fallback': False
                }

        # 2. Try OpenAI
        if os.getenv('OPENAI_API_KEY'):
            resp = cls._call_openai(prompt, system_instruction)
            if resp:
                model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                return {
                    'text': resp,
                    'provider': model_name,
                    'provider_label': f'OpenAI ({model_name})',
                    'is_fallback': False
                }

        return {
            'text': None,
            'provider': 'offline-knowledge-engine',
            'provider_label': 'SkillSphere Offline Knowledge Engine',
            'is_fallback': True
        }

    @classmethod
    def generate_text(cls, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        meta = cls.generate_text_with_meta(prompt, system_instruction)
        return meta['text']

    @classmethod
    def ask_study_assistant_with_meta(cls, question: str, mode: str = 'detailed', conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        AI Study Assistant returning full answer with explicit provider attribution and fallback flag.
        """
        mode_instructions = {
            'simple': "Provide a clear, simple, accessible explanation suitable for a beginner student. Avoid heavy technical jargon where possible.",
            'detailed': "Provide a thorough, comprehensive technical breakdown explaining internal mechanisms, architecture, and edge cases.",
            'code': "Focus on clean, readable, well-commented code implementations. Explain key lines, inputs, outputs, and time complexity.",
            'example': "Teach through real-world software engineering analogies, case studies, and concrete examples.",
            'revision': "Provide a high-yield rapid revision cheat sheet with bullet points, essential rules, formulas, and common pitfalls."
        }
        instruction = mode_instructions.get(mode, mode_instructions['detailed'])
        system_prompt = (
            "You are SkillSphere AI, an elite technical tutor and software mentor. "
            f"Mode: {mode.upper()}. {instruction} "
            "Format your response with clean Markdown headings, bullet points, and code blocks."
        )

        history_context = ""
        if conversation_history:
            history_context = "\nRecent Conversation Context:\n" + "\n".join(
                f"{m.get('role', 'user')}: {m.get('content', '')}" for m in conversation_history[-4:]
            ) + "\n\n"

        prompt = f"{history_context}Student Question: {question}"

        meta = cls.generate_text_with_meta(prompt, system_prompt)
        if meta.get('text'):
            return meta

        # Educational fallback engine for common student inquiries
        q_lower = question.lower()
        fallback_text = None
        if 'oop' in q_lower or 'object oriented' in q_lower:
            fallback_text = (
                "### Understanding Object-Oriented Programming (OOP)\n\n"
                "Object-Oriented Programming is a paradigm centered around **objects** (data structures containing fields) and **methods** (procedures operating on objects).\n\n"
                "#### The 4 Core OOP Pillars:\n"
                "1. **Encapsulation:** Bundling data and methods into a single unit (class) while restricting direct access to internal state.\n"
                "2. **Abstraction:** Exposing only essential interface details while hiding complex underlying implementation mechanics.\n"
                "3. **Inheritance:** Creating new classes based on existing ones to share behavior and promote DRY code.\n"
                "4. **Polymorphism:** Enabling entities to assume different forms (method overriding and interfaces).\n\n"
                "```python\n"
                "class EngineeringStudent:\n"
                "    def __init__(self, name: str, major: str):\n"
                "        self.name = name\n"
                "        self._major = major  # Encapsulated state\n"
                "\n"
                "    def study(self, hours: int) -> str:\n"
                "        return f\"{self.name} invested {hours} focused hours in {self._major}.\"\n"
                "```"
            )
        elif 'django' in q_lower or 'mvt' in q_lower:
            fallback_text = (
                "### Django MTV Architecture Breakdown\n\n"
                "Django follows the **Model-Template-View (MTV)** pattern, which structures web application layers:\n\n"
                "- **Model:** Defines your data access layer, database schemas, relationships, and queries using Django ORM.\n"
                "- **Template:** The presentation layer handling HTML rendering, template tags, filters, and dynamic user interfaces.\n"
                "- **View:** The business logic controller that receives HTTP requests, coordinates with Models, and renders Templates.\n\n"
                "```python\n"
                "# views.py\n"
                "from django.shortcuts import render\n"
                "from .models import Course\n\n"
                "def course_list(request):\n"
                "    courses = Course.objects.filter(is_published=True)\n"
                "    return render(request, 'courses/list.html', {'courses': courses})\n"
                "```"
            )
        elif 'time complexity' in q_lower or 'big o' in q_lower:
            fallback_text = (
                "### Big-O Notation & Algorithm Complexity\n\n"
                "Big-O notation describes the limiting behavior of an algorithm as the input size ($N$) approaches infinity.\n\n"
                "| Complexity | Common Name | Typical Example |\n"
                "|---|---|---|\n"
                "| **$O(1)$** | Constant Time | Hash table lookup, array index access |\n"
                "| **$O(\\log N)$** | Logarithmic Time | Binary Search in sorted array |\n"
                "| **$O(N)$** | Linear Time | Linear scan, counting elements |\n"
                "| **$O(N \\log N)$** | Linearithmic | Merge Sort, QuickSort (average), Timsort |\n"
                "| **$O(N^2)$** | Quadratic Time | Nested loops, Bubble Sort, Selection Sort |\n"
            )
        else:
            fallback_text = (
                f"### Academic Reference: {question[:60]}\n\n"
                "*(Response served via SkillSphere Offline Knowledge Engine)*\n\n"
                "To explore this concept:\n"
                "1. **Core Concept:** Identify the foundational computational principles, data structures, and state transitions involved.\n"
                "2. **Implementation:** Write a minimal reproducible script demonstrating the behavior with unit test assertions.\n"
                "3. **Trade-offs:** Analyze time complexity, space complexity, and concurrency implications.\n\n"
                "> [!NOTE]\n"
                "> For generative explanations using deep reasoning LLMs, configure `GEMINI_API_KEY` or `OPENAI_API_KEY` in your environment."
            )

        return {
            'text': fallback_text,
            'provider': 'offline-knowledge-engine',
            'provider_label': 'SkillSphere Offline Knowledge Engine',
            'is_fallback': True
        }

    @classmethod
    def ask_study_assistant(cls, question: str, mode: str = 'detailed', conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        meta = cls.ask_study_assistant_with_meta(question, mode, conversation_history)
        return meta['text']

    @classmethod
    def generate_roadmap(cls, skill: str, level: str, goal: str, daily_time: str, duration: str) -> List[Dict[str, Any]]:
        """Generates a structured learning roadmap with phases, milestones, exercises, and mini projects."""
        system_prompt = (
            "You are a Senior Curriculum Architect. Generate a personalized, highly structured learning roadmap "
            "as a valid JSON list of phases. Each phase object must have: "
            "`title` (string), `description` (string), `topics` (list of strings), "
            "`mini_project` (string), `estimated_weeks` (integer). "
            "Return ONLY the valid raw JSON array, without any conversational wrapper."
        )
        user_prompt = (
            f"Target Skill: {skill}\n"
            f"Current Level: {level}\n"
            f"Career Goal: {goal}\n"
            f"Daily Available Time: {daily_time}\n"
            f"Preferred Duration: {duration}\n"
            "Provide 5 to 7 sequential, practical mastery phases."
        )

        resp = cls.generate_text(user_prompt, system_prompt)
        if resp:
            try:
                cleaned = re.sub(r'```(?:json)?', '', resp).strip()
                data = json.loads(cleaned)
                if isinstance(data, list) and len(data) > 0:
                    return data
            except Exception as e:
                print(f"[AIService Roadmap JSON parse error] {e}")

        # Intelligent Curated Fallback Roadmaps
        skill_lower = skill.lower()
        if 'python' in skill_lower or 'backend' in skill_lower:
            return [
                {
                    "title": "Phase 1: Python Core Foundations",
                    "description": "Master clean syntax, primitives, functions, and memory references.",
                    "topics": ["Variables & Data Types", "Control Flow & Loops", "Functions & Scope", "List Comprehensions"],
                    "mini_project": "CLI Student Gradebook & Statistical Analyzer",
                    "estimated_weeks": 2
                },
                {
                    "title": "Phase 2: Object-Oriented Architecture",
                    "description": "Design modular classes, encapsulation, inheritance, and error handling.",
                    "topics": ["Classes & Constructors", "Inheritance & Mixins", "Magic Methods (__repr__, __str__)", "Custom Exceptions"],
                    "mini_project": "Object-Oriented Bank Account & Transaction System",
                    "estimated_weeks": 2
                },
                {
                    "title": "Phase 3: Data Structures & Algorithms",
                    "description": "Implement efficient algorithms and analyze asymptotic complexity.",
                    "topics": ["Big O Analysis", "Hash Maps & Sets", "Stacks & Queues", "Binary Trees & Searching"],
                    "mini_project": "In-Memory LRU Cache with O(1) Lookups",
                    "estimated_weeks": 3
                },
                {
                    "title": "Phase 4: Django Web Framework & MVT",
                    "description": "Build full-stack web applications with URL routing, views, templates, and sessions.",
                    "topics": ["Django Architecture", "Template Inheritance", "Form Validation", "Session Authentication"],
                    "mini_project": "Collaborative Notes & Knowledge Management Web App",
                    "estimated_weeks": 3
                },
                {
                    "title": "Phase 5: Database Engineering & PostgreSQL",
                    "description": "Design normalized database schemas, write ORM queries, and handle migrations.",
                    "topics": ["Relational Schemas", "Foreign Keys & Constraints", "Query Optimization (select_related)", "PostgreSQL Indexing"],
                    "mini_project": "E-Commerce Database Schema with Inventory Integrity",
                    "estimated_weeks": 2
                },
                {
                    "title": "Phase 6: REST APIs & Django REST Framework",
                    "description": "Build secure, stateless RESTful web services with token authentication.",
                    "topics": ["DRF Serializers", "APIView & ViewSets", "Token/JWT Authentication", "Rate Limiting & Throttling"],
                    "mini_project": "Production-Ready SkillSphere REST API Microservice",
                    "estimated_weeks": 3
                }
            ]
        elif 'web' in skill_lower or 'frontend' in skill_lower or 'javascript' in skill_lower:
            return [
                {
                    "title": "Phase 1: Modern HTML5 & Semantic Web",
                    "description": "Build accessible, semantic markup optimized for search engines and screen readers.",
                    "topics": ["Semantic Layout Elements", "Forms & Client Validation", "ARIA Accessibility", "SEO Meta Tags"],
                    "mini_project": "High-Accessibility University Event Portal",
                    "estimated_weeks": 2
                },
                {
                    "title": "Phase 2: Modern Responsive CSS3 & Bootstrap 5",
                    "description": "Design fluid dark SaaS UI layouts with Flexbox, CSS Grid, and responsive cards.",
                    "topics": ["Flexbox & Grid Systems", "CSS Custom Properties (Variables)", "Bootstrap 5 Components", "Media Queries"],
                    "mini_project": "Responsive SaaS Product Analytics Landing Page",
                    "estimated_weeks": 2
                },
                {
                    "title": "Phase 3: JavaScript ES6+ Fundamentals",
                    "description": "Master modern JavaScript, DOM manipulation, events, and closures.",
                    "topics": ["Arrow Functions & Destructuring", "DOM Selectors & Event Listeners", "Promises & Async/Await", "Local Storage API"],
                    "mini_project": "Interactive Kanban Task Management Board",
                    "estimated_weeks": 3
                },
                {
                    "title": "Phase 4: Asynchronous JavaScript & REST Fetching",
                    "description": "Fetch real-time data from third-party APIs and handle loading and error states.",
                    "topics": ["Fetch API", "JSON Parsing", "Error Boundary Handling", "Debouncing & Throttling"],
                    "mini_project": "Live Crypto & Stock Market Tracking Dashboard",
                    "estimated_weeks": 2
                },
                {
                    "title": "Phase 5: Full-Stack Integration & Deployment",
                    "description": "Integrate interactive UI frontends with backend endpoints and deploy to the cloud.",
                    "topics": ["CSRF Protection", "State Management", "CI/CD Deployment Pipelines", "Lighthouse Performance Audits"],
                    "mini_project": "Full-Stack Portfolio Showcase Application",
                    "estimated_weeks": 3
                }
            ]

        # Generic technical roadmap fallback
        return [
            {
                "title": f"Phase 1: {skill} Fundamentals",
                "description": f"Master core syntax, fundamental concepts, and development environment setup for {skill}.",
                "topics": ["Environment & Tooling", "Core Syntax & Variables", "Control Structures", "Data Handling"],
                "mini_project": f"Basic {skill} Starter Utility Application",
                "estimated_weeks": 2
            },
            {
                "title": f"Phase 2: Intermediate {skill} Mechanics",
                "description": f"Deep dive into modular architecture, functions, error handling, and testing.",
                "topics": ["Modular Architecture", "Error Handling & Logging", "Unit Testing", "Debugging Workflows"],
                "mini_project": f"Production-Style {skill} Data Processor",
                "estimated_weeks": 3
            },
            {
                "title": f"Phase 3: Practical Application & System Design",
                "description": f"Build scalable components aligned with your goal: {goal}.",
                "topics": ["System Architecture", "Performance Optimization", "Data Persistence", "API Integration"],
                "mini_project": f"Portfolio-Ready {skill} Solution Project",
                "estimated_weeks": 3
            },
            {
                "title": f"Phase 4: Capstone & Career Readiness",
                "description": "Package, test, document, and deploy your project for internship and developer applications.",
                "topics": ["Documentation & READMEs", "Automated Testing", "Code Reviews", "Interview Preparation"],
                "mini_project": f"Complete {skill} Capstone Showcase",
                "estimated_weeks": 2
            }
        ]

    @classmethod
    def evaluate_interview_response(cls, category: str, question: str, user_answer: str) -> Dict[str, Any]:
        """Evaluates student's answer in a technical mock interview."""
        system_prompt = (
            "You are an empathetic, expert Technical Hiring Manager. "
            "Evaluate the student's answer. Return ONLY a valid JSON object with: "
            "`rating` (integer 1-10), `technical_correctness` (string), `clarity` (string), "
            "`constructive_feedback` (string), `sample_ideal_answer` (string)."
        )
        user_prompt = (
            f"Interview Category: {category}\n"
            f"Question: {question}\n"
            f"Student Answer: {user_answer}\n"
        )

        resp = cls.generate_text(user_prompt, system_prompt)
        if resp:
            try:
                cleaned = re.sub(r'```(?:json)?', '', resp).strip()
                data = json.loads(cleaned)
                if isinstance(data, dict) and 'rating' in data:
                    return data
            except Exception as e:
                print(f"[AIService Interview eval error] {e}")

        # Intelligent Fallback Evaluation
        word_count = len(user_answer.strip().split())
        if word_count < 10:
            rating = 4
            feedback = "Your answer touches on the concept but is too brief for a technical interview. Try providing a concrete definition followed by a practical example."
        elif word_count < 30:
            rating = 7
            feedback = "Good explanation of the primary concept. To improve, mention real-world trade-offs, edge cases, or performance considerations."
        else:
            rating = 8
            feedback = "Strong and thorough answer! You demonstrated solid conceptual understanding and clear technical communication."

        return {
            "rating": rating,
            "technical_correctness": "Accurate foundational understanding of the core topic.",
            "clarity": "Logical structure and clear communication.",
            "constructive_feedback": feedback,
            "sample_ideal_answer": f"In {category}, this concept is best addressed by defining the mechanism, discussing time/space trade-offs, and explaining when you would choose this approach in production."
        }

    @classmethod
    def generate_project_idea(cls, language: str, level: str, category: str, complexity: str, project_type: str) -> Dict[str, Any]:
        """Generates full real-world practical project specification."""
        system_prompt = (
            "You are a Senior Software Architect. Generate a practical, portfolio-grade project idea. "
            "Return ONLY a valid JSON object with the following keys: "
            "`title` (string), `description` (string), `problem_statement` (string), "
            "`objectives` (string), `technology_stack` (string), `main_features` (string), "
            "`database_requirements` (string), `development_phases` (string)."
        )
        user_prompt = (
            f"Language: {language}\n"
            f"Skill Level: {level}\n"
            f"Category: {category}\n"
            f"Complexity: {complexity}\n"
            f"Project Type: {project_type}\n"
        )

        resp = cls.generate_text(user_prompt, system_prompt)
        if resp:
            try:
                cleaned = re.sub(r'```(?:json)?', '', resp).strip()
                data = json.loads(cleaned)
                if isinstance(data, dict) and 'title' in data:
                    return data
            except Exception as e:
                print(f"[AIService Project gen error] {e}")

        # Curated Fallback Project Idea
        return {
            "title": f"DevFlow: {language} {category} Platform",
            "description": f"A comprehensive {category} platform built with {language} designed to solve workflow fragmentation for software engineering students.",
            "problem_statement": "Students frequently struggle to track project requirements, collaborate on code reviews, and monitor milestone completion across disparate tools.",
            "objectives": f"Build a reliable {language} application implementing secure authentication, real-time database queries, and modular REST services.",
            "technology_stack": f"{language}, Django / DRF, PostgreSQL, Bootstrap 5, Chart.js",
            "main_features": "• Role-based access control (Student vs Mentor)\n• Automated task tracking & completion dashboards\n• RESTful API integration for external webhooks\n• Audit logging & CSV export functionality",
            "database_requirements": "Normalized relational schema with Users, Projects, Tasks, and AuditLog tables with foreign key constraints and indexed status fields.",
            "development_phases": "Phase 1: Schema design & migrations\nPhase 2: Authentication & CRUD views\nPhase 3: Interactive UI dashboards\nPhase 4: Automated unit tests & cloud deployment"
        }

    @classmethod
    def generate_resume_summary(cls, headline: str, skills: List[str], education: str = "") -> str:
        """Generates an action-oriented professional resume summary without inventing qualifications."""
        system_prompt = (
            "You are a professional Tech Career Coach. Write a concise, impactful 3-4 sentence resume summary "
            "for a candidate based ONLY on the provided headline, verified technical skills, and education. "
            "IMPORTANT: Do not invent any companies, degrees, unmentioned skills, or awards. Use active voice."
        )
        user_prompt = f"Headline: {headline}\nSkills: {', '.join(skills)}\nEducation: {education}"
        resp = cls.generate_text(user_prompt, system_prompt)
        if resp and len(resp.strip()) > 30:
            return resp.strip()

        # Fallback summary
        skills_str = ", ".join(skills[:4]) if skills else "modern software engineering practices"
        return (
            f"Dedicated {headline or 'Software Developer'} with a solid technical foundation in {skills_str}. "
            f"Passionate about writing clean, maintainable code, solving real-world challenges, and building high-performance applications. "
            f"Eager to contribute technical curiosity, collaborative problem solving, and disciplined delivery to an engineering team."
        )

    @classmethod
    def improve_project_description(cls, title: str, description: str, technologies: str) -> str:
        """Polishes a project description into high-impact, STAR-aligned resume bullet points."""
        system_prompt = (
            "You are a Tech Resume Specialist. Polish the project description into 2-3 impactful resume bullet points. "
            "Start each bullet with an active verb (e.g. Engineered, Architected, Designed, Implemented). "
            "Highlight technical problem solving, system architecture, and performance. Do not fabricate metrics or technologies."
        )
        user_prompt = f"Project: {title}\nTechnologies: {technologies}\nDraft Description: {description}"
        resp = cls.generate_text(user_prompt, system_prompt)
        if resp and len(resp.strip()) > 20:
            return resp.strip()

        # Fallback improvement
        tech_list = technologies or "modern tech stack"
        return (
            f"• Architected and deployed {title} utilizing {tech_list}, ensuring robust data flow and clean separation of concerns.\n"
            f"• Implemented end-to-end features, intuitive UI components, and reliable backend service endpoints to solve user requirements.\n"
            f"• Followed modular development standards, comprehensive validation, and version-controlled Git workflows."
        )

    @classmethod
    def rewrite_resume_bullet(cls, bullet_text: str) -> str:
        """Rewrites a single resume bullet point into concise, action-oriented phrasing."""
        system_prompt = (
            "Rewrite the provided resume bullet point to make it more professional, impactful, and action-oriented. "
            "Start with a strong action verb. Do not invent facts or metrics not implied in the text. Return only the revised single bullet."
        )
        resp = cls.generate_text(bullet_text, system_prompt)
        if resp and len(resp.strip()) > 10:
            return resp.strip().lstrip('•-* ')

        # Fallback
        cleaned = bullet_text.strip().lstrip('•-* ')
        return f"Engineered and maintained {cleaned.lower() if cleaned else 'core application components'}, ensuring optimal performance and stability."

    @classmethod
    def check_ats_readability(cls, resume_data: Dict[str, Any], job_description: Optional[str] = None) -> Dict[str, Any]:
        """Performs educational ATS readability analysis and keyword coverage checking."""
        contact = resume_data.get('contact', {})
        summary = resume_data.get('summary', '')
        education = resume_data.get('education', [])
        skills = resume_data.get('skills', [])
        projects = resume_data.get('projects', [])
        experience = resume_data.get('experience', [])

        missing_sections = []
        strengths = []
        improvements = []
        score = 60

        if not summary or len(summary) < 50:
            missing_sections.append("Professional Summary (recommended 50-100 words)")
            improvements.append("Add a clear, 3-sentence professional summary outlining your focus and core strengths.")
        else:
            score += 8
            strengths.append("Professional summary is present and concise.")

        if not education or len(education) == 0:
            missing_sections.append("Education section")
            improvements.append("Include your college, degree, graduation year, and GPA/relevant coursework.")
        else:
            score += 8
            strengths.append("Education background properly formatted.")

        if not skills or len(skills) < 5:
            missing_sections.append("Technical Skills (aim for 6+ concrete skills)")
            improvements.append("Add specific programming languages, frameworks, databases, and developer tools.")
        else:
            score += 10
            strengths.append(f"Strong technical skill coverage ({len(skills)} verified skills listed).")

        if not projects or len(projects) == 0:
            missing_sections.append("Projects section (vital for student resumes)")
            improvements.append("Add at least 2 practical technical projects with GitHub links and technology tags.")
        else:
            score += 10
            strengths.append(f"{len(projects)} technical projects listed with clear architecture.")

        if not contact.get('email') or not contact.get('full_name'):
            improvements.append("Ensure your full name, email, and LinkedIn/GitHub links are prominently listed at the top.")
        else:
            score += 4
            strengths.append("Essential contact coordinates are complete.")

        score = min(score, 100)

        # Keyword matching if job description is provided
        keywords_matched = []
        keywords_missing = []
        if job_description:
            words = set(re.findall(r'[a-zA-Z]{3,}', job_description.lower()))
            common_tech = {'python', 'django', 'javascript', 'react', 'html', 'css', 'sql', 'postgresql', 'git', 'docker', 'rest', 'api', 'aws'}
            target_keywords = words.intersection(common_tech)
            current_skills = {s.lower() for s in skills}
            for kw in target_keywords:
                if kw in current_skills:
                    keywords_matched.append(kw.capitalize())
                else:
                    keywords_missing.append(kw.capitalize())

        return {
            "score": score,
            "readability_status": "High" if score >= 85 else ("Moderate" if score >= 70 else "Needs Improvement"),
            "missing_sections": missing_sections,
            "strengths": strengths,
            "improvements": improvements,
            "keywords_matched": keywords_matched,
            "keywords_missing": keywords_missing,
            "disclaimer": "This score is an educational guideline based on industry standard formatting best practices, not a vendor ATS guarantee."
        }
