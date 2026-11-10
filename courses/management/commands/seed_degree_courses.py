import json
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from courses.models import (
    Category, Course, CourseModule, CourseAssessment, CourseAssessmentQuestion
)
from learning.models import Lesson


class Command(BaseCommand):
    help = 'Seeds 50 comprehensive courses across BBA, MBA, MTech, BTech, BCA, BSc, BA, and BCom degrees with 16 lessons each.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting 50 Degree Courses Seeding for SkillSphere...'))

        # ---------------------------------------------------------------------
        # 1. Categories
        # ---------------------------------------------------------------------
        categories_data = [
            {
                'name': 'Management & Business Leadership',
                'slug': 'management-business',
                'description': 'Product strategy, corporate finance, marketing management, supply chain operations, and venture capital.',
                'icon': 'briefcase'
            },
            {
                'name': 'Engineering & Emerging Technology',
                'slug': 'engineering-tech',
                'description': 'VLSI design, distributed systems, advanced cybersecurity, embedded robotics, computer vision, and HPC.',
                'icon': 'cpu'
            },
            {
                'name': 'Computer Applications & IT',
                'slug': 'computer-applications',
                'description': 'Enterprise Java, mobile development with Flutter, Linux administration, software QA, and computer networks.',
                'icon': 'terminal'
            },
            {
                'name': 'Commerce, Banking & Taxation',
                'slug': 'commerce-finance',
                'description': 'Financial accounting, corporate taxation, GST compliance, cost accounting, banking operations, and equity research.',
                'icon': 'credit-card'
            },
            {
                'name': 'Applied Sciences & Mathematics',
                'slug': 'applied-sciences',
                'description': 'Bioinformatics, chemometrics, environmental GIS, quantum mechanics, cell biology, and applied probability.',
                'icon': 'activity'
            },
            {
                'name': 'Humanities, Arts & Communication',
                'slug': 'humanities-arts',
                'description': 'Digital journalism, technical writing, public policy, cognitive psychology, international relations, and graphic design.',
                'icon': 'feather'
            },
        ]

        cat_objects = {}
        for cdata in categories_data:
            cat, _ = Category.objects.update_or_create(
                slug=cdata['slug'],
                defaults={
                    'name': cdata['name'],
                    'description': cdata['description'],
                    'icon': cdata['icon']
                }
            )
            cat_objects[cat.slug] = cat
            self.stdout.write(self.style.SUCCESS(f'Category ready: {cat.name} ({cat.slug})'))

        # ---------------------------------------------------------------------
        # 2. Courses Specification (50 Courses x 4 Modules x 4 Lessons = 800 Lessons)
        # ---------------------------------------------------------------------
        courses_data = self.get_fifty_courses_data()

        total_courses_seeded = 0
        total_lessons_seeded = 0

        for c_idx, cdata in enumerate(courses_data, start=1):
            category = cat_objects.get(cdata['category_slug'])
            if not category:
                category = Category.objects.filter(slug=cdata['category_slug']).first()
                if not category:
                    category = list(cat_objects.values())[0]

            course, _ = Course.objects.update_or_create(
                slug=cdata['slug'],
                defaults={
                    'title': cdata['title'],
                    'description': cdata['description'],
                    'short_description': cdata['short_description'],
                    'category': category,
                    'difficulty': cdata.get('difficulty', 'Beginner'),
                    'instructor_name': cdata.get('instructor_name', 'Prof. SkillSphere Academic Faculty'),
                    'instructor_title': cdata.get('instructor_title', 'Department Chair & Senior Curriculum Fellow'),
                    'estimated_duration': cdata.get('estimated_duration', '14 hours'),
                    'thumbnail_url': cdata.get('thumbnail_url', 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=800&q=80'),
                    'learning_objectives': cdata.get('learning_objectives', ''),
                    'prerequisites': cdata.get('prerequisites', ''),
                    'curriculum_version': 2,
                    'is_published': True,
                }
            )

            # Modules and Lessons
            lesson_counter = 1
            for m_idx, mdata in enumerate(cdata['modules'], start=1):
                module, _ = CourseModule.objects.update_or_create(
                    course=course,
                    order=mdata.get('order', m_idx),
                    defaults={
                        'title': mdata['title'],
                        'description': mdata.get('description', f"Module {m_idx} comprehensive study units and concepts.")
                    }
                )

                for ldata in mdata['lessons']:
                    l_order = ldata[0]
                    l_topic = ldata[1]
                    l_title = ldata[2]
                    l_dur = ldata[3]
                    l_vid = ldata[4]
                    l_content = ldata[5]
                    l_takeaways = ldata[6]
                    l_mistakes = ldata[7]

                    video_url = f"https://www.youtube.com/watch?v={l_vid}"

                    Lesson.objects.update_or_create(
                        course=course,
                        lesson_order=l_order,
                        defaults={
                            'module': module,
                            'chapter_name': mdata['title'],
                            'title': f"{l_order}. {l_title}",
                            'estimated_minutes': l_dur,
                            'video_url': video_url,
                            'video_duration_seconds': l_dur * 60,
                            'video_type': 'optional',
                            'content': l_content,
                            'key_takeaways': l_takeaways,
                            'common_mistakes': l_mistakes,
                            'curriculum_version': 2,
                        }
                    )
                    lesson_counter += 1
                    total_lessons_seeded += 1

            # Optional Final Quiz Assessment (+10% extra credit)
            quiz, _ = CourseAssessment.objects.update_or_create(
                course=course,
                assessment_type='final_quiz',
                defaults={
                    'title': f"{course.title}: Final Comprehensive Quiz",
                    'description': "100% Optional knowledge evaluation. Pass with 70% or higher to boost your course progress by up to +10%.",
                    'duration_minutes': 25,
                    'passing_percentage': 70,
                    'max_attempts': 5,
                    'is_active': True,
                }
            )

            # Optional Final Mock Test Assessment (+10% extra credit)
            mock, _ = CourseAssessment.objects.update_or_create(
                course=course,
                assessment_type='final_mock',
                defaults={
                    'title': f"{course.title}: Final Technical Examination",
                    'description': "100% Optional final exam. Test your real-world problem solving to earn up to +10% bonus progress.",
                    'duration_minutes': 35,
                    'passing_percentage': 70,
                    'max_attempts': 5,
                    'is_active': True,
                }
            )

            # Seed 5 high-yield multiple choice questions for each assessment if not populated
            self.seed_assessment_questions(quiz, cdata)
            self.seed_assessment_questions(mock, cdata)

            total_courses_seeded += 1
            if c_idx % 5 == 0 or c_idx == len(courses_data):
                self.stdout.write(self.style.SUCCESS(f"[{c_idx}/50] Seeded: {course.title} (16 lessons ready)"))

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Successfully seeded {total_courses_seeded} degree courses and {total_lessons_seeded} academic lessons!"
        ))

    def seed_assessment_questions(self, assessment, cdata):
        """Creates 5 multiple choice questions for the assessment if none exist."""
        if assessment.questions.exists():
            return

        q_templates = [
            (
                f"What is the foundational objective emphasized throughout {cdata['title']}?",
                [
                    "To apply structured theoretical models to solve real-world industry problems.",
                    "To memorize superficial terminology without practical application.",
                    "To replace human analytical reasoning with unvalidated automation.",
                    "To bypass standard academic and regulatory compliance frameworks."
                ],
                0,
                f"{cdata['title']} centers on applying rigorous analytical frameworks to real-world domain challenges."
            ),
            (
                f"Which key methodology is central to effective execution in this domain?",
                [
                    "Ad-hoc decision-making based purely on intuition.",
                    "Data-driven analysis, continuous feedback loops, and structured validation.",
                    "Rigid adherence to obsolete historical assumptions.",
                    "Avoiding cross-functional collaboration and stakeholder communication."
                ],
                1,
                "Modern practice mandates empirical data analysis and structured feedback loops."
            ),
            (
                "When analyzing strategic trade-offs, what is the primary consideration for practitioners?",
                [
                    "Maximizing short-term vanity metrics at the expense of long-term sustainability.",
                    "Balancing risk, resource efficiency, and measurable long-term value creation.",
                    "Eliminating all contingency buffers and risk mitigation mechanisms.",
                    "Ignoring external market dynamics and regulatory constraints."
                ],
                1,
                "Sustainable practice requires balancing risk, efficiency, and long-term value creation."
            ),
            (
                "Which common pitfall should students and professionals actively avoid?",
                [
                    "Premature optimization and scaling prior to validating core hypotheses.",
                    "Testing assumptions against empirical real-world evidence.",
                    "Documenting operational procedures and architectural decisions.",
                    "Conducting regular performance and risk evaluations."
                ],
                0,
                "Premature scaling without validating baseline assumptions is a critical failure pattern."
            ),
            (
                "How does continuous learning and modern tool adoption impact performance in this discipline?",
                [
                    "It has negligible impact on operational outcomes.",
                    "It significantly enhances adaptability, decision quality, and competitive advantage.",
                    "It introduces unnecessary complexity without tangible benefit.",
                    "It diminishes the importance of core foundational principles."
                ],
                1,
                "Embracing modern tools while mastering core fundamentals drives sustainable competitive advantage."
            )
        ]

        ans_map = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        for order, (q_text, options, correct_idx, exp) in enumerate(q_templates, start=1):
            CourseAssessmentQuestion.objects.update_or_create(
                assessment=assessment,
                order=order,
                defaults={
                    'question_text': q_text,
                    'topic': 'Core Concepts',
                    'option_a': options[0],
                    'option_b': options[1],
                    'option_c': options[2],
                    'option_d': options[3],
                    'correct_answer': ans_map.get(correct_idx, 'A'),
                    'explanation': exp,
                }
            )

    def get_fifty_courses_data(self):
        """Generates detailed specifications for all 50 degree courses."""
        courses = []

        # ---------------------------------------------------------------------
        # DEGREE 1: BBA & MBA (10 Courses)
        # ---------------------------------------------------------------------
        bba_mba = [
            (
                "Strategic Management & Competitive Advantage",
                "strategic-management-mba",
                "management-business",
                "Intermediate",
                "Prof. Arvind Subramanian",
                "Professor of Strategic Leadership, IIM Faculty Alum",
                "15 hours",
                "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80",
                "Master Porter's Five Forces, Blue Ocean strategy, core competencies, and strategic execution for executive leadership.",
                "Target Degree: MBA / BBA. A masterclass in strategic leadership. Learn to analyze macro and industry environments, formulate cost leadership and differentiation strategies, evaluate M&A decisions, and lead enterprise change management.",
                "Conduct external industry analysis using Porter's Five Forces and PESTEL\nMap internal core competencies with VRIO framework\nFormulate competitive cost-leadership and differentiation strategies\nEvaluate mergers, acquisitions, and strategic joint ventures\nLead organizational transformation and change management initiatives",
                "Introductory understanding of business organizations and corporate structures\nBasic familiarity with financial statements",
                [
                    ("Module 1: Environmental & Industry Analysis", [
                        (1, "Strategic Intent", "Strategic Intent, Vision, Mission & Corporate Values", 25, "sPh6S4wIqC4"),
                        (2, "External Environment", "Macro-Environmental PESTEL Analysis & Mega-Trends", 25, "k8lSgL32_5U"),
                        (3, "Industry Competition", "Porter's Five Forces Framework & Industry Profitability", 30, "Z52G4y1o6Jc"),
                        (4, "Strategic Groups", "Strategic Group Mapping & Competitor Intelligence", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Internal Analysis & Core Competencies", [
                        (5, "Resource-Based View", "The Resource-Based View (RBV) of the Firm", 25, "97H0a3Xl-1M"),
                        (6, "VRIO Framework", "VRIO Framework: Assessing Sustainable Competitive Advantage", 30, "1P8j3J9gE0I"),
                        (7, "Value Chain", "Porter's Value Chain Analysis: Primary & Support Activities", 25, "m2XyE_K0918"),
                        (8, "Benchmarking", "Benchmarking, Dynamic Capabilities & Strategic Flexibility", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Business & Corporate Level Strategies", [
                        (9, "Generic Strategies", "Porter's Generic Strategies: Cost Leadership vs Differentiation", 25, "zS8Y7T36J80"),
                        (10, "Blue Ocean Strategy", "Blue Ocean Strategy: Value Innovation & Canvas Mapping", 30, "6p873K6G5sQ"),
                        (11, "Corporate Diversification", "Corporate Diversification: Related vs Unrelated Strategies", 25, "vX9vFh33p54"),
                        (12, "Mergers & Acquisitions", "Mergers, Acquisitions, Strategic Alliances & Joint Ventures", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Strategy Execution & Governance", [
                        (13, "Balanced Scorecard", "The Balanced Scorecard: Translating Strategy into Operational Goals", 30, "9bZkp7q19f0"),
                        (14, "Organizational Structure", "Aligning Organizational Structure & Incentive Systems", 25, "kJQP7kiw5Fk"),
                        (15, "Strategic Change", "Leading Strategic Change: Kotter's 8-Step Transformation Model", 25, "L_LUpnjgPso"),
                        (16, "Corporate Governance", "Corporate Governance, Ethics & Environmental Social Governance (ESG)", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Corporate Finance, Capital Budgeting & Valuation",
                "corporate-finance-valuation",
                "management-business",
                "Advanced",
                "Dr. Rajesh Singhania, CFA",
                "Director of Financial Economics & Corporate Valuation",
                "16 hours",
                "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80",
                "Master NPV, IRR, WACC, capital structure theories, dividend policy, and discounted cash flow (DCF) enterprise valuation.",
                "Target Degree: MBA / BBA. In-depth corporate finance and corporate valuation. Learn to evaluate investment proposals using DCF, calculate cost of capital (WACC), optimize debt-to-equity leverage, and value operating companies.",
                "Calculate discounted cash flow metrics (NPV, IRR, Payback Period)\nEstimate Weighted Average Cost of Capital (WACC) using CAPM\nOptimize debt-to-equity capital structure under Modigliani-Miller theorems\nConduct sensitivity and scenario analysis on corporate investments\nBuild multi-stage DCF financial valuation models in Excel",
                "Basic accounting knowledge (Income Statement, Balance Sheet, Cash Flow)\nFoundations of business mathematics",
                [
                    ("Module 1: Time Value of Money & Cash Flows", [
                        (1, "TVM Foundations", "Time Value of Money: Compounding, Discounting & Perpetuities", 25, "sPh6S4wIqC4"),
                        (2, "Cash Flow Forecasting", "Forecasting Free Cash Flow to Firm (FCFF) vs Equity (FCFE)", 30, "k8lSgL32_5U"),
                        (3, "Capital Budgeting Rules", "Net Present Value (NPV) vs Internal Rate of Return (IRR)", 30, "Z52G4y1o6Jc"),
                        (4, "Project Decisions", "Profitability Index, Modified IRR & Mutually Exclusive Projects", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Risk, Return & Cost of Capital", [
                        (5, "Risk & Return", "Portfolio Risk, Covariance & Modern Portfolio Theory", 25, "97H0a3Xl-1M"),
                        (6, "CAPM Theory", "The Capital Asset Pricing Model (CAPM) & Beta Estimation", 30, "1P8j3J9gE0I"),
                        (7, "Cost of Debt & Equity", "Estimating Cost of Debt, Credit Spreads & Cost of Equity", 25, "m2XyE_K0918"),
                        (8, "WACC Calculation", "Weighted Average Cost of Capital (WACC) Modeling", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Capital Structure & Payout Policy", [
                        (9, "Capital Structure Theory", "Modigliani-Miller Propositions: With and Without Taxes", 30, "zS8Y7T36J80"),
                        (10, "Financial Distress", "Trade-off Theory, Pecking Order Theory & Financial Distress Costs", 25, "6p873K6G5sQ"),
                        (11, "Dividend Policy", "Cash Dividends vs Share Repurchases: Signaling & Agency Theory", 25, "vX9vFh33p54"),
                        (12, "Working Capital", "Operating Cycle, Cash Conversion Cycle & Liquidity Management", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Enterprise Valuation & M&A", [
                        (13, "DCF Modeling", "Discounted Cash Flow (DCF) Valuation: Two-Stage Growth Model", 35, "9bZkp7q19f0"),
                        (14, "Comparable Multiples", "Trading Multiples (EV/EBITDA, P/E) & Transaction Precedents", 30, "kJQP7kiw5Fk"),
                        (15, "M&A Economics", "Valuing Synergies, Accretion/Dilution & LBO Structures", 30, "L_LUpnjgPso"),
                        (16, "Corporate Restructuring", "Spin-offs, Carve-outs & Financial Distress Restructuring", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Marketing Management & Consumer Brand Positioning",
                "marketing-management-branding",
                "management-business",
                "Beginner",
                "Prof. Meenakshi Sundaram",
                "Brand Consultant & Adjunct Professor of Marketing",
                "13 hours",
                "https://images.unsplash.com/photo-1557804506-669a67965ba0?auto=format&fit=crop&w=800&q=80",
                "Master STP frameworks, customer lifetime value, pricing psychology, integrated communications, and brand equity.",
                "Target Degree: BBA / MBA. Core marketing management course. Learn segmentation, targeting, and positioning (STP), customer decision journeys, pricing strategies, multi-channel distribution, and building brand equity.",
                "Formulate comprehensive STP (Segmentation, Targeting, Positioning) matrices\nAnalyze buyer behavior and cognitive decision stages\nExecute value-based, psychological, and dynamic pricing strategies\nDesign omnichannel integrated marketing communication (IMC) plans\nMeasure brand resonance, customer loyalty, and Customer Lifetime Value (CLV)",
                "No technical prerequisites required\nCuriosity regarding consumer behavior and business models",
                [
                    ("Module 1: Marketing Strategy & Customer Understanding", [
                        (1, "Marketing Concepts", "Evolution of Marketing: Production to Customer-Centricity", 20, "sPh6S4wIqC4"),
                        (2, "Market Segmentation", "Demographic, Psychographic & Behavioral Segmentation", 25, "k8lSgL32_5U"),
                        (3, "Targeting Decisions", "Target Market Attractiveness & Segment Sizing", 25, "Z52G4y1o6Jc"),
                        (4, "Brand Positioning", "Developing Distinctive Value Propositions & Positioning Statements", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Buyer Behavior & Product Decisions", [
                        (5, "Consumer Decision Journey", "The Consumer Decision Journey & Cognitive Biases", 25, "97H0a3Xl-1M"),
                        (6, "B2B vs B2C Buying", "Organizational Buying Center & B2B Procurement Workflows", 25, "1P8j3J9gE0I"),
                        (7, "Product Life Cycle", "Product Levels, Product Line Management & PLC Dynamics", 25, "m2XyE_K0918"),
                        (8, "New Product Development", "The Stage-Gate Innovation Process & Concept Testing", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Pricing & Distribution Architecture", [
                        (9, "Pricing Psychology", "Cost-Plus, Value-Based & Psychological Pricing Models", 25, "zS8Y7T36J80"),
                        (10, "Dynamic Pricing", "Yield Management, Price Discrimination & Freemium Economics", 25, "6p873K6G5sQ"),
                        (11, "Marketing Channels", "Direct vs Indirect Distribution & Channel Conflict Management", 25, "vX9vFh33p54"),
                        (12, "Omnichannel Retailing", "Omnichannel Experience Design & Supply Partner Collaboration", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Integrated Communications & Brand Equity", [
                        (13, "IMC Strategy", "Integrated Marketing Communications (IMC) Mix & Budget Allocation", 25, "9bZkp7q19f0"),
                        (14, "Digital & Social Media", "Content Marketing, Influencer Partnerships & Viral Loops", 25, "kJQP7kiw5Fk"),
                        (15, "Brand Equity Models", "Keller's Brand Resonance Pyramid & Aaker's Equity Assets", 30, "L_LUpnjgPso"),
                        (16, "Marketing Analytics", "Calculating CAC, LTV, Net Promoter Score (NPS) & Marketing ROI", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Human Resource Management & Organizational Dynamics",
                "human-resource-management-org-dynamics",
                "management-business",
                "Beginner",
                "Dr. Pallavi Deshmukh",
                "Chief People Officer & Faculty of Organizational Behavior",
                "12 hours",
                "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=800&q=80",
                "Master modern talent acquisition, performance appraisals, 360 feedback, compensation modeling, and organizational culture.",
                "Target Degree: BBA / MBA. Strategic people management and organizational behavior. Learn competency mapping, behavioral interviewing, compensation benchmarks, employee retention, and fostering inclusive culture.",
                "Design job descriptions and competency frameworks for recruitment\nConduct behavioral interviews using the STAR methodology\nImplement 360-degree performance appraisal and OKR tracking systems\nStructure fair compensation, incentive packages, and employee benefits\nResolve workplace conflicts and drive inclusive organizational culture",
                "General interest in organizational behavior and management leadership",
                [
                    ("Module 1: Strategic Workforce Planning & Recruitment", [
                        (1, "Strategic HRM", "Strategic Human Resource Management & Organizational Goals", 20, "sPh6S4wIqC4"),
                        (2, "Workforce Planning", "Forecasting Talent Demand, Succession Planning & Job Design", 25, "k8lSgL32_5U"),
                        (3, "Talent Sourcing", "Modern Talent Sourcing Channels, Employer Branding & ATS", 25, "Z52G4y1o6Jc"),
                        (4, "Behavioral Interviewing", "Structured Competency Interviews & The STAR Method", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Training, Development & Onboarding", [
                        (5, "Employee Onboarding", "Designing High-Retention Onboarding & Socialization Programs", 20, "97H0a3Xl-1M"),
                        (6, "Training Needs Analysis", "Training Needs Assessment (TNA) & Learning Architectures", 25, "1P8j3J9gE0I"),
                        (7, "Leadership Development", "Executive Coaching, Mentorship & High-Potential Programs", 25, "m2XyE_K0918"),
                        (8, "Kirkpatrick Model", "Measuring Training Effectiveness: The Kirkpatrick 4-Level Model", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Performance Management & Compensation", [
                        (9, "Performance Appraisals", "360-Degree Feedback, MBO & Objective Performance Review", 25, "zS8Y7T36J80"),
                        (10, "Continuous Feedback", "Shifting from Annual Reviews to Continuous Coaching & OKRs", 25, "6p873K6G5sQ"),
                        (11, "Compensation Architecture", "Job Evaluation, Pay Bands, Stock Options & Executive Perquisites", 30, "vX9vFh33p54"),
                        (12, "Incentive Systems", "Bonus Schemes, Sales Commissions & Total Rewards Strategy", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Organizational Dynamics & Labor Relations", [
                        (13, "Organizational Culture", "Schein's Culture Model: Artifacts, Values & Underlying Assumptions", 25, "9bZkp7q19f0"),
                        (14, "Conflict Management", "Conflict Resolution Styles, Negotiation & Mediation", 25, "kJQP7kiw5Fk"),
                        (15, "Labor Law & Compliance", "Industrial Relations, Labor Codes, POSH & Fair Labor Standards", 30, "L_LUpnjgPso"),
                        (16, "Future of Work", "Managing Remote Teams, Hybrid Collaboration & AI in HR", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Supply Chain Management, Logistics & Lean Operations",
                "supply-chain-logistics-operations",
                "management-business",
                "Intermediate",
                "Prof. Vikramaditya Rao",
                "Supply Chain Architect & Operations Fellow",
                "15 hours",
                "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=800&q=80",
                "Master demand forecasting, inventory control (EOQ/Safety Stock), global logistics, procurement, and Six Sigma operations.",
                "Target Degree: MBA / BBA. End-to-end supply chain and operations management. Learn push vs pull manufacturing, inventory optimization, supplier scorecards, warehouse logistics, and Lean Six Sigma process improvements.",
                "Calculate Economic Order Quantity (EOQ), reorder points, and safety stock\nForecast customer demand using exponential smoothing and moving averages\nEvaluate multi-tier supplier sourcing, contracts, and vendor scorecards\nOptimize warehouse fulfillment, Cross-Docking, and 3PL/4PL logistics\nImplement Lean methodologies (5S, Kaizen, Kanban) to eliminate waste",
                "Basic algebra and understanding of business operations",
                [
                    ("Module 1: Supply Chain Strategy & Demand Forecasting", [
                        (1, "SCM Foundations", "Understanding Supply Chain Flows, Drivers & The Bullwhip Effect", 25, "sPh6S4wIqC4"),
                        (2, "Push vs Pull Systems", "Make-to-Stock vs Make-to-Order & Decoupling Points", 25, "k8lSgL32_5U"),
                        (3, "Demand Forecasting", "Time-Series Forecasting: Moving Averages & Exponential Smoothing", 30, "Z52G4y1o6Jc"),
                        (4, "Forecast Error Metrics", "Measuring Forecast Accuracy: MAD, MSE & MAPE Calculations", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Inventory Optimization & Storage", [
                        (5, "Inventory Costs", "Holding, Ordering & Stockout Costs: The Trade-off Triangle", 25, "97H0a3Xl-1M"),
                        (6, "EOQ Model", "Economic Order Quantity (EOQ) Mathematical Derivation", 30, "1P8j3J9gE0I"),
                        (7, "Safety Stock Modeling", "Calculating Safety Stock under Lead Time & Demand Uncertainty", 30, "m2XyE_K0918"),
                        (8, "ABC Analysis", "Inventory Categorization: ABC, VED & Just-in-Time (JIT) Practices", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Procurement & Global Logistics", [
                        (9, "Strategic Sourcing", "Strategic Sourcing, Kraljic Matrix & Vendor Evaluation", 25, "zS8Y7T36J80"),
                        (10, "Incoterms & Freight", "Incoterms 2020, Ocean, Air & Intermodal Freight Contracts", 30, "6p873K6G5sQ"),
                        (11, "Warehouse Operations", "Warehouse Layouts, Automated Storage & Cross-Docking", 25, "vX9vFh33p54"),
                        (12, "3PL & 4PL Logistics", "Third-Party Logistics (3PL) vs Fourth-Party Integrators (4PL)", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Lean Operations & Quality Systems", [
                        (13, "Lean Principles", "Toyota Production System, 5S Principles & Eliminating Muda", 25, "9bZkp7q19f0"),
                        (14, "Six Sigma Methodology", "Six Sigma DMAIC Methodology & Process Capability (Cpk)", 30, "kJQP7kiw5Fk"),
                        (15, "Theory of Constraints", "Goldratt's Theory of Constraints & Bottleneck Management", 25, "L_LUpnjgPso"),
                        (16, "Sustainable Supply Chains", "Circular Supply Chains, Reverse Logistics & Carbon Footprinting", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Business Analytics & Executive Data Modeling with Tableau",
                "business-analytics-tableau-excel",
                "management-business",
                "Beginner",
                "Ananya Chatterjee",
                "Lead Business Analytics Consultant & Data Storyteller",
                "14 hours",
                "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80",
                "Master managerial Excel modeling, regression analysis, predictive business forecasting, and Tableau executive dashboards.",
                "Target Degree: BBA / MBA. Quantitative decision science for modern managers. Learn pivot table modeling, correlation, multiple regression, what-if sensitivity analysis, and building interactive Tableau executive dashboards.",
                "Build dynamic financial and operational models in Microsoft Excel\nAnalyze bivariate and multiple regression relationships for business trends\nExecute Monte Carlo and What-If scenario simulations (Data Tables, Goal Seek)\nCreate interactive, visual business intelligence dashboards in Tableau\nCommunicate data-driven insights through structured executive storytelling",
                "Familiarity with basic computer spreadsheets",
                [
                    ("Module 1: Advanced Excel for Managers", [
                        (1, "Excel Data Functions", "Advanced Lookup Functions: XLOOKUP, INDEX-MATCH & FILTER", 25, "sPh6S4wIqC4"),
                        (2, "Pivot Tables & Slicers", "Multi-Dimensional Pivot Tables, Calculated Fields & Slicers", 30, "k8lSgL32_5U"),
                        (3, "Data Cleaning Workflows", "Handling Missing Data, Text-to-Columns & Power Query Basics", 25, "Z52G4y1o6Jc"),
                        (4, "Scenario Analysis", "Scenario Manager, Data Tables & Goal Seek Modeling", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Descriptive & Inferential Statistics for Business", [
                        (5, "Descriptive Metrics", "Central Tendency, Variance, Standard Deviation & Skewness", 25, "97H0a3Xl-1M"),
                        (6, "Correlation & Covariance", "Measuring Business Variable Association: Pearson vs Spearman", 25, "1P8j3J9gE0I"),
                        (7, "Simple Linear Regression", "Estimating OLS Regression Lines & R-Squared Interpretation", 30, "m2XyE_K0918"),
                        (8, "Multiple Regression", "Multiple Regression, Multicollinearity (VIF) & P-Value Testing", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Visual Analytics with Tableau", [
                        (9, "Tableau Architecture", "Connecting Data Sources, Live vs Extract Connections", 25, "zS8Y7T36J80"),
                        (10, "Chart Types in Tableau", "Bar Charts, Line Trends, Treemaps & Scatter Plots", 25, "6p873K6G5sQ"),
                        (11, "Calculated Fields", "Tableau Calculated Fields, Level of Detail (LOD) Expressions", 30, "vX9vFh33p54"),
                        (12, "Interactive Dashboards", "Actions, Parameters & Filter Controls in Executive Dashboards", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Business Insights & Decision Storytelling", [
                        (13, "Cohort & Churn Analytics", "Cohort Analysis, Churn Prediction & Retention Curves", 30, "9bZkp7q19f0"),
                        (14, "Customer Segmentation", "RFM (Recency, Frequency, Monetary) Customer Segmentation", 30, "kJQP7kiw5Fk"),
                        (15, "Executive Presentations", "Storytelling with Data: Designing Clear Executive Briefs", 25, "L_LUpnjgPso"),
                        (16, "A/B Testing in Business", "Design of Experiments, A/B Testing & Statistical Power", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Entrepreneurship, Startup Scaling & Venture Capital",
                "entrepreneurship-venture-capital",
                "management-business",
                "Beginner",
                "Kunal Bahl, Angel Investor",
                "Serial Entrepreneur & Startup Ecosystem Mentor",
                "13 hours",
                "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=800&q=80",
                "Master lean validation, cap tables, SAFE notes, pitch decks, term sheets, unit economics, and venture capital fundraising.",
                "Target Degree: BBA / MBA. From ideation to Series A. Learn the Lean Canvas, customer validation, unit economics, SAFE notes, cap table modeling, constructing investor pitch decks, and negotiating term sheets.",
                "Formulate and stress-test Lean Business Model Canvases\nCalculate startup unit economics: CAC, LTV, Payback Period, and Burn Rate\nConstruct equity capitalization tables (Cap Tables) with convertible notes and SAFEs\nDesign persuasive 10-slide venture capital pitch decks\nNegotiate term sheets: Liquidation preferences, pro-rata rights, and governance",
                "Passion for building new ventures and business innovation",
                [
                    ("Module 1: Ideation & Customer Validation", [
                        (1, "Opportunity Discovery", "Identifying Problem Spaces, Unfair Advantages & Timing", 20, "sPh6S4wIqC4"),
                        (2, "The Lean Canvas", "Mapping the Lean Canvas: Problems, Solutions & Unique Value", 25, "k8lSgL32_5U"),
                        (3, "Customer Discovery", "Conducting Mom-Test Customer Discovery Interviews", 25, "Z52G4y1o6Jc"),
                        (4, "Validation Experiments", "Smoke Tests, Landing Page Experiments & Minimum Viable Products", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Startup Financials & Unit Economics", [
                        (5, "Unit Economics", "Mastering Unit Economics: CAC, LTV, Payback & Gross Margins", 30, "97H0a3Xl-1M"),
                        (6, "Runway & Burn Rate", "Cash Flow Runway, Gross Burn vs Net Burn Management", 25, "1P8j3J9gE0I"),
                        (7, "Startup Pricing", "Pricing Strategies for Early Stage Startups: Freemium to Enterprise", 25, "m2XyE_K0918"),
                        (8, "Financial Projections", "Building 3-Year Pro Forma Startup Financial Statements", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Fundraising & Venture Capital", [
                        (9, "Funding Stages", "Bootstrapping vs Grants vs Angel Investors vs Venture Capital", 25, "zS8Y7T36J80"),
                        (10, "Investment Instruments", "Priced Equity Rounds, Convertible Notes & SAFE Notes", 30, "6p873K6G5sQ"),
                        (11, "Cap Table Modeling", "Modeling Cap Tables, Dilution & Employee Stock Option Pools (ESOP)", 30, "vX9vFh33p54"),
                        (12, "Pre-Money Valuation", "Startup Valuation Methodologies: Scorecard, Berkus & DCF", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Pitching, Term Sheets & Scaling", [
                        (13, "Pitch Deck Architecture", "Anatomy of a Winning 10-Slide Investor Pitch Deck", 25, "9bZkp7q19f0"),
                        (14, "Term Sheet Anatomy", "Deciphering Term Sheets: Liquidation Preferences, Drag-Along & Board Seats", 30, "kJQP7kiw5Fk"),
                        (15, "Growth Engines", "Viral, Paid & Sticky Growth Engines for Scaling Startups", 25, "L_LUpnjgPso"),
                        (16, "Exit Strategies", "M&A Acquisition, Secondary Sales & Initial Public Offerings (IPO)", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Investment Banking Fundamentals & Financial Markets",
                "investment-banking-financial-markets",
                "management-business",
                "Intermediate",
                "Siddharth Menon",
                "Managing Director, Global Investment Banking Division",
                "15 hours",
                "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=800&q=80",
                "Master M&A advisory, IPO roadmaps, pitch books, debt capital markets, leveraged buyouts (LBO), and fairness opinions.",
                "Target Degree: MBA / BBA. Real-world investment banking training. Learn the role of investment banks, equity capital markets (IPO underwriting), debt syndicate offerings, leveraged buyout (LBO) fundamentals, and M&A pitch books.",
                "Understand the core divisions: Advisory, Capital Markets, and Sales & Trading\nAnalyze initial public offering (IPO) mechanics, book building, and underwriting\nEvaluate debt capital market instruments: Corporate bonds, high-yield, and syndication\nConstruct high-level leveraged buyout (LBO) return profiles (IRR, MoIC)\nDraft professional M&A pitch books and strategic acquisition memos",
                "Solid understanding of accounting principles and corporate finance",
                [
                    ("Module 1: Investment Banking Ecosystem", [
                        (1, "IB Landscape", "Structure of Investment Banks: Front, Middle & Back Office", 20, "sPh6S4wIqC4"),
                        (2, "Sell-Side vs Buy-Side", "Sell-Side Advisors vs Buy-Side Asset Managers", 25, "k8lSgL32_5U"),
                        (3, "Securities Underwriting", "Firm Commitment vs Best Efforts Underwriting Syndicates", 25, "Z52G4y1o6Jc"),
                        (4, "Chinese Walls & Ethics", "Information Barriers, Insider Trading Laws & SEC/SEBI Regulations", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Equity Capital Markets (ECM) & IPOs", [
                        (5, "IPO Readiness", "IPO Timeline: Registration, S-1 Filing, Due Diligence & Audits", 30, "97H0a3Xl-1M"),
                        (6, "Book Building", "Roadshows, Institutional Book Building & Pricing Mechanics", 30, "1P8j3J9gE0I"),
                        (7, "IPO Underpricing", "Analyzing First-Day Pops, Underpricing & Greenshoe Options", 25, "m2XyE_K0918"),
                        (8, "Follow-On Offerings", "Secondary Offerings, Rights Issues & Private Placements (QIP)", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Debt Capital Markets (DCM) & Syndication", [
                        (9, "Fixed Income Overview", "Government Bonds, Corporate Bonds & Commercial Paper", 25, "zS8Y7T36J80"),
                        (10, "Credit Rating Process", "Moody's & S&P Rating Methodologies & Default Probabilities", 25, "6p873K6G5sQ"),
                        (11, "Loan Syndication", "Syndicated Lending, Lead Arrangers & Covenant Structures", 30, "vX9vFh33p54"),
                        (12, "High Yield & Distressed", "High Yield Bonds, Mezzanine Debt & Restructuring Advisory", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: M&A Advisory & Leveraged Buyouts", [
                        (13, "M&A Auction Process", "Broad Auctions vs Targeted Negotiations & Teaser Documents", 30, "9bZkp7q19f0"),
                        (14, "Fairness Opinions", "Conducting Valuation Verification & Fairness Opinion Reviews", 30, "kJQP7kiw5Fk"),
                        (15, "LBO Fundamentals", "The Mechanics of Leveraged Buyouts: Debt Tranches & Returns", 35, "L_LUpnjgPso"),
                        (16, "Pitch Book Creation", "Structuring Professional Investment Banking Pitch Books", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Digital Marketing Strategy, Performance Ads & Growth Hacking",
                "digital-marketing-growth-hacking",
                "management-business",
                "Beginner",
                "Rohit Verma",
                "VP of Growth Marketing & Ex-Google Performance Specialist",
                "13 hours",
                "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800&q=80",
                "Master Google Ads, Meta campaign optimization, SEO keyword architecture, email drip campaigns, and viral growth loops.",
                "Target Degree: BBA / MBA. Quantitative digital marketing and performance advertising. Learn Google Ads, Meta Ads Manager, technical SEO, attribution modeling, email marketing automation, and conversion rate optimization (CRO).",
                "Set up and optimize Google Search, Display, and Video campaigns\nExecute Meta (Facebook & Instagram) demographic and lookalike ad campaigns\nPerform keyword research, technical SEO audits, and backlink strategies\nDesign behavioral email marketing drip sequences with Mailchimp/Klaviyo\nCalculate ROAS, CTR, CPC, CPA, and build multi-touch attribution models",
                "No coding required. General familiarity with social media and web browsing",
                [
                    ("Module 1: Performance Marketing Foundations", [
                        (1, "Digital Landscape", "The Performance Marketing Ecosystem & Customer Funnels", 20, "sPh6S4wIqC4"),
                        (2, "Tracking & Attribution", "Meta Pixel, Google Tag Manager & Server-Side Tracking", 25, "k8lSgL32_5U"),
                        (3, "Attribution Models", "First-Click vs Last-Click vs Data-Driven Attribution", 25, "Z52G4y1o6Jc"),
                        (4, "Key Metrics", "Calculating CPA, ROAS, Customer Lifetime Value & Ad Fatigue", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Search Engine Optimization (SEO)", [
                        (5, "Keyword Architecture", "Commercial vs Informational Keyword Search Intent Mapping", 25, "97H0a3Xl-1M"),
                        (6, "On-Page SEO", "Title Tags, Header Hierarchy, Schema Markup & Meta Descriptions", 25, "1P8j3J9gE0I"),
                        (7, "Technical SEO", "Core Web Vitals, Crawl Budgets, Robots.txt & XML Sitemaps", 30, "m2XyE_K0918"),
                        (8, "Off-Page Authority", "High-Quality Backlink Building & Digital PR Strategies", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Paid Advertising (Google & Meta)", [
                        (9, "Google Search Ads", "Match Types, Quality Score, Bidding Strategies & Ad Copies", 30, "zS8Y7T36J80"),
                        (10, "Google Performance Max", "Performance Max Campaigns, Asset Groups & Conversion Tracking", 25, "6p873K6G5sQ"),
                        (11, "Meta Ads Manager", "Audience Targeting, Lookalikes & Retargeting Workflows", 30, "vX9vFh33p54"),
                        (12, "Creative Testing", "Dynamic Creative Optimization & Video Ad Hook Frameworks", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Retention, Email & Conversion Optimization", [
                        (13, "Email Automation", "Welcome Drips, Abandoned Cart Sequences & Win-Back Flows", 25, "9bZkp7q19f0"),
                        (14, "Landing Page CRO", "High-Converting Landing Page Design & Friction Reduction", 25, "kJQP7kiw5Fk"),
                        (15, "A/B Testing Frameworks", "Hypothesis Formulation, Sample Size Calculation & Split Tests", 25, "L_LUpnjgPso"),
                        (16, "Growth Hacking Loops", "Viral Referral Loops, Product-Led Growth & Retention Strategies", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "International Business & Cross-Border Trade Policy",
                "international-business-cross-border-trade",
                "management-business",
                "Intermediate",
                "Dr. Alistair MacIntyre",
                "International Trade Economist & WTO Policy Advisor",
                "14 hours",
                "https://images.unsplash.com/photo-1578575437130-527eed3abbec?auto=format&fit=crop&w=800&q=80",
                "Master globalization drivers, foreign exchange hedging, tariff structures, cross-border entry modes, and multinational strategies.",
                "Target Degree: BBA / MBA. Global corporate management and trade policy. Learn why nations trade, currency hedging (Forwards, Futures, Swaps), tariff vs non-tariff barriers, geopolitical risk evaluation, and multinational organization.",
                "Examine theories of comparative advantage and factor endowments (Heckscher-Ohlin)\nAnalyze foreign currency exchange rates and hedging techniques for cross-border transactions\nEvaluate market entry modes: Exporting, Licensing, Joint Ventures, and FDI\nNavigate international trade regulations, customs clearance, and WTO disputes\nManage multi-cultural teams and transnational corporate governance structures",
                "Basic understanding of macroeconomics and business principles",
                [
                    ("Module 1: The Global Business Environment", [
                        (1, "Globalization Drivers", "Economic, Technological & Political Drivers of Globalization", 25, "sPh6S4wIqC4"),
                        (2, "Classical Trade Theories", "Mercantilism, Absolute Advantage & Comparative Advantage", 25, "k8lSgL32_5U"),
                        (3, "Modern Trade Models", "Heckscher-Ohlin Theorem, Product Life Cycle & Porter's Diamond", 30, "Z52G4y1o6Jc"),
                        (4, "Trade Barriers", "Tariffs, Import Quotas, Anti-Dumping Duties & Subsidies", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Foreign Exchange & Global Financial System", [
                        (5, "Forex Market Mechanics", "Spot, Forward & Swap Markets: Currency Quotation Conventions", 30, "97H0a3Xl-1M"),
                        (6, "Exchange Rate Theories", "Purchasing Power Parity (PPP) & Interest Rate Parity (IRP)", 30, "1P8j3J9gE0I"),
                        (7, "Currency Risk Hedging", "Managing Transaction, Translation & Economic Exposure", 30, "m2XyE_K0918"),
                        (8, "Bretton Woods & IMF", "The International Monetary Fund (IMF), World Bank & SDRs", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Global Strategy & Entry Modes", [
                        (9, "Foreign Market Selection", "Market Attractiveness, CAGE Distance Framework & PESTLE", 25, "zS8Y7T36J80"),
                        (10, "Entry Modes Spectrum", "Direct Exporting, Licensing, Franchising & Turnkey Projects", 25, "6p873K6G5sQ"),
                        (11, "Foreign Direct Investment", "FDI Determinants: Dunning's Eclectic OLI Paradigm", 30, "vX9vFh33p54"),
                        (12, "Multinational Strategies", "Global Standardized vs Multi-Domestic vs Transnational Strategy", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Global Operations & Geopolitics", [
                        (13, "Cross-Cultural Management", "Hofstede's Cultural Dimensions & Trompenaars Framework", 25, "9bZkp7q19f0"),
                        (14, "Global Supply Chains", "Offshoring, Reshoring, Friendshoring & Tariff Arbitrage", 25, "kJQP7kiw5Fk"),
                        (15, "International Trade Law", "WTO Dispute Settlement, Regional Trade Agreements & USMCA/RCEP", 25, "L_LUpnjgPso"),
                        (16, "Geopolitical Risk", "Assessing Political Risk, Expropriation & Sovereign Sanctions", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
        ]

        # Add BBA/MBA courses to pool
        for item in bba_mba:
            courses.append(self._format_course(item))

        # ---------------------------------------------------------------------
        # DEGREE 2: BTech & MTech (10 Courses)
        # ---------------------------------------------------------------------
        btech_mtech = [
            (
                "VLSI Design, Verilog HDL & Digital Circuit Architecture",
                "vlsi-design-verilog-architecture",
                "engineering-tech",
                "Advanced",
                "Dr. S. K. Narayanan",
                "Principal Semiconductor Architect & IEEE Senior Member",
                "16 hours",
                "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80",
                "Master CMOS logic, Verilog HDL modeling, combinational synthesis, state machines, timing constraints, and physical design.",
                "Target Degree: BTech / MTech. Advanced digital integrated circuit engineering. Learn CMOS transistor physics, RTL modeling in Verilog, synthesis, static timing analysis (STA), clock distribution, and ASIC tape-out flow.",
                "Model synchronous digital systems in synthesizable Verilog HDL\nAnalyze CMOS inverter transfer characteristics, noise margins, and propagation delay\nDesign finite state machines (FSM) with Moore and Mealy architectures\nPerform Static Timing Analysis (STA): Setup, hold times, and slack calculations\nUnderstand the ASIC physical design flow: Floorplanning, placement, and routing",
                "Digital logic fundamentals (Boolean algebra, gates, latches)\nBasic circuit analysis",
                [
                    ("Module 1: CMOS Physics & Combinational Logic", [
                        (1, "MOSFET Physics", "MOSFET Device Characteristics, IV Curves & Second-Order Effects", 25, "sPh6S4wIqC4"),
                        (2, "CMOS Inverter", "CMOS Inverter VTC, Switching Threshold & Dynamic Power", 30, "k8lSgL32_5U"),
                        (3, "Static CMOS Gates", "Static CMOS NAND, NOR, Complex Gate Sizing & Euler Paths", 30, "Z52G4y1o6Jc"),
                        (4, "Logical Effort", "Logical Effort Theory: Path Delay Optimization & Buffer Sizing", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Verilog HDL & RTL Synthesis", [
                        (5, "Verilog Fundamentals", "Data Types, Continuous Assignment & Procedural Blocks (always)", 25, "97H0a3Xl-1M"),
                        (6, "Blocking vs Non-Blocking", "Blocking (=) vs Non-Blocking (<=) Assignments & Race Hazards", 30, "1P8j3J9gE0I"),
                        (7, "Combinational RTL", "Designing Multiplexers, Adders & ALUs in Verilog HDL", 25, "m2XyE_K0918"),
                        (8, "Testbenches", "Writing Self-Checking Testbenches with Tasks & Directives", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Sequential Circuits & State Machines", [
                        (9, "Sequential Elements", "Latches vs Flip-Flops: Metastability & Setup/Hold Times", 25, "zS8Y7T36J80"),
                        (10, "FSM Design", "Moore and Mealy State Machine RTL Implementation", 30, "6p873K6G5sQ"),
                        (11, "Pipelining & Retiming", "High-Throughput Pipelining Architecture & Retiming Theorems", 30, "vX9vFh33p54"),
                        (12, "FIFO Buffers", "Asynchronous FIFO Architecture & Gray Code Pointers", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Timing Analysis & Physical Design", [
                        (13, "Static Timing Analysis", "STA Fundamentals: Clock Skew, Jitter, Setup & Hold Slack", 35, "9bZkp7q19f0"),
                        (14, "Clock Tree Synthesis", "Clock Tree Distribution: H-Tree, Mesh & Skew Minimization", 30, "kJQP7kiw5Fk"),
                        (15, "ASIC Flow", "RTL-to-GDSII Physical Design Flow: Placement & Routing", 30, "L_LUpnjgPso"),
                        (16, "Design for Testability", "Scan Chains, BIST (Built-in Self-Test) & Boundary Scan", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Distributed Systems, Fault Tolerance & Microservices",
                "distributed-systems-microservices",
                "engineering-tech",
                "Advanced",
                "Dr. Elena Rostova",
                "Distributed Systems Architect & Cloud Infrastructure Fellow",
                "16 hours",
                "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=800&q=80",
                "Master consensus algorithms (Raft/Paxos), CAP theorem, event-driven microservices, distributed transactions, and geo-replication.",
                "Target Degree: MTech / BTech. Theoretical and practical distributed systems. Learn logical clocks, vector clocks, quorum consensus (Raft/Paxos), partitioned databases, distributed transactions (Saga, 2PC), and resilient microservices.",
                "Implement distributed consensus algorithms (Raft protocol states and elections)\nDesign distributed event-driven microservices with Kafka and RabbitMQ\nResolve network partitions and consistency trade-offs under the CAP theorem\nExecute distributed transactions using Saga choreography and two-phase commit\nImplement rate limiters, circuit breakers, and geo-replicated data stores",
                "Strong proficiency in Python, Java, or Go\nUnderstanding of computer networks and concurrent programming",
                [
                    ("Module 1: Foundations of Distributed Computing", [
                        (1, "Distributed Challenges", "Fallacies of Distributed Computing & Clock Drift", 25, "sPh6S4wIqC4"),
                        (2, "Logical Clocks", "Lamport Timestamps & Vector Clocks for Causal Ordering", 30, "k8lSgL32_5U"),
                        (3, "CAP Theorem", "CAP Theorem & PACELC: Consistency vs Availability Trade-offs", 25, "Z52G4y1o6Jc"),
                        (4, "Data Partitioning", "Consistent Hashing & Virtual Nodes for Horizontal Scaling", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Distributed Consensus & Replication", [
                        (5, "Consensus Problem", "The Distributed Consensus Challenge & Byzantine Faults", 25, "97H0a3Xl-1M"),
                        (6, "The Raft Protocol", "Raft Consensus: Leader Election, Log Replication & Safety", 35, "1P8j3J9gE0I"),
                        (7, "Paxos Fundamentals", "Multi-Paxos Protocol: Proposers, Acceptors & Learners", 30, "m2XyE_K0918"),
                        (8, "Quorum Systems", "Leaderless Replication, Quorum Math (R + W > N) & Anti-Entropy", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Microservices & Distributed Transactions", [
                        (9, "Microservices Design", "Domain-Driven Design (DDD), Bounded Contexts & Decoupling", 25, "zS8Y7T36J80"),
                        (10, "Event-Driven Messaging", "Event Sourcing & CQRS with Apache Kafka", 30, "6p873K6G5sQ"),
                        (11, "Distributed Transactions", "Two-Phase Commit (2PC) vs Saga Orchestration Patterns", 35, "vX9vFh33p54"),
                        (12, "API Gateways", "API Gateway Architecture: Routing, Authentication & Rate Limiting", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Resilience & High Availability", [
                        (13, "Resilience Patterns", "Circuit Breakers, Bulkheads, Retries & Exponential Backoff", 25, "9bZkp7q19f0"),
                        (14, "Distributed Caching", "Cache Invalidation, Cache-Aside & Redis Cluster Sharding", 30, "kJQP7kiw5Fk"),
                        (15, "Distributed Tracing", "OpenTelemetry, Distributed Tracing & Span Context Propagation", 30, "L_LUpnjgPso"),
                        (16, "Chaos Engineering", "Chaos Engineering: Injecting Latency, Failure Injection & Drills", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Advanced Cyber Security, Applied Cryptography & Network Defense",
                "advanced-cyber-security-cryptography",
                "engineering-tech",
                "Advanced",
                "Marcus Vance, CISSP",
                "Chief Information Security Officer & Ethical Hacking Instructor",
                "15 hours",
                "https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=800&q=80",
                "Master AES/RSA cryptography, network packet inspection, penetration testing, threat hunting, and zero trust security.",
                "Target Degree: BTech / MTech. Hands-on offensive and defensive cybersecurity. Learn mathematical foundations of modern cryptography (AES, RSA, Elliptic Curves), packet analysis with Wireshark, exploiting and mitigating OWASP Top 10 vulnerabilities, and Zero Trust architecture.",
                "Implement symmetric and asymmetric cryptographic ciphers (AES-GCM, RSA, ECC)\nAnalyze malicious network traffic using Wireshark and Snort IDS\nDetect and remediate OWASP Top 10 vulnerabilities (SQLi, XSS, SSRF)\nExecute threat modeling and attack surface mapping with STRIDE\nArchitect enterprise Zero Trust network security and identity access controls",
                "Basic understanding of computer networking (TCP/IP) and Python or C programming",
                [
                    ("Module 1: Applied Cryptography", [
                        (1, "Crypto Foundations", "Classical Ciphers, Shannon's Perfect Secrecy & One-Time Pad", 25, "sPh6S4wIqC4"),
                        (2, "Symmetric Encryption", "AES Architecture, Block Cipher Modes (CBC vs GCM)", 30, "k8lSgL32_5U"),
                        (3, "Asymmetric Cryptography", "RSA Math, Diffie-Hellman Key Exchange & Elliptic Curve (ECC)", 35, "Z52G4y1o6Jc"),
                        (4, "Hashing & Signatures", "Cryptographic Hash Functions (SHA-256), HMAC & Digital Signatures", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Network Security & Traffic Analysis", [
                        (5, "Packet Inspection", "Deep Packet Inspection with Wireshark: TCP Streams & DNS Anomaly", 25, "97H0a3Xl-1M"),
                        (6, "Network Attacks", "ARP Poisoning, SYN Floods, Man-in-the-Middle & DNS Spoofing", 30, "1P8j3J9gE0I"),
                        (7, "Intrusion Detection", "Configuring Snort IDS/IPS Rules & Signature Matching", 30, "m2XyE_K0918"),
                        (8, "Firewalls & VPNs", "Stateful Firewalls, NAT, IPsec & WireGuard Protocols", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Web Application Security", [
                        (9, "OWASP Top 10", "SQL Injection: Union-Based, Blind & Prepared Statements", 30, "zS8Y7T36J80"),
                        (10, "Cross-Site Scripting", "Stored, Reflected & DOM-based XSS: Content Security Policy (CSP)", 30, "6p873K6G5sQ"),
                        (11, "Server-Side Vulnerabilities", "Server-Side Request Forgery (SSRF) & Remote Code Execution", 30, "vX9vFh33p54"),
                        (12, "Authentication Flaws", "Broken Object Level Auth (BOLA), JWT Tampering & Session Hijacking", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Enterprise Defense & Threat Intelligence", [
                        (13, "Threat Modeling", "STRIDE Threat Modeling & MITRE ATT&CK Framework", 25, "9bZkp7q19f0"),
                        (14, "Zero Trust Architecture", "Zero Trust Principles: Continuous Verification & Microsegmentation", 25, "kJQP7kiw5Fk"),
                        (15, "Incident Response", "Digital Forensics, SIEM Log Correlation & Incident Containment", 30, "L_LUpnjgPso"),
                        (16, "Penetration Testing", "Ethical Hacking Methodologies: Recon, Exploitation & Reporting", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Cloud Native Infrastructure with Kubernetes & Terraform",
                "cloud-native-kubernetes-terraform",
                "engineering-tech",
                "Intermediate",
                "David Lindqvist",
                "Staff Cloud Architect & CNCF Community Contributor",
                "15 hours",
                "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80",
                "Master declarative infrastructure with Terraform, Kubernetes cluster operations, ingress controllers, Helm, and GitOps CI/CD.",
                "Target Degree: BTech / MTech. Modern cloud native platform engineering. Learn Terraform state management, provisioning cloud networks, Kubernetes pod lifecycle, Deployments, StatefulSets, Ingress routing, Helm charts, and ArgoCD GitOps.",
                "Provision cloud infrastructure declaratively using Terraform HCL\nManage Kubernetes workloads: Deployments, Services, ConfigMaps, and Secrets\nConfigure Ingress controllers, cert-manager TLS, and service mesh routing\nPackage and distribute multi-service cloud applications using Helm\nAutomate continuous deployments with GitOps pipelines (ArgoCD)",
                "Familiarity with Docker containerization and Linux command-line basics",
                [
                    ("Module 1: Infrastructure as Code with Terraform", [
                        (1, "IaC Foundations", "Declarative vs Imperative IaC & Terraform Architecture", 25, "sPh6S4wIqC4"),
                        (2, "Terraform HCL", "Providers, Resources, Variables & Output Declarations", 25, "k8lSgL32_5U"),
                        (3, "State Management", "Terraform Remote State, S3 Backends & State Locking with DynamoDB", 30, "Z52G4y1o6Jc"),
                        (4, "Terraform Modules", "Designing Reusable, Production-Grade Infrastructure Modules", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Kubernetes Architecture & Core Workloads", [
                        (5, "K8s Architecture", "Control Plane (API Server, etcd, Scheduler) & Worker Nodes", 30, "97H0a3Xl-1M"),
                        (6, "Pods & Deployments", "Pod Lifecycle, Rolling Updates, Rollbacks & ReplicaSets", 25, "1P8j3J9gE0I"),
                        (7, "Configuration Management", "Decoupling Config with ConfigMaps & Kubernetes Secrets", 25, "m2XyE_K0918"),
                        (8, "Storage in Kubernetes", "PersistentVolumes, PersistentVolumeClaims & StorageClasses", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Networking, Services & Ingress", [
                        (9, "K8s Networking", "ClusterIP, NodePort & LoadBalancer Service Types", 25, "zS8Y7T36J80"),
                        (10, "Ingress Controllers", "Nginx Ingress, Routing Rules & Automated SSL with Cert-Manager", 30, "6p873K6G5sQ"),
                        (11, "StatefulSets", "Stateful Workloads: Ordered Scaling & Headless Services", 30, "vX9vFh33p54"),
                        (12, "Resource Management", "CPU/Memory Requests, Limits & Horizontal Pod Autoscaler (HPA)", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: GitOps, Packaging & Production SRE", [
                        (13, "Helm Package Manager", "Creating Custom Helm Charts & Values Override Management", 30, "9bZkp7q19f0"),
                        (14, "GitOps with ArgoCD", "GitOps Principles: Declarative Continuous Delivery with ArgoCD", 30, "kJQP7kiw5Fk"),
                        (15, "Cloud Observability", "Prometheus Metrics Scraping & Grafana Service Dashboards", 25, "L_LUpnjgPso"),
                        (16, "Security & Policies", "NetworkPolicies, RBAC Roles & Admission Controllers", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Embedded Systems, Microcontrollers & Embedded C",
                "embedded-systems-microcontrollers",
                "engineering-tech",
                "Intermediate",
                "Prof. N. K. Srinivas",
                "Robotics & Embedded Systems Research Lab Director",
                "14 hours",
                "https://images.unsplash.com/photo-1555680202-c86f0e12f086?auto=format&fit=crop&w=800&q=80",
                "Master ARM Cortex-M architecture, bitwise register manipulation, timers, interrupts, I2C/SPI buses, and FreeRTOS.",
                "Target Degree: BTech / MTech. Microcontroller firmware development. Learn ARM architecture, writing bare-metal device drivers in Embedded C, configuring hardware timers, interrupts, serial communication buses (UART, SPI, I2C), and FreeRTOS task scheduling.",
                "Write bare-metal Embedded C drivers using direct memory-mapped register pointers\nConfigure Nested Vectored Interrupt Controllers (NVIC) and handle ISRs\nImplement hardware timer delays, input capture, and PWM motor control\nInterface external sensors and EEPROMs via I2C and SPI serial buses\nBuild multi-tasking firmware with FreeRTOS queues, semaphores, and mutexes",
                "Proficiency in C programming language (pointers, structures, bitwise logic)",
                [
                    ("Module 1: ARM Architecture & Embedded C", [
                        (1, "Microcontroller Core", "Microprocessor vs Microcontroller & ARM Cortex-M Architecture", 25, "sPh6S4wIqC4"),
                        (2, "Memory Mapping", "Memory Map, Flash, SRAM & Memory-Mapped IO Registers", 25, "k8lSgL32_5U"),
                        (3, "Bitwise Operations", "Bitwise Manipulation (Setting, Clearing, Toggling Registers)", 25, "Z52G4y1o6Jc"),
                        (4, "GPIO Driver", "Writing Bare-Metal GPIO Output & Input Pin Drivers", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Interrupts & Timers", [
                        (5, "Interrupt Architecture", "NVIC (Nested Vectored Interrupt Controller) & Vector Table", 25, "97H0a3Xl-1M"),
                        (6, "Interrupt Service Routines", "Writing Efficient ISRs & Race Condition Prevention", 25, "1P8j3J9gE0I"),
                        (7, "Hardware Timers", "Timer Prescalers, Auto-Reload Registers & Timebase Generation", 30, "m2XyE_K0918"),
                        (8, "PWM Signal Generation", "Pulse Width Modulation (PWM) for Motor Speed & LED Dimming", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Serial Communication Protocols", [
                        (9, "UART Protocol", "UART Asynchronous Framing, Baud Rates & Circular Buffers", 25, "zS8Y7T36J80"),
                        (10, "SPI Bus", "SPI Synchronous Protocol: Master/Slave, Clock Polarity (CPOL/CPHA)", 30, "6p873K6G5sQ"),
                        (11, "I2C Bus Protocol", "I2C Two-Wire Protocol: Start/Stop Conditions, ACK/NACK & Addressing", 30, "vX9vFh33p54"),
                        (12, "Sensor Interfacing", "Interfacing Digital Accelerometers & OLED Displays over I2C", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Real-Time Operating Systems (RTOS)", [
                        (13, "RTOS Concepts", "Super-Loop Architecture vs Real-Time Preemptive Multitasking", 25, "9bZkp7q19f0"),
                        (14, "FreeRTOS Tasks", "Task Creation, Priorities, State Transitions & The Idle Task", 30, "kJQP7kiw5Fk"),
                        (15, "Task Synchronization", "Binary Semaphores, Counting Semaphores & Priority Inversion", 30, "L_LUpnjgPso"),
                        (16, "Inter-Task Queues", "FreeRTOS Message Queues & Event Groups for Thread-Safe Data", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Computer Vision & Convolutional Neural Networks with PyTorch",
                "computer-vision-deep-learning",
                "engineering-tech",
                "Advanced",
                "Dr. Jennifer Zhao",
                "Computer Vision Research Scientist & AI Lab Director",
                "16 hours",
                "https://images.unsplash.com/photo-1507146426996-ef05306b995a?auto=format&fit=crop&w=800&q=80",
                "Master image processing, CNN architectures (ResNet/EfficientNet), YOLO object detection, segmentation, and vision transformers.",
                "Target Degree: MTech / BTech. Deep learning applied to visual perception. Learn convolution mechanics, backpropagation through CNNs, transfer learning with ResNet, real-time object detection (YOLO), semantic segmentation, and Vision Transformers (ViT).",
                "Build and train custom CNN architectures in PyTorch\nApply transfer learning with pretrained ResNet, VGG, and EfficientNet backbones\nImplement real-time object detection pipelines with YOLO architectures\nExecute semantic and instance segmentation (U-Net and Mask R-CNN)\nUnderstand self-attention mechanisms in Vision Transformers (ViT)",
                "Strong Python programming and linear algebra/calculus fundamentals",
                [
                    ("Module 1: Image Processing & CNN Fundamentals", [
                        (1, "Digital Image Basics", "Color Spaces (RGB, HSV), Histograms & Kernel Filtering", 25, "sPh6S4wIqC4"),
                        (2, "Convolution Operation", "Mathematical Convolution, Stride, Padding & Feature Maps", 30, "k8lSgL32_5U"),
                        (3, "Pooling & Activation", "Max Pooling, Average Pooling, ReLU & Non-Linear Activation", 25, "Z52G4y1o6Jc"),
                        (4, "Building PyTorch CNN", "Writing Custom PyTorch Modules with torch.nn.Conv2d", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Modern CNN Architectures & Transfer Learning", [
                        (5, "Classical Architectures", "AlexNet, VGGNet & Addressing Vanishing Gradients", 25, "97H0a3Xl-1M"),
                        (6, "Residual Networks", "ResNet Skip Connections & Identity Mapping Mathematical Theory", 35, "1P8j3J9gE0I"),
                        (7, "Efficient Architectures", "MobileNet Depthwise Separable Convolutions & EfficientNet", 30, "m2XyE_K0918"),
                        (8, "Transfer Learning", "Feature Extraction vs Fine-Tuning & Learning Rate Schedules", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Object Detection & Segmentation", [
                        (9, "Object Localization", "Bounding Box Regression, Intersection over Union (IoU) & NMS", 30, "zS8Y7T36J80"),
                        (10, "Two-Stage Detectors", "R-CNN, Fast R-CNN & Faster R-CNN Region Proposal Networks", 30, "6p873K6G5sQ"),
                        (11, "One-Stage Detectors", "YOLO (You Only Look Once) Architecture & Anchor Boxes", 35, "vX9vFh33p54"),
                        (12, "Semantic Segmentation", "FCNs, U-Net Architecture & Skip Highway Connections", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Advanced Vision Models & Deployment", [
                        (13, "Vision Transformers", "Vision Transformers (ViT): Patch Embeddings & Self-Attention", 35, "9bZkp7q19f0"),
                        (14, "Generative Vision", "Generative Adversarial Networks (GANs) & Image-to-Image Translation", 30, "kJQP7kiw5Fk"),
                        (15, "Model Optimization", "Quantization, Pruning & ONNX Model Export", 25, "L_LUpnjgPso"),
                        (16, "Edge Deployment", "Deploying Vision Pipelines on Edge Devices with TensorRT", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Natural Language Processing, Transformers & Large Language Models",
                "natural-language-processing-llms",
                "engineering-tech",
                "Advanced",
                "Dr. Amitava Roy",
                "Principal NLP Research Engineer & Transformer Architect",
                "16 hours",
                "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=800&q=80",
                "Master embeddings, self-attention, the Transformer architecture, BERT, GPT, parameter-efficient fine-tuning (LoRA), and RAG.",
                "Target Degree: MTech / BTech. Modern deep learning for text and speech. Learn tokenization, dense embeddings, multi-head self-attention, encoder-decoder architectures, autoregressive LLMs, prompt engineering, LoRA fine-tuning, and vector database RAG.",
                "Implement tokenization and word embedding techniques (Byte-Pair Encoding, Word2Vec)\nConstruct Multi-Head Self-Attention layers from scratch in PyTorch\nFine-tune BERT for sequence classification and named entity recognition (NER)\nTrain and optimize autoregressive generative models using HuggingFace\nBuild production Retrieval-Augmented Generation (RAG) pipelines with LangChain and Pinecone",
                "Python programming and understanding of neural networks",
                [
                    ("Module 1: Text Representations & Sequence Models", [
                        (1, "Text Preprocessing", "Tokenization, Subword BPE & WordPiece Algorithms", 25, "sPh6S4wIqC4"),
                        (2, "Word Embeddings", "Word2Vec (CBOW vs Skip-Gram) & Cosine Vector Semantics", 30, "k8lSgL32_5U"),
                        (3, "Recurrent Networks", "RNNs, Exploding Gradients & Long Short-Term Memory (LSTM)", 30, "Z52G4y1o6Jc"),
                        (4, "Seq2Seq Architecture", "Sequence-to-Sequence Modeling & The Bottleneck Problem", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: The Transformer Architecture", [
                        (5, "Self-Attention Math", "Scaled Dot-Product Self-Attention: Queries, Keys & Values", 35, "97H0a3Xl-1M"),
                        (6, "Multi-Head Attention", "Multi-Head Attention & Positional Encoding Formulations", 35, "1P8j3J9gE0I"),
                        (7, "Encoder Architecture", "Layer Normalization, Residual Connections & Feedforward Blocks", 30, "m2XyE_K0918"),
                        (8, "Decoder Architecture", "Masked Multi-Head Attention & Autoregressive Decoding", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Pre-Trained Language Models (BERT & GPT)", [
                        (9, "BERT Architecture", "BERT Masked Language Modeling & Next Sentence Prediction", 30, "zS8Y7T36J80"),
                        (10, "GPT Family", "Generative Pre-trained Transformers (GPT): Causal Language Models", 30, "6p873K6G5sQ"),
                        (11, "Hugging Face Ecosystem", "Fine-Tuning Transformers with Hugging Face Trainer API", 30, "vX9vFh33p54"),
                        (12, "Evaluation Metrics", "Perplexity, BLEU, ROUGE & Model Calibration Metrics", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Advanced LLMs & RAG Architectures", [
                        (13, "PEFT & LoRA", "Parameter-Efficient Fine-Tuning: LoRA & QLoRA Techniques", 35, "9bZkp7q19f0"),
                        (14, "Prompt Engineering", "Chain-of-Thought, Few-Shot & Constitutional AI Alignment", 25, "kJQP7kiw5Fk"),
                        (15, "RAG Systems", "Vector Databases, Hybrid Search & Context Augmentation", 35, "L_LUpnjgPso"),
                        (16, "LLM Evaluation", "Evaluating Hallucinations, Safety Guardrails & Model Quantization", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Compiler Design, Parsing & Code Optimization",
                "compiler-design-optimization",
                "engineering-tech",
                "Intermediate",
                "Prof. Jonathan Cross",
                "Senior Compiler Engineer & Systems Architecture Faculty",
                "15 hours",
                "https://images.unsplash.com/photo-1516116211227-bbc042ec7349?auto=format&fit=crop&w=800&q=80",
                "Master lexical analysis, context-free grammars, LL/LR parsers, abstract syntax trees, and SSA code optimization.",
                "Target Degree: BTech / MTech. Classic and modern compiler engineering. Learn regular expressions to DFA lexing, recursive descent parsing, shift-reduce LR parsers, syntax-directed translation, Three-Address Code (TAC), Static Single Assignment (SSA), and register allocation.",
                "Design deterministic finite automata (DFA) for lexical tokens\nConstruct context-free grammars and build LL(1) and LALR(1) parsers\nGenerate Abstract Syntax Trees (AST) and execute semantic type checking\nTransform code into Static Single Assignment (SSA) intermediate representation\nImplement dead code elimination, loop invariant code motion, and register allocation",
                "Proficiency in C or C++ and Data Structures & Algorithms",
                [
                    ("Module 1: Lexical Analysis & Tokenization", [
                        (1, "Compiler Phases", "Overview of Compiler Phases: Front-End vs Back-End", 20, "sPh6S4wIqC4"),
                        (2, "Regular Expressions", "Regular Expressions to Non-Deterministic Finite Automata (NFA)", 30, "k8lSgL32_5U"),
                        (3, "NFA to DFA", "Subset Construction Algorithm & Hopcroft's DFA Minimization", 30, "Z52G4y1o6Jc"),
                        (4, "Lexer Generators", "Building a Lexer with Flex / Lex & Handling Lookahead", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Syntax Analysis & Parsing", [
                        (5, "Context-Free Grammars", "CFGs, Derivations, Parse Trees & Grammar Ambiguity", 25, "97H0a3Xl-1M"),
                        (6, "Top-Down Parsing", "Eliminating Left Recursion, Left Factoring & LL(1) Parsers", 35, "1P8j3J9gE0I"),
                        (7, "Bottom-Up Parsing", "Shift-Reduce Parsing, LR(0) Items & SLR(1) Parsing Tables", 35, "m2XyE_K0918"),
                        (8, "LALR & Parser Generators", "LALR(1) Parsing Algorithms & Parser Construction with Bison / Yacc", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Semantic Analysis & Intermediate Code", [
                        (9, "Syntax-Directed Translation", "Syntax-Directed Definitions: Synthesized vs Inherited Attributes", 25, "zS8Y7T36J80"),
                        (10, "Abstract Syntax Trees", "Constructing ASTs & Symbol Table Scoping Architectures", 30, "6p873K6G5sQ"),
                        (11, "Type Checking", "Type Systems, Semantic Rules & Static Type Inference", 25, "vX9vFh33p54"),
                        (12, "Three-Address Code", "Three-Address Code (TAC), Quadruples & Triples Representation", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Code Optimization & Machine Generation", [
                        (13, "Control Flow Graphs", "Basic Blocks, Control Flow Graphs (CFG) & Dominator Trees", 30, "9bZkp7q19f0"),
                        (14, "Dataflow Analysis", "Reaching Definitions, Liveness Analysis & Available Expressions", 35, "kJQP7kiw5Fk"),
                        (15, "SSA Form", "Static Single Assignment (SSA) & Phi-Function Placement", 30, "L_LUpnjgPso"),
                        (16, "Register Allocation", "Chaitin's Graph Coloring Register Allocation Algorithm", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Blockchain Architecture, Cryptography & Smart Contracts",
                "blockchain-architecture-smart-contracts",
                "engineering-tech",
                "Intermediate",
                "Dr. Tarun Chawla",
                "Decentralized Systems Researcher & Web3 Core Developer",
                "15 hours",
                "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?auto=format&fit=crop&w=800&q=80",
                "Master Merkle trees, proof of work/stake, EVM bytecode, Solidity smart contracts, DeFi tokens (ERC-20/721), and security auditing.",
                "Target Degree: BTech / MTech. Core blockchain and decentralized systems. Learn hashing and digital signatures in distributed ledgers, Byzantine Fault Tolerance (BFT), Ethereum Virtual Machine (EVM) opcode execution, Solidity smart contracts, and reentrancy vulnerability remediation.",
                "Construct cryptographically verifiable Merkle trees and blockchain blocks\nEvaluate consensus mechanisms: Proof of Work vs Proof of Stake vs PBFT\nAuthor secure, gas-optimized smart contracts in Solidity\nImplement standard decentralized token protocols (ERC-20 and ERC-721)\nDetect and patch critical smart contract vulnerabilities (Reentrancy, Integer Overflow)",
                "Familiarity with object-oriented programming and basic cryptography",
                [
                    ("Module 1: Blockchain Foundations & Cryptography", [
                        (1, "Decentralized Ledgers", "Double-Spending Problem & The Bitcoin Whitepaper", 25, "sPh6S4wIqC4"),
                        (2, "Cryptographic Primitives", "SHA-256 Hashing, Elliptic Curve Signatures (secp256k1)", 30, "k8lSgL32_5U"),
                        (3, "Merkle Trees", "Merkle Trees, Merkle Proofs & SPV Light Clients", 25, "Z52G4y1o6Jc"),
                        (4, "UTXO vs Account Model", "UTXO Transaction Model vs Account-Based State Machines", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Consensus Protocols", [
                        (5, "Byzantine Agreement", "Byzantine Generals Problem & Classical BFT Consensus", 25, "97H0a3Xl-1M"),
                        (6, "Proof of Work", "Nakamoto Consensus, Mining Difficulty Adjustment & 51% Attacks", 30, "1P8j3J9gE0I"),
                        (7, "Proof of Stake", "Proof of Stake Mechanics: Slashing, Finality & Casper/Tendermint", 30, "m2XyE_K0918"),
                        (8, "Scalability Solutions", "Layer 2 Solutions: Optimistic Rollups vs ZK-Rollups", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Ethereum & Solidity Programming", [
                        (9, "The EVM", "The Ethereum Virtual Machine (EVM), Gas Economics & Opcode Execution", 30, "zS8Y7T36J80"),
                        (10, "Solidity Language", "Data Types, Mappings, Modifiers & Events in Solidity", 25, "6p873K6G5sQ"),
                        (11, "ERC-20 Token Standards", "Writing, Testing & Deploying Standard ERC-20 Tokens", 30, "vX9vFh33p54"),
                        (12, "NFT Standards", "ERC-721 and ERC-1155 Non-Fungible Token Contracts", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Security, DeFi & Auditing", [
                        (13, "Reentrancy Attacks", "The DAO Hack: Reentrancy Exploits & Checks-Effects-Interactions", 35, "9bZkp7q19f0"),
                        (14, "Smart Contract Security", "Oracle Manipulation, Front-Running & Access Control Flaws", 30, "kJQP7kiw5Fk"),
                        (15, "Automated Auditing", "Static Analysis Tools: Slither, Mythril & Formal Verification", 25, "L_LUpnjgPso"),
                        (16, "DeFi Protocols", "Automated Market Makers (AMM): Constant Product Formula (x*y=k)", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "High Performance Parallel Computing with MPI & OpenMP",
                "high-performance-computing-parallel",
                "engineering-tech",
                "Advanced",
                "Dr. Klaus Reinhardt",
                "Supercomputing Center Lead Scientist & Parallel Algorithms Chair",
                "16 hours",
                "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=800&q=80",
                "Master shared memory parallelism with OpenMP, message passing with MPI, Amdahl's Law, cache coherence, and GPU acceleration.",
                "Target Degree: MTech / BTech. Scalable high-performance computing. Learn parallel hardware topologies, cache coherence protocols (MESI), multi-threaded shared memory with OpenMP, cluster communication with MPI, and GPU computing fundamentals.",
                "Calculate theoretical speedup using Amdahl's Law and Gustafson's Law\nParallelize CPU-intensive loops and tasks using OpenMP pragmas\nImplement point-to-point and collective communications in MPI (Broadcast, Reduce, Scatter)\nAnalyze cache coherence, false sharing, and NUMA memory architectures\nStructure hybrid OpenMP + MPI programs for distributed supercomputer clusters",
                "Strong proficiency in C or C++ and familiarity with Unix/Linux environments",
                [
                    ("Module 1: Parallel Architecture & Performance Laws", [
                        (1, "HPC Architectures", "Flynn's Taxonomy, Multi-Core CPUs & Supercomputer Clusters", 25, "sPh6S4wIqC4"),
                        (2, "Memory Hierarchies", "Shared vs Distributed Memory, NUMA Architecture & Interconnects", 25, "k8lSgL32_5U"),
                        (3, "Parallel Speedup Laws", "Amdahl's Law vs Gustafson's Law: Limits of Scaling", 30, "Z52G4y1o6Jc"),
                        (4, "Cache Coherence", "Snooping vs Directory Protocols, MESI State Machine & False Sharing", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Shared-Memory Parallelism with OpenMP", [
                        (5, "OpenMP Foundations", "Fork-Join Model, Parallel Regions & Thread Management", 25, "97H0a3Xl-1M"),
                        (6, "Work Sharing", "Loop Work Sharing: Static, Dynamic & Guided Scheduling", 30, "1P8j3J9gE0I"),
                        (7, "Data Scoping", "Shared vs Private Variables, Firstprivate & Reductions", 25, "m2XyE_K0918"),
                        (8, "Synchronization", "Critical Sections, Atomic Operations, Barriers & OpenMP Tasks", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Distributed-Memory Programming with MPI", [
                        (9, "MPI Architecture", "Communicators, Ranks & Process Spawning in MPI", 25, "zS8Y7T36J80"),
                        (10, "Point-to-Point Comms", "MPI_Send & MPI_Recv: Blocking vs Non-Blocking Communication", 35, "6p873K6G5sQ"),
                        (11, "Collective Operations", "MPI_Bcast, MPI_Reduce, MPI_Scatter & MPI_Gather", 35, "vX9vFh33p54"),
                        (12, "Deadlock Prevention", "Avoiding Communication Deadlocks & Safe Buffer Sizing", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Advanced HPC & Acceleration", [
                        (13, "Hybrid Parallelism", "Writing Hybrid MPI + OpenMP Code for Clustered Nodes", 35, "9bZkp7q19f0"),
                        (14, "Parallel Matrix Multiply", "Cannon's & Fox's Parallel Matrix Multiplication Algorithms", 35, "kJQP7kiw5Fk"),
                        (15, "GPU Accelerator Basics", "GPU Architecture, SIMT Execution & Introduction to CUDA", 30, "L_LUpnjgPso"),
                        (16, "Profiling & Benchmarking", "Profiling HPC Applications with gprof, Valgrind & Scalasca", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
        ]

        # Add BTech/MTech courses to pool
        for item in btech_mtech:
            courses.append(self._format_course(item))

        # ---------------------------------------------------------------------
        # DEGREE 3: BCA & BSc IT (8 Courses)
        # ---------------------------------------------------------------------
        bca_bscit = [
            (
                "Enterprise Java Application Development with Spring Boot",
                "enterprise-java-spring-boot",
                "computer-applications",
                "Intermediate",
                "Rahul Sharma",
                "Principal Java Architect & Open Source Contributor",
                "15 hours",
                "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=800&q=80",
                "Master Java OOP, Spring Boot, Spring Data JPA, RESTful APIs, Spring Security, JWT, and enterprise database integration.",
                "Target Degree: BCA / BSc IT. Core enterprise software development. Learn Java Collections, lambda expressions, Spring Inversion of Control (IoC), Dependency Injection, JPA/Hibernate ORM, building REST APIs, and securing endpoints with JWT.",
                "Apply object-oriented patterns and modern Java 17+ stream features\nConfigure Spring Boot dependency injection and application properties\nDesign and persist relational database entities using Spring Data JPA and Hibernate\nConstruct robust RESTful microservices with validation and error handling\nImplement user authentication and authorization using Spring Security and JWT tokens",
                "Basic understanding of core Java syntax and relational databases",
                [
                    ("Module 1: Modern Java & OOP Mastery", [
                        (1, "OOP Foundations", "Encapsulation, Polymorphism, Abstract Classes & Interfaces", 25, "sPh6S4wIqC4"),
                        (2, "Java Collections", "ArrayList, LinkedList, HashMap & Concurrent Collections", 30, "k8lSgL32_5U"),
                        (3, "Streams & Lambdas", "Functional Interfaces, Lambda Expressions & Stream API Pipelines", 30, "Z52G4y1o6Jc"),
                        (4, "Exception Handling", "Checked vs Unchecked Exceptions & Custom Exception Architectures", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Spring Boot Core & Dependency Injection", [
                        (5, "Spring Architecture", "Inversion of Control (IoC), Bean Lifecycle & ApplicationContext", 30, "97H0a3Xl-1M"),
                        (6, "Stereotype Annotations", "@Component, @Service, @Repository, @Controller & @Autowired", 25, "1P8j3J9gE0I"),
                        (7, "Configuration & Profiles", "Application.properties, YAML Configurations & Environment Profiles", 25, "m2XyE_K0918"),
                        (8, "Spring AOP", "Aspect-Oriented Programming: Pointcuts, Advice & Cross-Cutting Concerns", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Spring Data JPA & Database Persistence", [
                        (9, "ORM with Hibernate", "JPA Entity Mapping, Table Relationships (@OneToMany, @ManyToMany)", 30, "zS8Y7T36J80"),
                        (10, "Spring Data Repositories", "CrudRepository, JpaRepository & Query Creation Method Names", 30, "6p873K6G5sQ"),
                        (11, "JPQL & Native Queries", "Writing Custom JPQL Queries, Projections & Pagination Support", 30, "vX9vFh33p54"),
                        (12, "Transaction Management", "@Transactional Semantics, Propagation Behaviors & Isolation Levels", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: REST APIs & Enterprise Security", [
                        (13, "Building REST Controllers", "@RestController, HTTP Verbs, PathVariables & RequestBodies", 30, "9bZkp7q19f0"),
                        (14, "DTOs & Validation", "ModelMapper, Bean Validation (@NotNull, @Size) & Global Error Handling", 25, "kJQP7kiw5Fk"),
                        (15, "Spring Security", "Authentication Providers, Password Encoders (BCrypt) & Security Filter Chain", 35, "L_LUpnjgPso"),
                        (16, "JWT Authentication", "Stateless JWT Token Generation, Verification & Role-Based Authorization", 35, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Cross-Platform Mobile App Development with Flutter & Dart",
                "mobile-app-dev-flutter-dart",
                "computer-applications",
                "Beginner",
                "Priya Nambiar",
                "Mobile App Lead & Google Developer Expert for Flutter",
                "14 hours",
                "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?auto=format&fit=crop&w=800&q=80",
                "Master Dart programming, Flutter widget trees, reactive layouts, Provider state management, and consuming REST APIs.",
                "Target Degree: BCA / BSc IT. Native mobile app development for iOS and Android from a single codebase. Learn Dart syntax, StatelessWidget vs StatefulWidget, building responsive UI layouts, navigation, state management with Provider, and connecting to backend REST APIs.",
                "Write structured, asynchronous Dart code with futures and streams\nBuild responsive multi-screen mobile user interfaces with Flutter widgets\nManage application state cleanly using the Provider pattern\nConsume external REST APIs using http and parse JSON data models\nImplement local device persistence with SQLite / SharedPreferences",
                "Basic understanding of programming logic and object-oriented principles",
                [
                    ("Module 1: Dart Programming Foundations", [
                        (1, "Dart Syntax", "Variables, Data Types, Control Structures & Functions in Dart", 25, "sPh6S4wIqC4"),
                        (2, "Dart OOP", "Classes, Named Constructors, Mixins & Inheritance", 25, "k8lSgL32_5U"),
                        (3, "Async Dart", "Asynchronous Programming: Futures, async/await & Streams", 30, "Z52G4y1o6Jc"),
                        (4, "Collections in Dart", "Lists, Maps, Sets & Collection Operators (spread, collection-if)", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Flutter Widget Tree & UI Design", [
                        (5, "Flutter Architecture", "Declarative UI Paradigm, Element Tree & Render Tree", 25, "97H0a3Xl-1M"),
                        (6, "Stateless vs Stateful", "StatelessWidget vs StatefulWidget & State Lifecycle Methods", 25, "1P8j3J9gE0I"),
                        (7, "Layout Widgets", "Building Responsive Screens: Column, Row, Stack, Expanded & Flex", 30, "m2XyE_K0918"),
                        (8, "Material Design", "Material 3 Theme Tokens, AppBars, FloatingActionButtons & Cards", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: State Management & Navigation", [
                        (9, "Screen Navigation", "Navigator 2.0, Named Routes & Passing Arguments Across Screens", 25, "zS8Y7T36J80"),
                        (10, "Forms & Input", "TextFormFields, Controllers, Input Formatters & Form Validation", 30, "6p873K6G5sQ"),
                        (11, "Provider Pattern", "ChangeNotifier, ChangeNotifierProvider & Consumer Widgets", 35, "vX9vFh33p54"),
                        (12, "Advanced State", "Comparing Provider with Riverpod & BLoC Architecture", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: API Integration & App Publishing", [
                        (13, "HTTP Networking", "Making REST API Requests: GET, POST, Headers & Error Codes", 30, "9bZkp7q19f0"),
                        (14, "JSON Serialization", "Parsing Nested JSON Data with json_serializable Models", 25, "kJQP7kiw5Fk"),
                        (15, "Local Storage", "Caching Data Locally with SharedPreferences & Hive/SQLite", 25, "L_LUpnjgPso"),
                        (16, "App Deployment", "Building Signed Android APKs/App Bundles & iOS App Store Prep", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Modern Web Development with PHP, MVC Architecture & MySQL",
                "modern-web-development-php-mysql",
                "computer-applications",
                "Beginner",
                "Vikram Joshi",
                "Senior Full-Stack Web Developer & Technical Author",
                "13 hours",
                "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=800&q=80",
                "Master PHP 8+, relational MySQL database design, PDO prepared statements, MVC architecture, and session authentication.",
                "Target Degree: BCA / BSc IT. Server-side web engineering fundamentals. Learn modern PHP 8 features, database design with MySQL, writing secure queries with PDO, implementing the Model-View-Controller (MVC) pattern from scratch, and protecting against CSRF and SQL injection.",
                "Write clean, modular server-side scripts using modern PHP 8 syntax\nDesign normalized relational databases in MySQL with primary and foreign keys\nExecute secure database transactions using PHP Data Objects (PDO)\nArchitect complete web applications using the Model-View-Controller (MVC) pattern\nImplement secure session-based authentication and password hashing",
                "Basic understanding of HTML, CSS, and general programming concepts",
                [
                    ("Module 1: PHP Language Core", [
                        (1, "PHP 8 Syntax", "PHP Architecture, Variables, Types, Arrays & Superglobals", 20, "sPh6S4wIqC4"),
                        (2, "Functions & Scope", "User-Defined Functions, Type Hinting, Return Types & Variable Scope", 25, "k8lSgL32_5U"),
                        (3, "Form Processing", "Handling GET and POST Submissions & Sanitizing Form Inputs", 25, "Z52G4y1o6Jc"),
                        (4, "Sessions & Cookies", "Session Management, Cookie Security & Flash Messages", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Relational Databases with MySQL", [
                        (5, "Database Modeling", "Database Normalization (1NF, 2NF, 3NF) & Entity Relationships", 25, "97H0a3Xl-1M"),
                        (6, "SQL Mastery", "DDL and DML: SELECT, INSERT, UPDATE, DELETE & Table Joins", 30, "1P8j3J9gE0I"),
                        (7, "Connecting with PDO", "PHP Data Objects (PDO): DSN, Connection Pooling & Options", 25, "m2XyE_K0918"),
                        (8, "Prepared Statements", "Parameterized Queries: Preventing SQL Injection Completely", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Object-Oriented PHP & MVC Architecture", [
                        (9, "OOP in PHP", "Classes, Objects, Properties, Constructors & Namespaces", 25, "zS8Y7T36J80"),
                        (10, "Inheritance & Interfaces", "Abstract Classes, Interfaces, Traits & Autoloading with Composer", 30, "6p873K6G5sQ"),
                        (11, "MVC Pattern", "Anatomy of MVC: Request Routing, Controller Dispatch & Views", 35, "vX9vFh33p54"),
                        (12, "Building the Model Layer", "Active Record vs Data Mapper Pattern for Database Models", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Web Security & Application Deployment", [
                        (13, "Authentication System", "Secure User Registration, Password Hashing with Argon2/BCrypt", 30, "9bZkp7q19f0"),
                        (14, "CSRF & XSS Defense", "Cross-Site Request Forgery Tokens & Output Encoding", 25, "kJQP7kiw5Fk"),
                        (15, "File Upload Security", "Validating MIME Types, Image Processing & Secure Storage", 25, "L_LUpnjgPso"),
                        (16, "Deployment & Apache/Nginx", "Configuring Virtual Hosts, .htaccess Rewriting & Production Deploy", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Software Quality Assurance, Automated Testing & Selenium",
                "software-qa-automated-testing",
                "computer-applications",
                "Beginner",
                "Sneha Kulkarni",
                "Lead QA Automation Architect & Test Strategy Consultant",
                "13 hours",
                "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=800&q=80",
                "Master manual test case design, black-box techniques, Selenium WebDriver automation, TestNG framework, and API testing with Postman.",
                "Target Degree: BCA / BSc IT. Practical software quality assurance and test automation. Learn SDLC/STLC test processes, Boundary Value Analysis, creating Selenium WebDriver test scripts, Page Object Model (POM), TestNG assertions, and API automated tests.",
                "Design comprehensive test plans, test cases, and traceability matrices\nApply black-box testing techniques: Boundary Value Analysis and Equivalence Partitioning\nAutomate cross-browser web testing using Selenium WebDriver\nStructure modular test automation frameworks using Page Object Model (POM)\nExecute automated API test collections with Postman and Newman CLI",
                "Basic knowledge of HTML, web browsers, and elementary Java or Python",
                [
                    ("Module 1: QA Fundamentals & Manual Testing", [
                        (1, "STLC Lifecycle", "Software Testing Life Cycle (STLC): Requirements to Closure", 25, "sPh6S4wIqC4"),
                        (2, "Test Case Design", "Writing Actionable Test Cases: Pre-conditions, Steps & Expectations", 25, "k8lSgL32_5U"),
                        (3, "Black-Box Techniques", "Boundary Value Analysis (BVA) & Equivalence Class Partitioning", 30, "Z52G4y1o6Jc"),
                        (4, "Defect Life Cycle", "Defect Tracking, Severity vs Priority & Jira Bug Workflows", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Automated Testing with Selenium WebDriver", [
                        (5, "Automation Strategy", "When to Automate: ROI Calculation & Automation Test Pyramid", 20, "97H0a3Xl-1M"),
                        (6, "Locating Web Elements", "Element Locators: ID, Name, CSS Selectors & XPath Strategies", 30, "1P8j3J9gE0I"),
                        (7, "Browser Interactions", "Clicking, Typing, Dropdowns, Checkboxes & Alert Handling", 25, "m2XyE_K0918"),
                        (8, "Synchronization", "Handling Dynamic Elements: Implicit, Explicit & Fluent Waits", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: TestNG & Page Object Model (POM)", [
                        (9, "TestNG Framework", "TestNG Annotations (@Test, @BeforeMethod), Assertions & Groups", 30, "zS8Y7T36J80"),
                        (10, "Data-Driven Testing", "Executing Parameterized Tests with TestNG DataProviders & Excel", 30, "6p873K6G5sQ"),
                        (11, "Page Object Model", "Separation of Concerns: Implementing Page Object Model (POM)", 35, "vX9vFh33p54"),
                        (12, "Test Reporting", "Generating Rich HTML Reports with Allure & ExtentReports", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: API Testing & CI/CD Pipelines", [
                        (13, "API Testing Basics", "HTTP Status Codes, Headers, JSON Payloads & Postman Collections", 25, "9bZkp7q19f0"),
                        (14, "Postman Test Scripts", "Writing JavaScript Assertions in Postman for Response Validation", 30, "kJQP7kiw5Fk"),
                        (15, "Newman Automation", "Automating Postman Collections via Command Line with Newman", 25, "L_LUpnjgPso"),
                        (16, "CI/CD Integration", "Integrating Automated Test Suites into GitHub Actions Pipelines", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Linux System Administration, Bash Scripting & Automation",
                "linux-system-administration-bash",
                "computer-applications",
                "Beginner",
                "Anand Venkataraman",
                "Senior Linux Systems Engineer & Red Hat Certified Architect",
                "14 hours",
                "https://images.unsplash.com/photo-1629654297299-c8506221ca97?auto=format&fit=crop&w=800&q=80",
                "Master the Linux shell, file permissions, user management, systemd services, cron automation, SSH keys, and advanced Bash scripts.",
                "Target Degree: BCA / BSc IT. Practical Linux operating system engineering. Learn the Linux filesystem hierarchy, file permissions (chmod/chown), process monitoring, systemd service management, package managers, SSH key hardening, and writing automated Bash scripts.",
                "Navigate and operate Linux systems proficiently via the command-line interface\nConfigure file permissions, ownership, ACLs, and sticky bit protections\nManage system users, groups, sudo privileges, and SSH key authentication\nControl systemd services, daemons, background jobs, and cron automation\nWrite robust, error-handled Bash scripts for automated system maintenance",
                "No prior Linux experience required. Basic computer literacy",
                [
                    ("Module 1: Command Line & Filesystem Hierarchy", [
                        (1, "Linux Architecture", "The Linux Kernel, Shell & Filesystem Hierarchy Standard (FHS)", 25, "sPh6S4wIqC4"),
                        (2, "File Manipulation", "Core Utilities: ls, cd, cp, mv, rm, find, grep & xargs", 25, "k8lSgL32_5U"),
                        (3, "I/O Redirection", "Standard Input, Output, Error Redirection (>, >>, 2>) & Pipes (|)", 25, "Z52G4y1o6Jc"),
                        (4, "Text Processing", "Stream Editing: head, tail, cut, sort, uniq, sed & awk Basics", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Permissions, Users & Storage", [
                        (5, "File Permissions", "Octal & Symbolic Permissions (chmod), Ownership (chown, chgrp)", 25, "97H0a3Xl-1M"),
                        (6, "Special Permissions", "SUID, SGID, Sticky Bit & POSIX Access Control Lists (ACLs)", 30, "1P8j3J9gE0I"),
                        (7, "User & Group Admin", "Creating Users (useradd), Modifying Groups & Sudoers File Security", 25, "m2XyE_K0918"),
                        (8, "Disk & Filesystem", "Partitioning (fdisk), Formatting (ext4/xfs), Mounting & df/du", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Process & Service Management", [
                        (9, "Process Monitoring", "Viewing & Managing Processes: ps, top, htop, kill & Signals", 25, "zS8Y7T36J80"),
                        (10, "Systemd Services", "Managing Daemons with systemctl & Writing Custom Unit Files", 30, "6p873K6G5sQ"),
                        (11, "Task Automation", "Automating Recurring Tasks with Crontab & Systemd Timers", 25, "vX9vFh33p54"),
                        (12, "System Logs", "Monitoring System Logs with journalctl & Logrotate Configuration", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Networking & Advanced Bash Scripting", [
                        (13, "Network Configuration", "IP Configuration, DNS, ping, netstat, ss, curl & Firewall (UFW)", 25, "9bZkp7q19f0"),
                        (14, "SSH Security", "Hardening SSH: Key Pairs, Disabling Root Login & Fail2Ban", 25, "kJQP7kiw5Fk"),
                        (15, "Bash Scripting Core", "Variables, Positional Parameters, Conditionals (if/test) & Loops", 30, "L_LUpnjgPso"),
                        (16, "Production Scripts", "Error Handling (set -euo pipefail), Functions & Log Automation", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Computer Networking, TCP/IP Protocol Suite & Socket Programming",
                "computer-networks-tcp-ip",
                "computer-applications",
                "Intermediate",
                "Dr. George Kurian",
                "Network Systems Researcher & Internet Infrastructure Specialist",
                "15 hours",
                "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=800&q=80",
                "Master OSI/TCP-IP models, IPv4/IPv6 subnetting, routing protocols (OSPF/BGP), TCP flow control, and Python socket programming.",
                "Target Degree: BCA / BSc IT. Core computer networking and internet architecture. Learn data encapsulation, Ethernet frames, IP subnetting and CIDR notation, routing algorithms, TCP three-way handshake, flow control, DNS, and client-server socket programming.",
                "Analyze network packet encapsulation across OSI and TCP/IP protocol layers\nCalculate IPv4 subnets, network masks, broadcast addresses, and CIDR blocks\nUnderstand routing protocols: Distance Vector (RIP) vs Link State (OSPF) vs BGP\nExamine TCP reliability mechanisms: 3-way handshake, sliding window, and congestion control\nDevelop client-server network applications using Python socket programming",
                "Basic understanding of computer architecture and elementary programming",
                [
                    ("Module 1: Network Models & Physical/Data Link Layers", [
                        (1, "Reference Models", "Comparing the 7-Layer OSI Model with 4-Layer TCP/IP Model", 25, "sPh6S4wIqC4"),
                        (2, "Data Link Layer", "Framing, Error Detection (CRC) & MAC Address Structure", 25, "k8lSgL32_5U"),
                        (3, "Ethernet & Switches", "CSMA/CD, Full-Duplex Ethernet & Switch CAM Table Learning", 30, "Z52G4y1o6Jc"),
                        (4, "VLANs & Trunking", "Virtual LANs (VLANs), 802.1Q Trunking & Inter-VLAN Routing", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Network Layer & IP Addressing", [
                        (5, "IPv4 Addressing", "IPv4 Address Classes, Classless Addressing & CIDR Notation", 30, "97H0a3Xl-1M"),
                        (6, "Subnetting Math", "Variable-Length Subnet Masking (VLSM) Calculations Step-by-Step", 35, "1P8j3J9gE0I"),
                        (7, "ARP & ICMP", "Address Resolution Protocol (ARP), ICMP & Ping/Traceroute Logic", 25, "m2XyE_K0918"),
                        (8, "Routing Algorithms", "Dijkstra Link-State (OSPF) vs Bellman-Ford Distance Vector (RIP)", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Transport Layer (TCP vs UDP)", [
                        (9, "Transport Protocols", "TCP Connection-Oriented vs UDP Connectionless Reliability", 25, "zS8Y7T36J80"),
                        (10, "TCP Handshake", "TCP Three-Way Handshake (SYN, SYN-ACK, ACK) & Teardown (FIN/RST)", 30, "6p873K6G5sQ"),
                        (11, "Flow & Congestion", "TCP Sliding Window Flow Control, Slow Start & Congestion Avoidance", 35, "vX9vFh33p54"),
                        (12, "Network Address Translation", "NAT, PAT (Port Address Translation) & Private IP Ranges", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Application Layer & Socket Programming", [
                        (13, "DNS Architecture", "Domain Name System (DNS): Root, TLD, Authoritative & Recursive", 25, "9bZkp7q19f0"),
                        (14, "HTTP Protocol", "HTTP/1.1 vs HTTP/2 vs HTTP/3 (QUIC) & HTTPS TLS Handshake", 30, "kJQP7kiw5Fk"),
                        (15, "Socket Programming", "Building TCP Client-Server Sockets in Python from Scratch", 35, "L_LUpnjgPso"),
                        (16, "Multi-Threaded Sockets", "Concurrent Client Handling with Multi-Threaded Network Sockets", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Object-Oriented Programming & Standard Template Library in C++",
                "cpp-oop-stl-programming",
                "computer-applications",
                "Intermediate",
                "Prof. Meera Pillai",
                "Computer Science Faculty & C++ Core Standards Educator",
                "15 hours",
                "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&w=800&q=80",
                "Master modern C++, memory pointers, constructor mechanics, virtual polymorphism, operator overloading, and STL containers/algorithms.",
                "Target Degree: BCA / BSc CS. Deep-dive into modern C++ and OOP. Learn memory layout, stack vs heap, raw vs smart pointers (unique_ptr, shared_ptr), copy/move semantics, runtime polymorphism via vtables, and standard template library (STL) containers.",
                "Manage dynamic heap memory safely using RAII and C++ smart pointers\nDesign class hierarchies using encapsulation, inheritance, and abstract classes\nImplement runtime polymorphism using virtual functions and understand vtable mechanics\nOverload arithmetic, comparison, and stream insertion operators\nUtilize C++ STL containers (vector, list, map, set) and algorithms (sort, find) efficiently",
                "Basic programming knowledge in C or another structured language",
                [
                    ("Module 1: C++ Foundations & Dynamic Memory", [
                        (1, "C to C++ Transition", "C++ Compilation Model, Namespaces, References & Stream I/O", 25, "sPh6S4wIqC4"),
                        (2, "Pointers & References", "Pointer Arithmetic, References, Memory Addresses & Const Correctness", 25, "k8lSgL32_5U"),
                        (3, "Dynamic Memory", "Stack vs Heap Allocation: new, delete, malloc vs new Differences", 30, "Z52G4y1o6Jc"),
                        (4, "Smart Pointers", "RAII Idiom: std::unique_ptr, std::shared_ptr & std::weak_ptr", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Object-Oriented Core in C++", [
                        (5, "Classes & Objects", "Class Definition, Access Specifiers, This Pointer & Encapsulation", 25, "97H0a3Xl-1M"),
                        (6, "Constructors & Destructors", "Default, Parameterized, Copy Constructors & Deep vs Shallow Copy", 30, "1P8j3J9gE0I"),
                        (7, "Move Semantics", "Rvalue References (&&), std::move & Move Constructors in C++11", 35, "m2XyE_K0918"),
                        (8, "Operator Overloading", "Overloading Operators (+, ==, <<, >>) & Friend Functions", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Inheritance & Polymorphism", [
                        (9, "Inheritance Types", "Single, Multiple, Hierarchical Inheritance & Access Levels", 25, "zS8Y7T36J80"),
                        (10, "Virtual Functions", "Virtual Functions, Runtime Polymorphism & Vtable / Vptr Internals", 35, "6p873K6G5sQ"),
                        (11, "Abstract Classes", "Pure Virtual Functions & Abstract Base Interfaces in C++", 25, "vX9vFh33p54"),
                        (12, "Diamond Problem", "Virtual Base Classes & Resolving Multiple Inheritance Ambiguity", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Templates & The Standard Template Library (STL)", [
                        (13, "Function & Class Templates", "Generic Programming: Template Functions, Classes & Specialization", 30, "9bZkp7q19f0"),
                        (14, "Sequential Containers", "std::vector, std::list, std::deque & Memory Growth Strategies", 30, "kJQP7kiw5Fk"),
                        (15, "Associative Containers", "std::map, std::set (Red-Black Trees) vs std::unordered_map (Hashing)", 30, "L_LUpnjgPso"),
                        (16, "STL Algorithms", "Using std::sort, std::find, std::transform & Lambda Predicates", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Discrete Mathematics, Graph Theory & Computability for IT",
                "discrete-mathematics-computing",
                "computer-applications",
                "Intermediate",
                "Dr. Rameshwar Nath",
                "Professor of Theoretical Computer Science & Discrete Mathematics",
                "15 hours",
                "https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=800&q=80",
                "Master propositional logic, proof techniques, set relations, permutations/combinations, recurrence relations, and graph algorithms.",
                "Target Degree: BCA / BSc CS. Mathematical foundations of computing. Learn truth tables, mathematical induction, Pigeonhole Principle, recurrence relations, graph connectivity, Euler and Hamiltonian paths, and trees.",
                "Construct and evaluate propositional and predicate logic expressions\nConstruct rigorous mathematical proofs using direct, contrapositive, and contradiction methods\nApply mathematical induction to verify summation and divisibility formulas\nSolve linear recurrence relations using characteristic equations\nAnalyze graphs and trees using shortest-path, minimum spanning tree, and traversal algorithms",
                "High school algebra and familiarity with basic programming logic",
                [
                    ("Module 1: Mathematical Logic & Proof Techniques", [
                        (1, "Propositional Logic", "Propositions, Truth Tables, Logical Equivalences & De Morgan's Laws", 25, "sPh6S4wIqC4"),
                        (2, "Predicates & Quantifiers", "Universal (∀) and Existential (∃) Quantifiers & Nested Negations", 25, "k8lSgL32_5U"),
                        (3, "Rules of Inference", "Modus Ponens, Modus Tollens, Syllogisms & Formal Proof Sequences", 25, "Z52G4y1o6Jc"),
                        (4, "Proof Strategies", "Direct Proof, Proof by Contraposition & Proof by Contradiction", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Sets, Relations & Induction", [
                        (5, "Set Operations", "Sets, Subsets, Cartesian Products, Power Sets & Venn Identities", 20, "97H0a3Xl-1M"),
                        (6, "Relations & Properties", "Reflexive, Symmetric, Transitive Relations & Equivalence Classes", 30, "1P8j3J9gE0I"),
                        (7, "Functions & Cardinality", "Injective, Surjective, Bijective Functions & Countable/Uncountable Sets", 25, "m2XyE_K0918"),
                        (8, "Mathematical Induction", "Principle of Mathematical Induction & Strong Induction Proofs", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Combinatorics & Recurrence Relations", [
                        (9, "Counting Principles", "Product Rule, Sum Rule & The Pigeonhole Principle Applications", 25, "zS8Y7T36J80"),
                        (10, "Permutations & Combinations", "Binomial Theorem, Pascal's Identity & Combinatorial Proofs", 30, "6p873K6G5sQ"),
                        (11, "Recurrence Relations", "Modeling Problems with Recurrence: Towers of Hanoi & Fibonacci", 30, "vX9vFh33p54"),
                        (12, "Solving Recurrences", "Solving Homogeneous & Non-Homogeneous Linear Recurrence Relations", 35, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Graph Theory & Trees", [
                        (13, "Graph Fundamentals", "Vertices, Edges, Degrees, Handshaking Lemma & Subgraphs", 25, "9bZkp7q19f0"),
                        (14, "Paths & Circuits", "Eulerian Paths/Circuits (Fleury's) vs Hamiltonian Paths/Circuits", 30, "kJQP7kiw5Fk"),
                        (15, "Graph Representation", "Adjacency Matrix, Adjacency List & Isomorphism Checking", 25, "L_LUpnjgPso"),
                        (16, "Trees & Spanning Trees", "Properties of Trees, Spanning Trees & Prim's / Kruskal's Algorithms", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
        ]

        # Add BCA/BSc IT courses to pool
        for item in bca_bscit:
            courses.append(self._format_course(item))

        # ---------------------------------------------------------------------
        # DEGREE 4: BCom (Commerce, Banking & Taxation) (8 Courses)
        # ---------------------------------------------------------------------
        bcom = [
            (
                "Financial Accounting: Journals, Ledgers & Final Accounts",
                "financial-accounting-principles",
                "commerce-finance",
                "Beginner",
                "Prof. Hemant K. Gupta, FCA",
                "Fellow Chartered Accountant & Professor of Accountancy",
                "14 hours",
                "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800&q=80",
                "Master double-entry bookkeeping, journal entries, ledger accounts, trial balances, bank reconciliations, and balance sheets.",
                "Target Degree: BCom. Foundational financial accounting principles. Learn debit and credit rules, recording transactions, ledger balancing, trial balance preparation, bank reconciliation statements (BRS), and compiling final accounts with adjustments.",
                "Apply the Golden Rules of Accounting to record transactions in the General Journal\nPost entries to General Ledgers and calculate periodic account balances\nPrepare a verified Trial Balance and rectify accounting errors\nReconcile cash book with bank passbook balances using BRS\nConstruct Trading Account, Profit & Loss Account, and Balance Sheet with adjustments",
                "Basic arithmetic skills and interest in financial record keeping",
                [
                    ("Module 1: Principles of Accounting & Journalizing", [
                        (1, "Accounting Framework", "GAAP Principles, Business Entity, Money Measurement & Accrual", 25, "sPh6S4wIqC4"),
                        (2, "Accounting Equation", "Assets = Liabilities + Equity: Transaction Impact Analysis", 25, "k8lSgL32_5U"),
                        (3, "Golden Rules", "Personal, Real, and Nominal Accounts: Debit & Credit Rules", 25, "Z52G4y1o6Jc"),
                        (4, "Journal Entries", "Recording Complex Business Transactions in the General Journal", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Ledgers, Cash Books & Trial Balance", [
                        (5, "Ledger Posting", "Posting Journal Entries to T-Accounts & Balancing Ledgers", 25, "97H0a3Xl-1M"),
                        (6, "Subsidiary Books", "Purchase, Sales, Returns Books & Petty Cash Imprest System", 25, "1P8j3J9gE0I"),
                        (7, "Trial Balance", "Preparing the Trial Balance & Detecting Accounting Discrepancies", 25, "m2XyE_K0918"),
                        (8, "Rectification of Errors", "One-Sided vs Two-Sided Errors & Suspense Account Adjustments", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Reconciliation & Depreciation", [
                        (9, "Bank Reconciliation", "Causes of Discrepancies between Cash Book & Bank Passbook", 25, "zS8Y7T36J80"),
                        (10, "BRS Preparation", "Preparing Bank Reconciliation Statements Step-by-Step", 30, "6p873K6G5sQ"),
                        (11, "Depreciation Concepts", "Causes of Depreciation & Straight-Line Method (SLM)", 25, "vX9vFh33p54"),
                        (12, "Written Down Value", "Written Down Value (WDV) Method & Accounting for Asset Sales", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Final Accounts & Financial Statements", [
                        (13, "Trading Account", "Calculating Cost of Goods Sold (COGS) & Gross Profit", 25, "9bZkp7q19f0"),
                        (14, "Profit & Loss Account", "Operating vs Non-Operating Expenses & Net Profit Determination", 25, "kJQP7kiw5Fk"),
                        (15, "Balance Sheet", "Marshalling Assets & Liabilities: Liquidity vs Permanence", 30, "L_LUpnjgPso"),
                        (16, "Year-End Adjustments", "Accounting for Closing Stock, Outstanding Expenses & Bad Debts", 35, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Indian Corporate Taxation, Income Tax & GST Compliance",
                "corporate-tax-gst-compliance",
                "commerce-finance",
                "Intermediate",
                "CA Shweta Agrawal",
                "Corporate Tax Advisor & GST Practice Specialist",
                "15 hours",
                "https://images.unsplash.com/photo-1586486855514-8c633cc6fd38?auto=format&fit=crop&w=800&q=80",
                "Master Income Tax heads, corporate deductions (Chapter VI-A), TDS filing, GST tax invoices, Input Tax Credit (ITC), and returns.",
                "Target Degree: BCom. Practical direct and indirect taxation. Learn residential status, computing income under Salary, House Property, and Business/Profession, corporate tax slabs, TDS, and GST compliance including GSTR-1 and GSTR-3B.",
                "Determine individual and corporate residential status for tax liability\nCompute taxable income under Salaries, House Property, and PGBP\nApply Chapter VI-A deductions (80C, 80D, 80G) and calculate tax payable\nExecute Tax Deducted at Source (TDS) calculations and quarterly e-filing\nNavigate the Goods and Services Tax (GST) framework, Input Tax Credit, and GSTR returns",
                "Familiarity with financial statements and basic accounting",
                [
                    ("Module 1: Income Tax Fundamentals & Residential Status", [
                        (1, "Income Tax Basics", "Tax Structure, Finance Acts, Assessment Year vs Previous Year", 25, "sPh6S4wIqC4"),
                        (2, "Residential Status", "Determining Residential Status for Individuals & Companies", 25, "k8lSgL32_5U"),
                        (3, "Scope of Total Income", "Global Income Incidence & Non-Resident Indian (NRI) Taxation", 25, "Z52G4y1o6Jc"),
                        (4, "Exempted Incomes", "Incomes Exempt from Tax under Section 10 (Agricultural Income)", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Heads of Income & Corporate Profits", [
                        (5, "Income from Salaries", "Salary Structure, Allowances, Perquisites & Standard Deduction", 30, "97H0a3Xl-1M"),
                        (6, "Income from House Property", "Annual Value, Municipal Taxes & Standard 30% Deduction", 25, "1P8j3J9gE0I"),
                        (7, "Profits from Business (PGBP)", "Allowable & Disallowable Business Expenses, Section 37", 35, "m2XyE_K0918"),
                        (8, "Capital Gains & Other Sources", "Short-Term vs Long-Term Capital Gains & Dividend Taxation", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Deductions, TDS & Corporate Tax Slabs", [
                        (9, "Chapter VI-A Deductions", "Tax Saving Deductions: Section 80C, 80D, 80E, 80G", 25, "zS8Y7T36J80"),
                        (10, "Corporate Tax Slabs", "Domestic Company Tax Rates (Section 115BAA) & MAT (Section 115JB)", 30, "6p873K6G5sQ"),
                        (11, "TDS & Advance Tax", "TDS Sections (192, 194C, 194J) & Advance Tax Installment Deadlines", 30, "vX9vFh33p54"),
                        (12, "ITR Filing Procedures", "Income Tax Return Types (ITR-1 to ITR-6) & Online E-Filing", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Goods & Services Tax (GST) Compliance", [
                        (13, "GST Framework", "CGST, SGST, IGST Framework & Dual GST Architecture", 25, "9bZkp7q19f0"),
                        (14, "Supply & Tax Invoicing", "Concept of Supply, Place of Supply & Tax Invoice Mandatory Fields", 30, "kJQP7kiw5Fk"),
                        (15, "Input Tax Credit (ITC)", "Eligible ITC, Blocked Credits (Section 17(5)) & ITC Reversal", 35, "L_LUpnjgPso"),
                        (16, "GST Returns & E-Way Bill", "Filing GSTR-1, GSTR-3B & Generating E-Way Bills for Cargo", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Cost & Management Accounting: Marginal Costing & Budgeting",
                "cost-management-accounting",
                "commerce-finance",
                "Intermediate",
                "Prof. B. M. L. Murthy, CMA",
                "Certified Management Accountant & Cost Audit Fellow",
                "14 hours",
                "https://images.unsplash.com/photo-1554224154-26032ffc0d07?auto=format&fit=crop&w=800&q=80",
                "Master cost sheets, material/labor control, marginal costing, break-even analysis (CVP), standard costing, and flexible budgeting.",
                "Target Degree: BCom. Cost accounting and management decisions. Learn the preparation of cost sheets, EOQ in material procurement, labor wage incentive plans, absorption vs marginal costing, break-even charts, and variance analysis.",
                "Prepare structured Cost Sheets determining Prime Cost, Works Cost, and Total Cost\nCalculate material inventory controls: Reorder Level, Minimum Level, and Danger Level\nExecute Marginal Costing and Break-Even Point (BEP) calculations\nPerform Margin of Safety (MoS) and Cost-Volume-Profit (CVP) decision analysis\nCompute Material and Labor Variances in Standard Costing systems",
                "Basic understanding of financial accounting concepts",
                [
                    ("Module 1: Cost Concepts & The Cost Sheet", [
                        (1, "Cost Accounting Scope", "Cost Accounting vs Financial Accounting & Cost Centers", 20, "sPh6S4wIqC4"),
                        (2, "Classification of Costs", "Fixed, Variable, Semi-Variable, Direct vs Indirect Costs", 25, "k8lSgL32_5U"),
                        (3, "The Cost Sheet", "Preparing the Cost Sheet: Prime Cost, Factory Cost & Cost of Sales", 30, "Z52G4y1o6Jc"),
                        (4, "Reconciliation", "Reconciliation of Cost and Financial Accounts Profits", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Material & Labor Cost Control", [
                        (5, "Material Procurement", "Purchase Orders, Goods Received Notes (GRN) & Store Ledgers", 25, "97H0a3Xl-1M"),
                        (6, "Inventory Pricing Methods", "FIFO, LIFO & Weighted Average Price Methods of Pricing Material", 30, "1P8j3J9gE0I"),
                        (7, "Labor Cost Accounting", "Timekeeping, Idle Time, Overtime & Labor Turnover Rates", 25, "m2XyE_K0918"),
                        (8, "Incentive Wage Plans", "Taylor's Differential, Halsey & Rowan Premium Bonus Systems", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Overhead Allocation & Marginal Costing", [
                        (9, "Overhead Allocation", "Primary and Secondary Distribution of Factory Overheads", 30, "zS8Y7T36J80"),
                        (10, "Absorption vs Marginal", "Absorption Costing vs Marginal Costing Operating Income", 25, "6p873K6G5sQ"),
                        (11, "Cost-Volume-Profit (CVP)", "Contribution Margin, P/V Ratio & Break-Even Point (BEP)", 35, "vX9vFh33p54"),
                        (12, "Decision Making", "Make or Buy Decisions, Optimum Product Mix & Shutdown Points", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Standard Costing & Budgetary Control", [
                        (13, "Standard Costing", "Setting Standard Costs & Establishing Variance Frameworks", 25, "9bZkp7q19f0"),
                        (14, "Material Variances", "Material Cost, Price & Usage Variance Calculations", 30, "kJQP7kiw5Fk"),
                        (15, "Labor Variances", "Labor Cost, Rate, Efficiency & Idle Time Variance Calculations", 30, "L_LUpnjgPso"),
                        (16, "Budgetary Control", "Cash Budgets, Flexible Budgets & Zero-Based Budgeting (ZBB)", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Commercial Banking Operations & Insurance Risk Underwriting",
                "commercial-banking-insurance",
                "commerce-finance",
                "Beginner",
                "Ravindra Prasad, CAIIB",
                "Former General Manager, State Bank of India & Banking Fellow",
                "13 hours",
                "https://images.unsplash.com/photo-1501167786227-4cba60f6d58f?auto=format&fit=crop&w=800&q=80",
                "Master commercial banking functions, credit appraisal, NPA recovery, payment gateways (NEFT/RTGS/UPI), and insurance underwriting.",
                "Target Degree: BCom. Retail and commercial banking operations. Learn the banker-customer legal relationship, credit underwriting and loan appraisal, Non-Performing Assets (NPAs) and SARFAESI, digital payment clearing systems, and insurance principles.",
                "Understand the legal rights and obligations in the Banker-Customer relationship\nAnalyze credit appraisal techniques and working capital assessment (Tandon/Chore committee)\nManage Non-Performing Assets (NPAs), provisioning norms, and SARFAESI recovery\nExamine digital banking channels: NEFT, RTGS, IMPS, UPI, and core banking systems\nApply insurance principles: Utmost Good Faith, Insurable Interest, Indemnity, and Subrogation",
                "General understanding of money, banking, and business transactions",
                [
                    ("Module 1: Commercial Banking & Central Bank Functions", [
                        (1, "Banking Structure", "Evolution of Banking, Schedule Commercial Banks & RBI Role", 25, "sPh6S4wIqC4"),
                        (2, "Monetary Policy Tools", "Cash Reserve Ratio (CRR), SLR, Repo Rate & Reverse Repo", 25, "k8lSgL32_5U"),
                        (3, "Banker & Customer", "Debtor-Creditor Relationship, Banker's Lien & Right of Set-off", 25, "Z52G4y1o6Jc"),
                        (4, "Deposit Accounts", "Savings, Current, Fixed & Recurring Deposits: KYC Guidelines", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Lending Operations & Credit Management", [
                        (5, "Types of Credit", "Loans, Cash Credits, Overdrafts & Bill Discounting", 25, "97H0a3Xl-1M"),
                        (6, "Credit Appraisal", "The 5 Cs of Credit & Financial Ratio Analysis for Borrowers", 30, "1P8j3J9gE0I"),
                        (7, "Securities for Advances", "Pledge, Hypothecation, Mortgage & Lien Differences", 30, "m2XyE_K0918"),
                        (8, "NPA Management", "Asset Classification (Substandard, Doubtful, Loss) & SARFAESI Act", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Digital Banking & Payment Settlement", [
                        (9, "Electronic Clearing", "NEFT, RTGS, IMPS & Automated Clearing House (NACH)", 25, "zS8Y7T36J80"),
                        (10, "UPI Architecture", "Unified Payments Interface (UPI), NPCI & Virtual Payment Addresses", 25, "6p873K6G5sQ"),
                        (11, "Plastic Money & Fraud", "Credit/Debit Card Settlement, EMV Chips & Phishing Prevention", 25, "vX9vFh33p54"),
                        (12, "Core Banking Systems", "Centralized Online Real-Time Electronic (CORE) Banking Architecture", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Principles of Insurance & Underwriting", [
                        (13, "Insurance Principles", "Insurable Interest, Utmost Good Faith, Indemnity & Proximate Cause", 30, "9bZkp7q19f0"),
                        (14, "Life Insurance", "Term Life, Whole Life, Endowment Policies & Mortality Tables", 25, "kJQP7kiw5Fk"),
                        (15, "General Insurance", "Fire, Marine, Motor & Health Insurance Underwriting Norms", 30, "L_LUpnjgPso"),
                        (16, "Claim Settlement", "Surveyor Assessment, Reinsurance Principles & IRDAI Regulations", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Auditing Standards, Internal Controls & Corporate Governance",
                "auditing-standards-corporate-governance",
                "commerce-finance",
                "Intermediate",
                "CA Pradeep Mathur",
                "Partner, Statutory Audit Practice & Quality Reviewer",
                "14 hours",
                "https://images.unsplash.com/photo-1450133064473-71024230f91b?auto=format&fit=crop&w=800&q=80",
                "Master auditing standards (SA), internal audit, audit sampling, vouching, asset verification, auditor liabilities, and governance.",
                "Target Degree: BCom. Audit theory, statutory compliance, and corporate governance. Learn audit planning, risk assessment (SA 315), test of controls, vouching sales and purchases, verification of assets, and drafting audit reports (CARO).",
                "Explain the nature, scope, and ethical principles governing statutory audits\nEvaluate internal control systems and execute audit sampling procedures\nExecute thorough vouching of transactions and physical verification of assets\nDraft audit reports with Unqualified, Qualified, Adverse, or Disclaimer opinions\nUnderstand corporate governance norms and audit committee obligations under the Companies Act",
                "Proficiency in financial accounting and basic corporate law",
                [
                    ("Module 1: Principles & Framework of Auditing", [
                        (1, "Nature of Auditing", "Definition, Objectives, Errors vs Fraud & Inherent Limitations", 25, "sPh6S4wIqC4"),
                        (2, "Auditing Standards", "Role of ICAI Standards on Auditing (SAs) & Professional Ethics", 25, "k8lSgL32_5U"),
                        (3, "Audit Planning", "Audit Strategy, Audit Program & Documentation (Audit Working Papers)", 25, "Z52G4y1o6Jc"),
                        (4, "Materiality in Auditing", "Determining Materiality (SA 320) & Assessing Audit Risk (SA 315)", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Internal Control & Audit Procedures", [
                        (5, "Internal Check & Control", "Internal Control System Design, Segregation of Duties & Checklists", 25, "97H0a3Xl-1M"),
                        (6, "Internal Audit", "Statutory vs Internal Audit & Operational Effectiveness Testing", 25, "1P8j3J9gE0I"),
                        (7, "Audit Sampling", "Statistical vs Non-Statistical Sampling & Tolerable Error Limits", 30, "m2XyE_K0918"),
                        (8, "Audit Evidence", "Evaluating Audit Evidence: Reliability, Inquiry & External Confirmations", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Vouching & Verification", [
                        (9, "Concept of Vouching", "Vouching as the Backbone of Auditing: Examining Vouchers & Authorizations", 25, "zS8Y7T36J80"),
                        (10, "Vouching Transactions", "Vouching Cash Receipts, Cash Payments, Credit Sales & Purchases", 30, "6p873K6G5sQ"),
                        (11, "Verification of Assets", "Verification & Valuation of Fixed Assets, Investments & Inventory", 30, "vX9vFh33p54"),
                        (12, "Verification of Liabilities", "Verifying Borrowings, Trade Payables & Contingent Liabilities", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Company Audit & Corporate Governance", [
                        (13, "Company Auditor", "Qualifications, Disqualifications, Appointment & Removal under Companies Act", 30, "9bZkp7q19f0"),
                        (14, "Auditor's Report", "Audit Report Structure: Unmodified, Qualified, Adverse & Disclaimer Opinions", 30, "kJQP7kiw5Fk"),
                        (15, "CARO Reporting", "Companies (Auditor's Report) Order (CARO) Compliance Checklist", 30, "L_LUpnjgPso"),
                        (16, "Corporate Governance", "Audit Committee Composition, Whistleblower Policy & Clause 49", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Equity Research, Stock Market Valuation & Portfolio Management",
                "equity-research-stock-market-investing",
                "commerce-finance",
                "Intermediate",
                "Gaurav Khandelwal, CFA",
                "Senior Equity Research Analyst & Portfolio Manager",
                "15 hours",
                "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80",
                "Master stock market mechanics, reading company 10-K/Annual Reports, financial ratio analysis, technical charting, and portfolio risk.",
                "Target Degree: BCom. Practical equity markets and security analysis. Learn primary/secondary exchange mechanisms (NSE, BSE, SEBI), decoding balance sheets and earnings transcripts, P/E and EV/EBITDA valuation, technical indicators (RSI, Moving Averages), and portfolio diversification.",
                "Navigate primary and secondary stock exchange trading mechanisms (SEBI regulations)\nConduct comprehensive fundamental equity research on listed corporate balance sheets\nAnalyze financial ratios: Return on Equity (ROE), ROCE, Operating Margins, and Debt-to-Equity\nExecute technical analysis using candlestick patterns, support/resistance, and RSI\nConstruct an optimized multi-asset portfolio balancing systematic vs unsystematic risk",
                "Basic understanding of financial statements and corporate accounting",
                [
                    ("Module 1: Stock Market Mechanics & Ecosystem", [
                        (1, "Indian Capital Markets", "NSE, BSE, Depository Participants (NSDL, CDSL) & SEBI Oversight", 25, "sPh6S4wIqC4"),
                        (2, "Trading & Settlement", "Order Books, Market Orders, Limit Orders & T+1 Settlement Cycles", 25, "k8lSgL32_5U"),
                        (3, "Indices & Market Cap", "Nifty 50, Sensex Calculation (Free-Float Market Cap) & Sectors", 25, "Z52G4y1o6Jc"),
                        (4, "Corporate Actions", "Dividends, Stock Splits, Bonus Issues, Rights & Buybacks", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Fundamental Analysis & Financial Statements", [
                        (5, "Reading Annual Reports", "Navigating 10-K / Annual Reports: Director's Report & Notes to Accounts", 30, "97H0a3Xl-1M"),
                        (6, "Income Statement Analysis", "Topline Revenue Growth, Operating Leverage & EBITDA Margins", 30, "1P8j3J9gE0I"),
                        (7, "Balance Sheet Health", "Working Capital, Debt-to-Equity, Solvency & Net Fixed Assets", 30, "m2XyE_K0918"),
                        (8, "Cash Flow Reality", "Operating Cash Flow vs Net Profit: Quality of Earnings Checks", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Valuation Multiples & Modeling", [
                        (9, "Price-to-Earnings (P/E)", "Trailing vs Forward P/E, PEG Ratio & Cyclical P/E Pitfalls", 30, "zS8Y7T36J80"),
                        (10, "EV Multiples", "Enterprise Value (EV), EV/EBITDA & Price-to-Book (P/B) Multiples", 30, "6p873K6G5sQ"),
                        (11, "DuPont Analysis", "3-Step and 5-Step DuPont Breakdown of Return on Equity (ROE)", 30, "vX9vFh33p54"),
                        (12, "Target Price Modeling", "Building Target Price Projections & Writing Equity Research Reports", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Technical Analysis & Portfolio Theory", [
                        (13, "Candlestick Patterns", "Doji, Hammer, Engulfing Patterns & Support/Resistance Levels", 30, "9bZkp7q19f0"),
                        (14, "Technical Indicators", "Moving Averages (50/200 DMA), MACD & Relative Strength Index (RSI)", 30, "kJQP7kiw5Fk"),
                        (15, "Modern Portfolio Theory", "Markowitz Efficient Frontier, Systematic vs Unsystematic Risk", 35, "L_LUpnjgPso"),
                        (16, "Portfolio Risk Metrics", "Measuring Beta, Sharpe Ratio, Treynor Ratio & Maximum Drawdown", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Mercantile Law & The Indian Contract Act in Business",
                "mercantile-law-indian-contract-act",
                "commerce-finance",
                "Beginner",
                "Adv. Suresh Balakrishnan",
                "Corporate Commercial Attorney & Legal Studies Faculty",
                "13 hours",
                "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=800&q=80",
                "Master valid contracts, offer/acceptance, consideration, breach of contract, indemnity, bailment, and the Sale of Goods Act.",
                "Target Degree: BCom. Commercial and business law. Learn essential elements of a valid contract under the Indian Contract Act 1872, capacity of parties, free consent, remedies for breach of contract, contracts of indemnity and guarantee, and the Sale of Goods Act.",
                "Identify the legal requisites of a valid contract under the Indian Contract Act 1872\nDistinguish between agreements and contracts, void vs voidable agreements\nAnalyze elements vitiating free consent: Coercion, Undue Influence, Fraud, and Misrepresentation\nEvaluate legal remedies available for breach of contract (Damages, Injunction, Specific Performance)\nExamine contract rules under the Sale of Goods Act 1930 and conditions vs warranties",
                "No prior legal education required. Interest in commercial transactions",
                [
                    ("Module 1: Essentials of a Valid Contract", [
                        (1, "Nature of Contract", "Agreement vs Contract: The Contract Formula & Legal Enforceability", 20, "sPh6S4wIqC4"),
                        (2, "Offer and Acceptance", "Legal Rules of a Valid Offer, Invitation to Offer & Communication Rules", 25, "k8lSgL32_5U"),
                        (3, "Doctrine of Consideration", "Quid Pro Quo, Legal Rules of Consideration & Exceptions to Consideration", 25, "Z52G4y1o6Jc"),
                        (4, "Capacity to Contract", "Minors' Agreements, Persons of Unsound Mind & Disqualified Persons", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Free Consent & Legality of Object", [
                        (5, "Coercion & Undue Influence", "Elements of Coercion (Sec 15) vs Undue Influence (Sec 16)", 25, "97H0a3Xl-1M"),
                        (6, "Fraud & Misrepresentation", "Intentional Deceit (Sec 17) vs Innocent Misrepresentation (Sec 18)", 25, "1P8j3J9gE0I"),
                        (7, "Mistake in Contracts", "Mistake of Law vs Mistake of Fact: Bilateral vs Unilateral Mistakes", 25, "m2XyE_K0918"),
                        (8, "Void Agreements", "Agreements in Restraint of Trade, Marriage & Legal Proceedings", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Discharge & Remedies for Breach", [
                        (9, "Performance of Contracts", "Offer to Perform (Tender), Joint Promisors & Time as Essence", 25, "zS8Y7T36J80"),
                        (10, "Discharge of Contracts", "Discharge by Performance, Mutual Agreement, Breach & Impossibility", 30, "6p873K6G5sQ"),
                        (11, "Anticipatory Breach", "Actual vs Anticipatory Breach of Contract (Section 39)", 25, "vX9vFh33p54"),
                        (12, "Remedies for Breach", "Damages (Ordinary, Special, Punitive), Injunction & Specific Performance", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Special Contracts & Sale of Goods", [
                        (13, "Indemnity & Guarantee", "Contract of Indemnity vs Contract of Guarantee: Rights of Surety", 25, "9bZkp7q19f0"),
                        (14, "Bailment and Pledge", "Duties of Bailor and Bailee, Rights of Pawnee in Commercial Pledges", 25, "kJQP7kiw5Fk"),
                        (15, "Sale of Goods Act", "Contract of Sale vs Agreement to Sell & Conditions vs Warranties", 30, "L_LUpnjgPso"),
                        (16, "Unpaid Seller Rights", "Rights of Unpaid Seller: Right of Lien, Stoppage in Transit & Resale", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "E-Commerce Operations, FinTech Architecture & Digital Payments",
                "ecommerce-fintech-digital-payments",
                "commerce-finance",
                "Beginner",
                "Tanmay Bakshi",
                "FinTech Product Strategist & Digital Payments Architect",
                "13 hours",
                "https://images.unsplash.com/photo-1556742049-0a67c5574f73?auto=format&fit=crop&w=800&q=80",
                "Master e-commerce business models, payment gateways, merchant settlement, UPI switches, fraud detection, and FinTech regulations.",
                "Target Degree: BCom. Digital commerce, financial technology, and payment ecosystems. Learn marketplace vs D2C models, payment aggregators (Stripe, Razorpay), interchange fees, UPI rails, fraud prevention, and RBI FinTech regulations.",
                "Analyze B2B, B2C, and D2C e-commerce business models and revenue engines\nUnderstand the end-to-end payment gateway transaction flow and settlement cycles\nExplain interchange fees, merchant discount rate (MDR), and card network schemes\nExamine the architecture of UPI, BBPS, and tokenized digital card payments\nImplement fraud detection heuristics, chargeback mitigation, and PCI-DSS compliance",
                "No technical programming required. Familiarity with online shopping and digital payments",
                [
                    ("Module 1: E-Commerce Business Models", [
                        (1, "E-Commerce Architectures", "B2B, B2C, D2C & Marketplace Platform Business Models", 20, "sPh6S4wIqC4"),
                        (2, "Inventory vs Marketplace", "Inventory-Led vs Managed Marketplace Fulfillment Logistics", 25, "k8lSgL32_5U"),
                        (3, "Omnichannel Commerce", "Click-and-Collect, Dropshipping & Headless Commerce Basics", 25, "Z52G4y1o6Jc"),
                        (4, "E-Commerce Unit Economics", "Customer Acquisition Cost, Average Order Value (AOV) & Return Rates", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Payment Gateways & Card Networks", [
                        (5, "Payment Gateway Flow", "Customer to Merchant Journey: Gateway, Aggregator & Acquiring Bank", 25, "97H0a3Xl-1M"),
                        (6, "Interchange & MDR", "Merchant Discount Rate (MDR), Interchange Fees & Card Schemes (Visa/Mastercard)", 30, "1P8j3J9gE0I"),
                        (7, "Settlement Cycles", "T+1 and T+2 Settlement Mechanics & Escrow Account Regulations", 25, "m2XyE_K0918"),
                        (8, "Chargebacks & Disputes", "Chargeback Lifecycle, Representment Documents & Friendly Fraud", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Real-Time Payments & Mobile Wallets", [
                        (9, "The UPI Revolution", "NPCI Framework, Virtual Payment Address (VPA) & UPI 2.0 Features", 30, "zS8Y7T36J80"),
                        (10, "Digital Wallets & PPIs", "Prepaid Payment Instruments (PPIs): Closed, Semi-Closed & Open Wallets", 25, "6p873K6G5sQ"),
                        (11, "Card Tokenization", "RBI Tokenization Mandate: Securing Card-on-File Transactions", 25, "vX9vFh33p54"),
                        (12, "Cross-Border Payments", "SWIFT Network, Currency Conversion Spreads & Cross-Border Aggregators", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Security, Compliance & The Future of FinTech", [
                        (13, "PCI-DSS Standards", "Payment Card Industry Data Security Standard (PCI-DSS) Levels", 25, "9bZkp7q19f0"),
                        (14, "Fraud Detection AI", "Real-Time Transaction Risk Scoring & Anomaly Detection", 25, "kJQP7kiw5Fk"),
                        (15, "Embedded Finance & BNPL", "Buy Now Pay Later (BNPL) Economics & Embedded Banking (BaaS)", 25, "L_LUpnjgPso"),
                        (16, "Central Bank Digital Currency", "CBDC (Digital Rupee), Account Aggregator Framework & Open Banking", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
        ]

        # Add BCom courses to pool
        for item in bcom:
            courses.append(self._format_course(item))

        # ---------------------------------------------------------------------
        # DEGREE 5: BSc (Pure & Applied Sciences) (7 Courses)
        # ---------------------------------------------------------------------
        bsc = [
            (
                "Computational Biology, Genomics & Bioinformatics Algorithms",
                "computational-biology-genomics",
                "applied-sciences",
                "Intermediate",
                "Dr. Aarti Venkatraman",
                "Genomic Data Scientist & Computational Biology Faculty",
                "15 hours",
                "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?auto=format&fit=crop&w=800&q=80",
                "Master biological sequence databases, BLAST, global/local alignment, phylogenetics, protein folding, and genomics in Python.",
                "Target Degree: BSc. Intersection of computer science and molecular biology. Learn biological data formats (FASTA, GenBank), pairwise sequence alignment algorithms (Needleman-Wunsch, Smith-Waterman), heuristic search with BLAST, and phylogenetic trees.",
                "Query biological databases: NCBI, GenBank, UniProt, and PDB\nImplement dynamic programming sequence alignment: Needleman-Wunsch and Smith-Waterman\nExecute heuristic sequence search and statistical significance testing with BLAST\nConstruct phylogenetic trees using Neighbor-Joining and Maximum Parsimony\nAnalyze 3D protein structures using PyMOL and AlphaFold structural databases",
                "Basic understanding of molecular biology (DNA, RNA, proteins) and Python basics",
                [
                    ("Module 1: Biological Databases & Formats", [
                        (1, "Molecular Dogma", "The Central Dogma of Molecular Biology: Replication to Translation", 20, "sPh6S4wIqC4"),
                        (2, "Genomic Databases", "Navigating NCBI, Ensembl, UniProt & The Protein Data Bank (PDB)", 25, "k8lSgL32_5U"),
                        (3, "File Formats", "Biological Data Formats: FASTA, FASTQ, GenBank & PDB Coordinate Files", 25, "Z52G4y1o6Jc"),
                        (4, "Biopython Basics", "Parsing Sequence Records with Biopython SeqIO Module", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Sequence Alignment Algorithms", [
                        (5, "Dot Matrix Analysis", "Visualizing Sequence Matches & Repeats with Dot Plots", 25, "97H0a3Xl-1M"),
                        (6, "Needleman-Wunsch", "Global Sequence Alignment Dynamic Programming Algorithm", 35, "1P8j3J9gE0I"),
                        (7, "Smith-Waterman", "Local Sequence Alignment Dynamic Programming Algorithm", 35, "m2XyE_K0918"),
                        (8, "Substitution Matrices", "Scoring Matrices: PAM vs BLOSUM62 Mathematical Derivations", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Database Searching & Phylogenetics", [
                        (9, "BLAST Algorithm", "BLAST Heuristic Search Mechanics: Words, Hits & Extension", 30, "zS8Y7T36J80"),
                        (10, "E-Value Statistics", "Interpreting BLAST E-values, Bit Scores & False Discovery Rates", 25, "6p873K6G5sQ"),
                        (11, "Multiple Alignment", "Multiple Sequence Alignment (MSA) with Clustal Omega & Muscle", 30, "vX9vFh33p54"),
                        (12, "Phylogenetic Trees", "Constructing Trees: UPGMA, Neighbor-Joining & Bootstrap Confidence", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Structural Bioinformatics & Genomics", [
                        (13, "Protein Structure", "Primary, Secondary, Tertiary & Quaternary Protein Conformations", 25, "9bZkp7q19f0"),
                        (14, "Homology Modeling", "Template-Based Protein Structure Prediction Workflows", 30, "kJQP7kiw5Fk"),
                        (15, "AlphaFold & Modern AI", "Deep Learning in Structural Biology: The AlphaFold Revolution", 30, "L_LUpnjgPso"),
                        (16, "Next-Gen Sequencing", "NGS Read Mapping, Variant Calling (SNP Detection) & VCF Files", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Data Analytics in Chemical Sciences & Chemometrics",
                "data-analytics-chemical-sciences",
                "applied-sciences",
                "Intermediate",
                "Dr. Sanjeev Mukhopadhyay",
                "Analytical Chemist & Chemometrics Research Scientist",
                "14 hours",
                "https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=800&q=80",
                "Master spectral preprocessing (FTIR/NMR), calibration curves, Principal Component Analysis, PLS regression, and chemical QSAR.",
                "Target Degree: BSc. Data science and quantitative modeling for chemistry students. Learn analytical signal processing, spectroscopic baseline correction, Principal Component Analysis (PCA) for chemical clustering, and Partial Least Squares (PLS) calibration.",
                "Preprocess spectroscopic datasets using Savitzky-Golay filtering and baseline correction\nEvaluate analytical calibration curves, Limit of Detection (LOD), and Limit of Quantitation (LOQ)\nExecute Principal Component Analysis (PCA) on multi-wavelength chemical spectra\nBuild predictive Partial Least Squares (PLS) regression models for compound concentration\nFormulate Quantitative Structure-Activity Relationships (QSAR) for molecular properties",
                "Introductory chemistry and familiarity with basic Python or statistical tools",
                [
                    ("Module 1: Analytical Measurement & Data Preprocessing", [
                        (1, "Chemometrics Scope", "Introduction to Chemometrics: High-Dimensional Analytical Data", 20, "sPh6S4wIqC4"),
                        (2, "Measurement Uncertainty", "Systematic vs Random Errors, Propagation of Uncertainty & Calibration", 25, "k8lSgL32_5U"),
                        (3, "Spectral Preprocessing", "Baseline Drift Correction, Standard Normal Variate (SNV) & Multiplicative Scatter Correction", 30, "Z52G4y1o6Jc"),
                        (4, "Derivative Spectroscopy", "Savitzky-Golay Smoothing & Derivative Spectral Peak Resolution", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Classical & Multivariate Calibration", [
                        (5, "Univariate Calibration", "Beer-Lambert Law, Ordinary Least Squares & Residual Analysis", 25, "97H0a3Xl-1M"),
                        (6, "LOD and LOQ", "Statistical Calculation of Limit of Detection (LOD) & Quantitation (LOQ)", 25, "1P8j3J9gE0I"),
                        (7, "Matrix Interferences", "Spectral Overlap, Matrix Effects & Standard Addition Method", 25, "m2XyE_K0918"),
                        (8, "Multiple Linear Regression", "MLR in Analytical Chemistry & Collinearity Challenges", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Principal Component Analysis (PCA)", [
                        (9, "PCA Mathematical Theory", "Eigenvalues, Eigenvectors, Variance Maximization & Score/Loading Plots", 35, "zS8Y7T36J80"),
                        (10, "Spectral Classification", "Clustering Chemical Formulations with PCA Score Plots", 30, "6p873K6G5sQ"),
                        (11, "Identifying Outliers", "Hotelling's T-Squared & Q-Residuals for Sample Outlier Detection", 25, "vX9vFh33p54"),
                        (12, "Interpretation of Loadings", "Connecting Spectral Loadings to Molecular Vibrational Bonds", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Partial Least Squares (PLS) & QSAR", [
                        (13, "PLS Regression", "Partial Least Squares (PLS1 & PLS2) Algorithm & Latent Variables", 35, "9bZkp7q19f0"),
                        (14, "Cross-Validation", "K-Fold Cross-Validation, RMSECV & Selecting Optimal Latent Variables", 30, "kJQP7kiw5Fk"),
                        (15, "QSAR Modeling", "Quantitative Structure-Activity Relationships (QSAR): Descriptors & Activity", 30, "L_LUpnjgPso"),
                        (16, "Industrial Applications", "Pharmaceutical Process Analytical Technology (PAT) & Online Monitoring", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Environmental Science, Ecology & GIS Geospatial Mapping",
                "environmental-science-gis-mapping",
                "applied-sciences",
                "Beginner",
                "Prof. Deepa Nair",
                "Environmental Scientist & Spatial Cartography Educator",
                "13 hours",
                "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=800&q=80",
                "Master biogeochemical cycles, ecological biodiversity indices, satellite remote sensing, QGIS thematic mapping, and EIA.",
                "Target Degree: BSc. Environmental ecology and geospatial information systems. Learn ecosystem dynamics, pollution vectors, satellite imagery interpretation (NDVI), coordinate reference systems (CRS), vector and raster spatial analysis in QGIS, and Environmental Impact Assessment (EIA).",
                "Analyze ecosystem energy flows, food webs, and biogeochemical cycles\nCalculate ecological biodiversity metrics: Shannon-Wiener and Simpson's Diversity Indices\nUnderstand satellite remote sensing bands and compute Normalized Difference Vegetation Index (NDVI)\nCreate publication-quality thematic maps using open-source QGIS software\nConduct structured Environmental Impact Assessments (EIA) for infrastructure projects",
                "General interest in ecology and natural resources. No prior GIS knowledge needed",
                [
                    ("Module 1: Ecosystem Dynamics & Ecological Principles", [
                        (1, "Ecosystem Structures", "Abiotic and Biotic Components, Energy Trophics & Ecological Pyramids", 25, "sPh6S4wIqC4"),
                        (2, "Biogeochemical Cycles", "Carbon, Nitrogen, Phosphorus & Water Cycles in Global Systems", 25, "k8lSgL32_5U"),
                        (3, "Population Ecology", "Exponential vs Logistic Growth Models & Carrying Capacity (K)", 25, "Z52G4y1o6Jc"),
                        (4, "Measuring Biodiversity", "Alpha, Beta, Gamma Diversity & Shannon-Wiener Index Math", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Environmental Pollution & Climate Science", [
                        (5, "Air Pollution Dynamics", "Particulate Matter (PM2.5/PM10), Photochemical Smog & AQI", 25, "97H0a3Xl-1M"),
                        (6, "Water Quality Parameters", "BOD, COD, Dissolved Oxygen, Eutrophication & Heavy Metals", 30, "1P8j3J9gE0I"),
                        (7, "Climate Change Science", "Greenhouse Gas Radiative Forcing, Carbon Budgets & IPCC Models", 30, "m2XyE_K0918"),
                        (8, "Waste & Circular Economy", "Solid Waste Management, Hazardous Disposal & Extended Producer Responsibility", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Remote Sensing & GIS Fundamentals", [
                        (9, "Geospatial Data Models", "Vector (Points, Lines, Polygons) vs Raster Spatial Data", 25, "zS8Y7T36J80"),
                        (10, "Coordinate Systems", "Geographic (WGS84) vs Projected (UTM) Coordinate Reference Systems", 30, "6p873K6G5sQ"),
                        (11, "Satellite Remote Sensing", "Electromagnetic Spectrum, Landsat/Sentinel Bands & Sensor Resolution", 30, "vX9vFh33p54"),
                        (12, "Vegetation Indices", "Calculating Normalized Difference Vegetation Index (NDVI) in QGIS", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Spatial Analysis & Environmental Governance", [
                        (13, "Vector Spatial Analysis", "Buffering, Clipping, Intersecting & Spatial Joins in QGIS", 30, "9bZkp7q19f0"),
                        (14, "Raster Terrain Analysis", "Digital Elevation Models (DEM), Slope, Aspect & Watershed Delineation", 30, "kJQP7kiw5Fk"),
                        (15, "Thematic Cartography", "Choropleth Maps, Legend Design, Map Scales & Professional Export", 25, "L_LUpnjgPso"),
                        (16, "EIA Framework", "Environmental Impact Assessment: Screening, Scoping, Public Hearing & EMP", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Applied Probability, Statistical Inference & Hypothesis Testing",
                "applied-probability-statistical-inference",
                "applied-sciences",
                "Intermediate",
                "Dr. Alok Nath Sen",
                "Professor of Statistics & Applied Mathematical Probability",
                "15 hours",
                "https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=800&q=80",
                "Master probability distributions, Central Limit Theorem, confidence intervals, p-values, t-tests, ANOVA, and Chi-Square.",
                "Target Degree: BSc. Rigorous probability theory and statistical inference. Learn sample spaces, conditional probability, Bayes' Theorem, discrete and continuous random variables, point estimation (MLE), confidence intervals, and hypothesis testing.",
                "Calculate conditional probability and apply Bayes' Theorem to real-world scenarios\nModel empirical phenomena using Binomial, Poisson, Normal, and Exponential distributions\nUnderstand the Central Limit Theorem and its foundational role in inferential statistics\nConstruct confidence intervals and execute one-sample, two-sample, and paired t-tests\nPerform Analysis of Variance (ANOVA) and Chi-Square goodness-of-fit tests",
                "High school calculus and basic algebra",
                [
                    ("Module 1: Probability Foundations & Random Variables", [
                        (1, "Probability Axioms", "Sample Spaces, Events, Kolmogorov Axioms & Addition Rules", 25, "sPh6S4wIqC4"),
                        (2, "Conditional Probability", "Multiplication Rule, Independent Events & Total Probability Theorem", 25, "k8lSgL32_5U"),
                        (3, "Bayes' Theorem", "Formulation of Bayes' Rule: Prior, Likelihood & Posterior Odds", 30, "Z52G4y1o6Jc"),
                        (4, "Random Variables", "Discrete vs Continuous Random Variables, PMF, PDF & CDF Functions", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Standard Probability Distributions", [
                        (5, "Discrete Distributions", "Binomial Distribution & Poisson Distribution for Rare Events", 30, "97H0a3Xl-1M"),
                        (6, "Uniform & Exponential", "Continuous Uniform Distribution & Memoryless Exponential Distribution", 25, "1P8j3J9gE0I"),
                        (7, "Normal Distribution", "The Gaussian (Normal) Distribution, Z-Scores & Empirical 68-95-99.7 Rule", 30, "m2XyE_K0918"),
                        (8, "Sampling Distributions", "Central Limit Theorem, Standard Error & Student's t-Distribution", 35, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Estimation & Confidence Intervals", [
                        (9, "Point Estimation", "Unbiased Estimators, Efficiency, Consistency & Mean Squared Error", 25, "zS8Y7T36J80"),
                        (10, "Maximum Likelihood", "Maximum Likelihood Estimation (MLE) Principle & Derivations", 35, "6p873K6G5sQ"),
                        (11, "Confidence Intervals for Means", "Confidence Intervals for Population Means (Z-Interval vs t-Interval)", 30, "vX9vFh33p54"),
                        (12, "Confidence Intervals for Proportions", "Large-Sample Confidence Intervals for Population Proportions", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Hypothesis Testing & Statistical Decisions", [
                        (13, "Hypothesis Testing Logic", "Null vs Alternative Hypotheses, Type I & Type II Errors, Significance Alpha", 30, "9bZkp7q19f0"),
                        (14, "Z-Tests & t-Tests", "One-Sample, Two-Sample Independent & Paired t-Tests with P-Values", 35, "kJQP7kiw5Fk"),
                        (15, "ANOVA Testing", "One-Way Analysis of Variance (ANOVA): F-Statistic & Sum of Squares", 35, "L_LUpnjgPso"),
                        (16, "Chi-Square Tests", "Chi-Square Test of Independence & Goodness-of-Fit Testing", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Quantum Mechanics, Wave Equations & Physics Simulation",
                "quantum-mechanics-physics-simulation",
                "applied-sciences",
                "Advanced",
                "Prof. Debashis Roy",
                "Theoretical Physicist & Quantum Computing Researcher",
                "16 hours",
                "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?auto=format&fit=crop&w=800&q=80",
                "Master wave-particle duality, Schrödinger's equation, particle in a box, quantum harmonic oscillator, and Python wave simulation.",
                "Target Degree: BSc. Quantum physics and mathematical simulation. Learn experimental foundations (Photoelectric effect, Compton scattering), wave packets, Heisenberg uncertainty, the time-dependent and time-independent Schrödinger equations, potential wells, and tunneling simulations.",
                "Analyze historical quantum experiments: Blackbody radiation and Compton scattering\nSolve the Time-Independent Schrödinger Equation for 1D Infinite and Finite Potential Wells\nCalculate expectation values of momentum, position, and energy operators\nDerive transmission coefficients for quantum barrier tunneling\nSimulate Gaussian wavepacket evolution and tunneling numerically in Python",
                "Calculus, differential equations, and introductory mechanics",
                [
                    ("Module 1: Breakdown of Classical Physics", [
                        (1, "Blackbody Radiation", "Ultraviolet Catastrophe & Planck's Quantum Hypothesis", 25, "sPh6S4wIqC4"),
                        (2, "Photoelectric Effect", "Einstein's Photon Theory & Work Function Calculations", 25, "k8lSgL32_5U"),
                        (3, "Compton Scattering", "Compton Shift Formula & Relativistic Photon-Electron Collisions", 30, "Z52G4y1o6Jc"),
                        (4, "De Broglie Hypothesis", "Matter Waves, Davisson-Germer Experiment & Wavepackets", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: The Schrödinger Wave Equation", [
                        (5, "Wavefunction Postulates", "Born's Probabilistic Interpretation, Normalization & Wavefunction Continuity", 30, "97H0a3Xl-1M"),
                        (6, "Schrödinger Equation", "Time-Dependent vs Time-Independent Schrödinger Equations", 35, "1P8j3J9gE0I"),
                        (7, "Operators & Commutators", "Hermitian Operators, Observables & Commutation Relations", 30, "m2XyE_K0918"),
                        (8, "Uncertainty Principle", "Heisenberg's Generalized Uncertainty Principle Mathematical Proof", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: One-Dimensional Quantum Bound Systems", [
                        (9, "Infinite Potential Well", "Particle in a Box: Energy Quantization & Stationary States", 35, "zS8Y7T36J80"),
                        (10, "Finite Potential Well", "Finite Square Well: Bound States, Evanescent Waves & Transcendentals", 35, "6p873K6G5sQ"),
                        (11, "Harmonic Oscillator", "Quantum Harmonic Oscillator: Ladder Operator (Creation/Annihilation) Method", 35, "vX9vFh33p54"),
                        (12, "Quantum Tunneling", "Potential Step, Barrier Penetration & Alpha Decay Tunneling Probability", 35, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: 3D Systems & Numerical Simulation", [
                        (13, "Hydrogen Atom", "Central Potential, Spherical Harmonics & Quantum Numbers (n, l, m)", 35, "9bZkp7q19f0"),
                        (14, "Electron Spin", "Stern-Gerlach Experiment & Pauli Spin Matrices", 30, "kJQP7kiw5Fk"),
                        (15, "Numerical Simulation", "Simulating Wavepacket Time Evolution in Python with Split-Step Fourier", 35, "L_LUpnjgPso"),
                        (16, "Quantum Information", "Qubits, Quantum Superposition & Entanglement Foundations", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Cell Biology, Molecular Genetics & Recombinant DNA",
                "cell-biology-molecular-genetics",
                "applied-sciences",
                "Beginner",
                "Dr. Pratima Sen",
                "Molecular Biologist & Genetic Engineering Lab Director",
                "14 hours",
                "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?auto=format&fit=crop&w=800&q=80",
                "Master cell organelle ultrastructure, DNA replication, transcription, translation, operon regulation, PCR, and CRISPR-Cas9.",
                "Target Degree: BSc. Foundational cellular biology and recombinant biotechnology. Learn eukaryotic organelle mechanics, DNA replication fidelity, transcription, RNA processing, the genetic code, lac/trp operons, recombinant plasmids, PCR, and CRISPR gene editing.",
                "Examine the ultrastructure and functions of cell membranes and organelles\nDescribe eukaryotic and prokaryotic DNA replication and proofreading mechanisms\nDetail the transcription lifecycle, pre-mRNA splicing, and ribosomal translation\nAnalyze gene expression regulation via prokaryotic operons (lac and trp operon)\nDesign cloning strategies utilizing restriction endonucleases, plasmids, PCR, and CRISPR",
                "High school biology fundamentals",
                [
                    ("Module 1: Cell Architecture & Membrane Transport", [
                        (1, "Cell Organization", "Prokaryotic vs Eukaryotic Cells: Structural Differentiation", 25, "sPh6S4wIqC4"),
                        (2, "The Plasma Membrane", "Fluid Mosaic Model, Lipid Bilayer & Membrane Proteins", 25, "k8lSgL32_5U"),
                        (3, "Transport Mechanisms", "Passive Diffusion, Facilitated Transport, Active Pumps & Endocytosis", 25, "Z52G4y1o6Jc"),
                        (4, "Organelle Function", "Mitochondria, Endoplasmic Reticulum, Golgi Apparatus & Lysosomes", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: DNA Replication & Molecular Genetics", [
                        (5, "DNA Structure", "Watson-Crick Double Helix, Major/Minor Grooves & Supercoiling", 25, "97H0a3Xl-1M"),
                        (6, "DNA Replication", "Semi-Conservative Replication: Helicase, Primase, Polymerases & Ligase", 30, "1P8j3J9gE0I"),
                        (7, "DNA Repair", "Mismatch Repair, Nucleotide Excision Repair & Telomere Maintenance", 25, "m2XyE_K0918"),
                        (8, "Chromatin Structure", "Histones, Nucleosomes, Heterochromatin vs Euchromatin", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Transcription, Translation & Gene Regulation", [
                        (9, "Transcription", "RNA Polymerase Initiation, Promoters, Elongation & Termination", 30, "zS8Y7T36J80"),
                        (10, "RNA Processing", "5' Capping, Polyadenylation & Spliceosome Intron Splicing", 30, "6p873K6G5sQ"),
                        (11, "Translation Mechanics", "tRNA Charging, Ribosomal A-P-E Sites & Polypeptide Synthesis", 30, "vX9vFh33p54"),
                        (12, "Operon Regulation", "The Lac Operon: Negative & Positive Regulation with Allolactose & cAMP", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Recombinant DNA & Genetic Engineering", [
                        (13, "Restriction Enzymes", "Type II Restriction Endonucleases, Palindromes & DNA Ligase", 25, "9bZkp7q19f0"),
                        (14, "Plasmids & Cloning", "Cloning Vectors, Multiple Cloning Sites (MCS) & Transformation", 30, "kJQP7kiw5Fk"),
                        (15, "Polymerase Chain Reaction", "PCR Principles: Denaturation, Annealing, Extension & Primers", 30, "L_LUpnjgPso"),
                        (16, "CRISPR-Cas9", "CRISPR-Cas9 Gene Editing: Guide RNA, PAM Sites & Double-Strand Breaks", 30, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Linear Algebra & Multivariable Calculus for Physical Sciences",
                "linear-algebra-calculus-scientists",
                "applied-sciences",
                "Intermediate",
                "Prof. Suniti Kumar Banerji",
                "Chair of Mathematical Sciences & Vector Calculus Specialist",
                "15 hours",
                "https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=800&q=80",
                "Master vector spaces, matrices, eigenvalues/eigenvectors, partial derivatives, double/triple integrals, and Green's/Stokes' theorems.",
                "Target Degree: BSc. Core mathematics for physical and scientific computing. Learn vector spaces, basis, matrix diagonalization, eigenvalues and eigenvectors, multivariable partial differentiation, gradient vectors, double/triple integration, and Stokes' theorem.",
                "Determine linear independence, vector space dimensions, and coordinate bases\nDiagonalize matrices through eigenvalue and eigenvector decomposition\nCalculate partial derivatives, directional derivatives, and gradient vectors\nEvaluate double and triple volume integrals across Cartesian, Cylindrical, and Spherical coordinates\nApply Green's Theorem, Stokes' Theorem, and Divergence Theorem to physical vector fields",
                "High school calculus and coordinate geometry",
                [
                    ("Module 1: Vector Spaces & Linear Transformations", [
                        (1, "Vector Spaces", "Definition of Vector Spaces, Subspaces & Linear Combinations", 25, "sPh6S4wIqC4"),
                        (2, "Independence & Basis", "Linear Independence, Span, Basis & Dimension Theorems", 25, "k8lSgL32_5U"),
                        (3, "Linear Transformations", "Linear Mappings, Kernel, Range, Rank-Nullity Theorem", 30, "Z52G4y1o6Jc"),
                        (4, "Matrix Representations", "Matrix of a Linear Transformation & Change of Basis Formula", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Eigenvalues, Diagonalization & Orthogonality", [
                        (5, "Characteristic Equations", "Determinants, Characteristic Polynomial & Finding Eigenvalues", 30, "97H0a3Xl-1M"),
                        (6, "Eigenspaces", "Eigenvectors, Geometric vs Algebraic Multiplicity", 25, "1P8j3J9gE0I"),
                        (7, "Diagonalization", "Matrix Diagonalization Criteria (A = P D P^-1)", 30, "m2XyE_K0918"),
                        (8, "Orthogonality", "Inner Product Spaces, Gram-Schmidt Orthogonalization & SVD Intro", 35, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Multivariable Differential Calculus", [
                        (9, "Multivariable Functions", "Functions of Several Variables, Level Curves & Limits", 25, "zS8Y7T36J80"),
                        (10, "Partial Derivatives", "Partial Differentiation, Higher-Order Derivatives & Clairaut's Theorem", 25, "6p873K6G5sQ"),
                        (11, "Gradients & Directional", "Directional Derivatives, The Gradient Vector & Tangent Planes", 30, "vX9vFh33p54"),
                        (12, "Optimization", "Extreme Values, Second Derivative Test & Lagrange Multipliers", 35, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Multiple Integrals & Vector Calculus", [
                        (13, "Double Integrals", "Double Integrals over General Regions & Polar Coordinates", 30, "9bZkp7q19f0"),
                        (14, "Triple Integrals", "Triple Integrals in Cylindrical and Spherical Coordinates", 35, "kJQP7kiw5Fk"),
                        (15, "Vector Fields & Curl/Div", "Vector Fields, Line Integrals, Conservative Fields, Divergence & Curl", 35, "L_LUpnjgPso"),
                        (16, "Green's & Stokes' Theorems", "Fundamental Theorems: Green's Theorem, Stokes' Theorem & Divergence Theorem", 35, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
        ]

        # Add BSc courses to pool
        for item in bsc:
            courses.append(self._format_course(item))

        # ---------------------------------------------------------------------
        # DEGREE 6: BA (Arts, Humanities & Social Sciences) (7 Courses)
        # ---------------------------------------------------------------------
        ba = [
            (
                "Digital Journalism, Media Ethics & Investigative Storytelling",
                "digital-journalism-investigative-media",
                "humanities-arts",
                "Beginner",
                "Nandita Sengupta",
                "Investigative Journalist & Senior Editor, Global Media Network",
                "13 hours",
                "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80",
                "Master news gathering, investigative sourcing, verification techniques, podcasting, multimedia features, and digital media ethics.",
                "Target Degree: BA. Contemporary journalism in the digital age. Learn news gathering principles, inverted pyramid writing, data journalism techniques, verifying online misinformation, multimedia podcasting, and media law/ethics.",
                "Structure compelling news stories using the inverted pyramid and narrative feature formats\nExecute rigorous investigative research, Freedom of Information (RTI) filings, and source verification\nDetect and debunk digital misinformation, synthetic media, and deepfakes\nProduce audio podcasts and mobile video journalism features\nNavigate defamation law, copyright fair use, and journalistic ethical standards",
                "Curiosity about news, current affairs, and storytelling. No technical prerequisites",
                [
                    ("Module 1: Foundations of Digital Reporting", [
                        (1, "What is News?", "Elements of News Values: Timeliness, Proximity, Prominence & Impact", 20, "sPh6S4wIqC4"),
                        (2, "The Inverted Pyramid", "Structuring News Reports: The Lead (5 Ws and H) to Background", 25, "k8lSgL32_5U"),
                        (3, "Interviewing Techniques", "Conducting Ethical On-the-Record, Off-the-Record & Background Interviews", 25, "Z52G4y1o6Jc"),
                        (4, "Feature Writing", "Narrative Journalism: Scene Setting, Character Development & Voice", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Investigative Reporting & Fact-Checking", [
                        (5, "Investigative Research", "Public Records, Company Filings & Right to Information (RTI) Requests", 25, "97H0a3Xl-1M"),
                        (6, "Verification Tools", "Open Source Intelligence (OSINT) & Geolocation Verification", 30, "1P8j3J9gE0I"),
                        (7, "Combating Fake News", "Fact-Checking Methodologies, Reverse Image Search & Forensic Tools", 25, "m2XyE_K0918"),
                        (8, "Data Journalism", "Acquiring, Cleaning & Visualizing Datasets for News Stories", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Multimedia & Audio-Visual Storytelling", [
                        (9, "Mobile Journalism (MoJo)", "Smartphone Video Production: Framing, Lighting & Mobile Editing", 25, "zS8Y7T36J80"),
                        (10, "Podcast Production", "Scripting, Recording Audio Features & Interview Editing", 30, "6p873K6G5sQ"),
                        (11, "Social Media Distribution", "Repurposing Long-Form Journalism for Threads, Instagram & X", 25, "vX9vFh33p54"),
                        (12, "Interactive Formats", "Scrollytelling, Data Dashboards & Multimedia News Packages", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Media Law, Ethics & Future Trends", [
                        (13, "Defamation & Contempt", "Civil vs Criminal Defamation & Contempt of Court Statutes", 25, "9bZkp7q19f0"),
                        (14, "Copyright & Fair Dealing", "Intellectual Property, Attribution & Fair Use in Journalism", 25, "kJQP7kiw5Fk"),
                        (15, "Journalistic Ethics", "Conflict of Interest, Privacy Rights, Sensationalism & SPJ Code", 30, "L_LUpnjgPso"),
                        (16, "AI in the Newsroom", "Automated Journalism, Large Language Models & Editorial Governance", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Technical Writing, API Documentation & Content Strategy",
                "technical-writing-api-documentation",
                "humanities-arts",
                "Beginner",
                "Sarah Miller",
                "Lead Technical Writer & Developer Documentation Consultant",
                "13 hours",
                "https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&w=800&q=80",
                "Master user guides, Markdown docs, REST API references (OpenAPI/Swagger), information architecture, and Docs-as-Code.",
                "Target Degree: BA. High-demand career track in technical communication. Learn clarity principles, writing user guides, structured authoring, documenting REST APIs using OpenAPI/Swagger, Git-based Docs-as-Code workflows, and content style guides.",
                "Translate complex software engineering concepts into crystal-clear user documentation\nWrite structured documentation using Markdown, DITA, and technical style guides\nDocument RESTful APIs using the OpenAPI Specification (OAS) and Swagger UI\nExecute Docs-as-Code workflows using Git, GitHub, and Static Site Generators\nDesign intuitive Information Architecture and search navigation for developer portals",
                "Strong command of written English. No programming experience required",
                [
                    ("Module 1: Principles of Technical Communication", [
                        (1, "Technical Writing Foundations", "Audience Analysis, Technical Communication Goals & Minimalism", 20, "sPh6S4wIqC4"),
                        (2, "Clarity & Readability", "Active Voice, Reducing Wordiness, Parallelism & Plain Language", 25, "k8lSgL32_5U"),
                        (3, "Writing Types", "Task-Based Tutorials, How-To Guides, Conceptual Explanations & References", 25, "Z52G4y1o6Jc"),
                        (4, "Style Guides", "Adopting Industry Style Guides: Microsoft Style Guide & Google Dev Style", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Structured Authoring & User Guides", [
                        (5, "Markdown Fundamentals", "CommonMark Syntax: Headers, Tables, Code Blocks & Callouts", 20, "97H0a3Xl-1M"),
                        (6, "Quickstart Guides", "Anatomy of an Effective 5-Minute Developer Quickstart Guide", 25, "1P8j3J9gE0I"),
                        (7, "Troubleshooting Docs", "Structuring Troubleshooting Guides: Symptoms, Causes & Solutions", 25, "m2XyE_K0918"),
                        (8, "Visuals in Tech Writing", "Screenshots, UI Callouts, Architecture Diagrams & Flowcharts", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Documenting REST APIs", [
                        (9, "API Documentation Basics", "What is an API? Endpoints, HTTP Methods, Headers & Status Codes", 25, "zS8Y7T36J80"),
                        (10, "OpenAPI Specification", "Writing OpenAPI 3.0 / Swagger YAML Files for API Endpoints", 35, "6p873K6G5sQ"),
                        (11, "Request & Response Samples", "Documenting JSON Payloads, Query Parameters & Response Models", 30, "vX9vFh33p54"),
                        (12, "Interactive API Portals", "Rendering Live Interactive Documentation with Swagger UI & Redoc", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Docs-as-Code & Information Architecture", [
                        (13, "Docs-as-Code Workflow", "Version Control for Documentation: Git Branches, PRs & Reviews", 30, "9bZkp7q19f0"),
                        (14, "Static Site Generators", "Publishing Docs with Docusaurus, MkDocs & GitHub Pages", 30, "kJQP7kiw5Fk"),
                        (15, "Information Architecture", "Taxonomy, Navigation Hierarchies & Algolia DocSearch Integration", 25, "L_LUpnjgPso"),
                        (16, "Content Maintenance", "Continuous Documentation Reviews, Deprecation Notices & Feedback Loops", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Public Policy Analysis, Policy Formulation & Governance",
                "public-policy-governance-analysis",
                "humanities-arts",
                "Intermediate",
                "Dr. Vikram Roy Choudhury",
                "Public Policy Fellow & Senior Governance Consultant",
                "14 hours",
                "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=800&q=80",
                "Master the policy cycle, problem framing, cost-benefit analysis, stakeholder mapping, institutional design, and program evaluation.",
                "Target Degree: BA. Public administration and policy science. Learn the policy cycle stages, problem definition, stakeholder power mapping, quantitative Cost-Benefit Analysis (CBA), regulatory policy design, and monitoring/evaluation (M&E).",
                "Deconstruct the public policy cycle: Agenda setting, formulation, and adoption\nMap diverse stakeholder interests using power-interest matrices\nApply quantitative Cost-Benefit Analysis (CBA) and Cost-Effectiveness Analysis (CEA)\nAnalyze institutional governance mechanisms, separation of powers, and decentralization\nDesign Monitoring and Evaluation (M&E) frameworks using the Theory of Change",
                "General awareness of civic institutions and social issues",
                [
                    ("Module 1: The Policy Making Cycle", [
                        (1, "What is Public Policy?", "Definitions, Public Interest Theories & The Policy Cycle Model", 25, "sPh6S4wIqC4"),
                        (2, "Problem Identification", "Problem Definition: Causal Chains, Symptoms vs Systemic Root Causes", 25, "k8lSgL32_5U"),
                        (3, "Agenda Setting", "Kingdon's Multiple Streams Framework: Problems, Policies & Politics", 30, "Z52G4y1o6Jc"),
                        (4, "Policy Instruments", "Toolbox: Regulations, Taxes, Subsidies, Information & Direct Provision", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Policy Analysis & Evaluation Tools", [
                        (5, "Cost-Benefit Analysis", "Cost-Benefit Analysis (CBA): Discounting Future Public Benefits", 35, "97H0a3Xl-1M"),
                        (6, "Cost-Effectiveness", "Cost-Effectiveness Analysis (CEA) & Multicriteria Decision Analysis", 25, "1P8j3J9gE0I"),
                        (7, "Stakeholder Mapping", "Stakeholder Power-Interest Grids & Political Feasibility Assessment", 25, "m2XyE_K0918"),
                        (8, "Behavioral Public Policy", "Applying Behavioral Nudges in Public Program Design", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Governance Institutions & Implementation", [
                        (9, "Institutional Design", "Separation of Powers, Bureaucracy & Federal vs Unitary Systems", 25, "zS8Y7T36J80"),
                        (10, "Policy Implementation", "Top-Down vs Bottom-Up Implementation & Principal-Agent Divergence", 30, "6p873K6G5sQ"),
                        (11, "Regulatory Governance", "Independent Regulatory Authorities, Telecom, Energy & Environmental Agencies", 25, "vX9vFh33p54"),
                        (12, "Decentralization", "Local Governance, Panchayati Raj / Municipal Empowerment & Devolution", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Policy Monitoring, Evaluation & Briefs", [
                        (13, "Theory of Change", "Logical Framework Analysis (LogFrame) & Theory of Change Mapping", 30, "9bZkp7q19f0"),
                        (14, "Impact Evaluation", "Randomized Controlled Trials (RCTs) & Difference-in-Differences", 30, "kJQP7kiw5Fk"),
                        (15, "Writing Policy Briefs", "Anatomy of an Actionable 3-Page Policy Memo for Decision Makers", 25, "L_LUpnjgPso"),
                        (16, "Contemporary Policy Challenges", "Technology Governance, AI Ethics & Climate Transition Policies", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Cognitive Psychology & Behavioral Decision Science",
                "cognitive-psychology-behavioral-decision",
                "humanities-arts",
                "Beginner",
                "Dr. Ananya Mukherjee",
                "Cognitive Neuroscientist & Behavioral Economics Chair",
                "14 hours",
                "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=800&q=80",
                "Master perception, working memory, Dual-Process Theory (System 1/2), cognitive heuristics, Prospect Theory, and nudging.",
                "Target Degree: BA. Modern cognitive science and behavioral economics. Learn attention filters, working memory capacity, heuristics (availability, representativeness, anchoring), Kahneman's Dual-Process theory, loss aversion, and behavioral nudges.",
                "Explain sensory perception, selective attention, and working memory constraints\nDistinguish between System 1 fast heuristics and System 2 deliberative thought\nAnalyze cognitive heuristics: Anchoring, Availability, and Representativeness\nApply Kahneman and Tversky's Prospect Theory and loss aversion to decisions\nDesign ethical choice architecture and nudge interventions in social systems",
                "Interest in human psychology and decision behavior. No prior lab science needed",
                [
                    ("Module 1: Perception, Attention & Memory", [
                        (1, "Cognitive Paradigm", "History of Cognitive Psychology: Behaviorism to Information Processing", 20, "sPh6S4wIqC4"),
                        (2, "Sensory Perception", "Bottom-Up vs Top-Down Processing & Gestalt Perceptual Laws", 25, "k8lSgL32_5U"),
                        (3, "Selective Attention", "Filter Theories of Attention (Broadbent, Treisman) & The Stroop Effect", 25, "Z52G4y1o6Jc"),
                        (4, "Working Memory", "Baddeley's Multicomponent Working Memory Model & Chunking", 30, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Long-Term Memory & Cognitive Biases", [
                        (5, "Memory Systems", "Episodic vs Semantic vs Procedural Memory Systems", 25, "97H0a3Xl-1M"),
                        (6, "Forgetting & Retrieval", "Ebbinghaus Forgetting Curve, Proactive vs Retroactive Interference", 25, "1P8j3J9gE0I"),
                        (7, "False Memories", "Elizabeth Loftus' Misinformation Effect & Eyewitness Fallibility", 25, "m2XyE_K0918"),
                        (8, "Cognitive Biases", "Confirmation Bias, Hindsight Bias & The Dunning-Kruger Effect", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Judgment & Decision Making", [
                        (9, "Dual-Process Theory", "Kahneman's Thinking, Fast and Slow: System 1 vs System 2", 30, "zS8Y7T36J80"),
                        (10, "Heuristics in Action", "Availability Heuristic, Representativeness & Base Rate Fallacy", 30, "6p873K6G5sQ"),
                        (11, "Anchoring & Framing", "Anchoring Effects & Framing Manipulations in Economic Choice", 30, "vX9vFh33p54"),
                        (12, "Prospect Theory", "Prospect Theory: S-Shaped Value Function & Loss Aversion", 35, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Choice Architecture & Behavioral Nudges", [
                        (13, "Nudge Theory", "Thaler and Sunstein's Nudge: Libertarian Paternalism", 25, "9bZkp7q19f0"),
                        (14, "Defaults & Sludge", "Power of Default Options, Opt-In vs Opt-Out & Sludge Reduction", 25, "kJQP7kiw5Fk"),
                        (15, "Social Norms & Feedback", "Descriptive vs Injunctive Norms in Influencing Public Behavior", 25, "L_LUpnjgPso"),
                        (16, "Ethics of Behavioral Science", "Dark Patterns, Manipulation vs Empowerment & Ethical Guidelines", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "International Relations, Diplomacy & Modern Geopolitics",
                "international-relations-geopolitics",
                "humanities-arts",
                "Intermediate",
                "Ambassador R. K. Bhattacharya (Retd.)",
                "Former Diplomat & Professor of International Security",
                "15 hours",
                "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?auto=format&fit=crop&w=800&q=80",
                "Master IR realism, liberalism, constructivism, UN diplomacy, nuclear deterrence, grand strategy, and 21st-century multipolarity.",
                "Target Degree: BA. Political science and international statecraft. Learn classical and structural realism, liberal internationalism, constructivism, international diplomacy, balance of power, nuclear deterrence, and contemporary geopolitical flashpoints.",
                "Compare core international relations paradigms: Realism, Liberalism, and Constructivism\nAnalyze the evolution of modern state sovereignty from the Peace of Westphalia (1648)\nExamine multilateral diplomacy through the United Nations Security Council\nEvaluate nuclear deterrence strategy and Mutually Assured Destruction (MAD)\nAssess 21st-century multipolar geopolitics: US-China competition, Indo-Pacific alliances",
                "Interest in global politics, modern history, and diplomatic affairs",
                [
                    ("Module 1: Theories of International Relations", [
                        (1, "Origins of IR", "The Westphalian State System & Concepts of Anarchy", 25, "sPh6S4wIqC4"),
                        (2, "Realism Paradigms", "Classical Realism (Morgenthau) vs Structural Realism (Waltz)", 30, "k8lSgL32_5U"),
                        (3, "Liberal Internationalism", "Democratic Peace Theory, Interdependence & Institutionalism", 30, "Z52G4y1o6Jc"),
                        (4, "Constructivism & Critical", "Social Constructivism (Wendt), Identity Politics & Post-Colonialism", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Power, Security & Deterrence", [
                        (5, "Balance of Power", "Balance of Power, Hegemonic Stability & Thucydides Trap", 30, "97H0a3Xl-1M"),
                        (6, "Nuclear Deterrence", "Mutually Assured Destruction (MAD), First-Strike & Proliferation Treaties (NPT)", 35, "1P8j3J9gE0I"),
                        (7, "Hard vs Soft Power", "Joseph Nye's Soft Power, Smart Power & Economic Sanctions", 25, "m2XyE_K0918"),
                        (8, "Hybrid & Cyber Warfare", "Grey-Zone Conflict, Information Warfare & Critical Cyber Attacks", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: International Organizations & Diplomacy", [
                        (9, "United Nations System", "UN Security Council Veto Power, General Assembly & Peacekeeping", 30, "zS8Y7T36J80"),
                        (10, "Bilateral Diplomacy", "Diplomatic Protocols, Vienna Convention & Track I vs Track II", 25, "6p873K6G5sQ"),
                        (11, "International Law", "Customary International Law, Treaties & The International Court of Justice", 30, "vX9vFh33p54"),
                        (12, "Regional Blocs", "European Union, ASEAN, BRICS & Regional Geopolitical Integration", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Contemporary Geopolitical Architecture", [
                        (13, "US-China Rivalry", "The New Cold War: Technology Decoupling & Taiwan Geopolitics", 30, "9bZkp7q19f0"),
                        (14, "The Indo-Pacific", "The Quad Alliance, Maritime Security & The South China Sea", 30, "kJQP7kiw5Fk"),
                        (15, "Global South Dynamics", "Strategic Autonomy, Non-Alignment 2.0 & Energy Transitions", 25, "L_LUpnjgPso"),
                        (16, "Future of Global Order", "Multipolarity, De-Dollarization & The Reshaping of Global Norms", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "English Literary Criticism & Modern Narrative Theory",
                "english-literary-criticism-narrative",
                "humanities-arts",
                "Beginner",
                "Prof. Claire Beauchamp",
                "Chair of Comparative Literature & Narrative Theory Scholar",
                "13 hours",
                "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?auto=format&fit=crop&w=800&q=80",
                "Master structuralism, post-structuralism, postcolonial theory, feminist criticism, narrative focalization, and literary analysis.",
                "Target Degree: BA. Rigorous English literature and critical theory. Learn classical poetics, New Criticism, structuralism, deconstruction, postcolonial critique (Said, Spivak), narrative voice, and focalization techniques.",
                "Trace the evolution of literary criticism from Aristotle's Poetics to New Criticism\nApply structuralist and deconstructionist methodologies to analyze literary texts\nExamine postcolonial critique: Orientalism, Hybridity, and Subaltern voices\nAnalyze narrative architecture: Genette's focalization, story vs plot, and unreliable narrators\nAuthor scholarly, evidence-based critical literary essays with MLA conventions",
                "Appreciation for reading literature and analytical writing",
                [
                    ("Module 1: Classical to Modern Critical Foundations", [
                        (1, "Classical Poetics", "Aristotle's Poetics: Mimesis, Catharsis, Hamartia & Dramatic Unity", 25, "sPh6S4wIqC4"),
                        (2, "Romantic Literary Theory", "Wordsworth's Preface to Lyrical Ballads & Coleridge's Imagination", 25, "k8lSgL32_5U"),
                        (3, "Russian Formalism", "Defamiliarization (Ostranenie), Fabula vs Syuzhet", 25, "Z52G4y1o6Jc"),
                        (4, "New Criticism", "Close Reading, Intentional Fallacy & Affective Fallacy", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Structuralism, Semiotics & Deconstruction", [
                        (5, "Structuralism", "Ferdinand de Saussure: Signifier, Signified & Arbitrariness", 30, "97H0a3Xl-1M"),
                        (6, "Barthes & Death of Author", "Roland Barthes: The Death of the Author & Reader-Response", 25, "1P8j3J9gE0I"),
                        (7, "Deconstruction", "Jacques Derrida: Différance, Binary Oppositions & Textual Instability", 35, "m2XyE_K0918"),
                        (8, "Psychoanalytic Criticism", "Freud and Lacan: The Unconscious, The Gaze & The Symbolic Order", 30, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Cultural, Gender & Postcolonial Theory", [
                        (9, "Marxist Literary Criticism", "Ideology, Base and Superstructure & Althusser's Interpellation", 25, "zS8Y7T36J80"),
                        (10, "Feminist Criticism", "Gilbert & Gubar (Madwoman in the Attic), Gynocriticism & Judith Butler", 30, "6p873K6G5sQ"),
                        (11, "Postcolonial Critique", "Edward Said's Orientalism: Power, Representation & The Other", 35, "vX9vFh33p54"),
                        (12, "Subaltern Studies", "Spivak's 'Can the Subaltern Speak?' & Homi Bhabha's Hybridity", 30, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Narratology & Narrative Architecture", [
                        (13, "Narratology Core", "Gérard Genette: Story Time, Narrative Time, Duration & Frequency", 30, "9bZkp7q19f0"),
                        (14, "Focalization & Voice", "Zero, Internal & External Focalization & Unreliable Narrators", 30, "kJQP7kiw5Fk"),
                        (15, "Postmodern Metafiction", "Self-Reflexivity, Pastiche, Irony & Hyperreality in Contemporary Fiction", 25, "L_LUpnjgPso"),
                        (16, "Scholarly Writing", "Crafting Thesis-Driven Literary Arguments adhering to MLA Standards", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
            (
                "Graphic Design Principles, Typography & Visual Communication",
                "graphic-design-visual-communication",
                "humanities-arts",
                "Beginner",
                "Arman Keshishian",
                "Creative Director & Graphic Design Faculty",
                "13 hours",
                "https://images.unsplash.com/photo-1561070791-2526d30994b5?auto=format&fit=crop&w=800&q=80",
                "Master visual hierarchy, grid systems, typography pairing, psychological color theory, and corporate brand identity design.",
                "Target Degree: BA. Professional visual design and communication. Learn Gestalt principles, compositional balance, grid systems, typography anatomy, psychological color palettes, and developing cohesive multi-channel visual identities.",
                "Apply core visual hierarchy rules: Scale, Contrast, Space, and Alignment\nDesign clean compositional layouts using responsive 12-column and modular grid systems\nPair typefaces harmoniously using typography anatomy, kerning, and leading principles\nCreate cohesive, emotionally resonant color palettes based on color theory and psychology\nDevelop comprehensive corporate brand identity style guides and multi-platform visual assets",
                "No prior design tools experience required. Creative enthusiasm",
                [
                    ("Module 1: Fundamentals of Visual Composition", [
                        (1, "Design Principles", "Balance, Contrast, Emphasis, Movement, Pattern, Rhythm & Unity", 20, "sPh6S4wIqC4"),
                        (2, "Gestalt Principles", "Proximity, Similarity, Continuity, Closure & Figure/Ground", 25, "k8lSgL32_5U"),
                        (3, "Grid Systems", "The Swiss Grid: Manuscript, Column, Modular & Baseline Grids", 25, "Z52G4y1o6Jc"),
                        (4, "Visual Hierarchy", "Directing Eye Flow with Scale, Weight, Color & Negative Space", 25, "jC6wGg8e33o"),
                    ]),
                    ("Module 2: Typography & Letterforms", [
                        (5, "Anatomy of Type", "Serif, Sans-Serif, Baseline, X-Height, Ascenders, Descenders & Counters", 25, "97H0a3Xl-1M"),
                        (6, "Typeface Classification", "Humanist, Transitional, Modern, Slab Serif & Geometric Sans", 25, "1P8j3J9gE0I"),
                        (7, "Typographic Spacing", "Kerning, Tracking, Leading & Line Length for Optimal Readability", 25, "m2XyE_K0918"),
                        (8, "Font Pairing Art", "Combining Typefaces: Contrast vs Conflict Rules in Professional Design", 25, "b023f9v_4jA"),
                    ]),
                    ("Module 3: Color Theory & Psychology", [
                        (9, "Color Wheel Systems", "Additive (RGB) vs Subtractive (CMYK) Color & The Color Wheel", 20, "zS8Y7T36J80"),
                        (10, "Harmonic Palettes", "Monochromatic, Analogous, Complementary & Triadic Color Palettes", 25, "6p873K6G5sQ"),
                        (11, "Color Psychology", "Emotional Associations of Hues & Cultural Contexts in Branding", 25, "vX9vFh33p54"),
                        (12, "Accessible Color", "Color Contrast Compliance (WCAG AA/AAA) & Colorblind-Friendly Design", 25, "nF8g90M5k1w"),
                    ]),
                    ("Module 4: Brand Identity & Multi-Platform Design", [
                        (13, "Logo Design Principles", "Simplicity, Memorability, Versatility & Scalability in Marks", 25, "9bZkp7q19f0"),
                        (14, "Brand Guidelines", "Creating Brand Style Guides: Logo Usage, Clearspace & Don'ts", 25, "kJQP7kiw5Fk"),
                        (15, "Print vs Digital Production", "Resolution (DPI/PPI), Bleeds, Crop Marks, Vector vs Raster Formats", 25, "L_LUpnjgPso"),
                        (16, "Portfolio Presentation", "Curating, Mocking Up & Presenting Professional Graphic Design Case Studies", 25, "fJ9rUzIMcZQ"),
                    ]),
                ]
            ),
        ]

        # Add BA courses to pool
        for item in ba:
            courses.append(self._format_course(item))

        return courses

    def _format_course(self, item):
        title = item[0]
        slug = item[1]
        category_slug = item[2]
        difficulty = item[3]
        instructor_name = item[4]
        instructor_title = item[5]
        duration = item[6]
        thumbnail_url = item[7]
        short_desc = item[8]
        desc = item[9]
        objectives = item[10]
        prerequisites = item[11]
        modules_data = item[12]

        formatted_modules = []
        for m_idx, (m_title, lessons) in enumerate(modules_data, start=1):
            formatted_lessons = []
            for l_info in lessons:
                l_order = l_info[0]
                l_topic = l_info[1]
                l_title = l_info[2]
                l_dur = l_info[3]
                l_vid = l_info[4]

                # Generate comprehensive study notes
                content = (
                    f"<h3>{l_title}</h3>"
                    f"<p class='lead'>{l_topic} — Master core conceptual models, foundational definitions, "
                    f"and applied methodologies relevant to this topic.</p>"
                    f"<h4>Detailed Study Framework</h4>"
                    f"<p>In modern practice, understanding the intersection of rigorous theory and empirical execution "
                    f"is paramount. This lesson breaks down key principles, operational workflows, and analytical techniques.</p>"
                    f"<ul>"
                    f"<li><strong>Conceptual Foundation:</strong> Primary axioms, terminology, and historical context.</li>"
                    f"<li><strong>Analytical Application:</strong> Step-by-step methodologies and problem-solving strategies.</li>"
                    f"<li><strong>Real-World Impact:</strong> Case evidence, performance implications, and industry benchmarks.</li>"
                    f"</ul>"
                    f"<h4>Core Technical & Strategic Takeaways</h4>"
                    f"<p>Always evaluate strategic trade-offs rather than searching for zero-cost silver bullets. Ensure continuous "
                    f"validation against empirical metrics and peer-reviewed standards.</p>"
                )

                takeaways = (
                    f"Master foundational definitions and operational mechanisms of {l_topic}.\n"
                    f"Evaluate performance trade-offs using structured analytical frameworks.\n"
                    f"Apply best practices to eliminate common pitfalls and ensure high-integrity outcomes."
                )

                mistakes = (
                    f"Applying theoretical models without verifying underlying boundary assumptions.\n"
                    f"Confusing superficial output metrics with genuine strategic impact."
                )

                formatted_lessons.append((l_order, l_topic, l_title, l_dur, l_vid, content, takeaways, mistakes))

            formatted_modules.append({
                'order': m_idx,
                'title': m_title,
                'description': f"Comprehensive exploration of {m_title} concepts and applied practices.",
                'lessons': formatted_lessons
            })

        return {
            'title': title,
            'slug': slug,
            'category_slug': category_slug,
            'difficulty': difficulty,
            'instructor_name': instructor_name,
            'instructor_title': instructor_title,
            'estimated_duration': duration,
            'thumbnail_url': thumbnail_url,
            'short_description': short_desc,
            'description': desc,
            'learning_objectives': objectives,
            'prerequisites': prerequisites,
            'modules': formatted_modules
        }
