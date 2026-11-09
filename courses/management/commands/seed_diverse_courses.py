import json
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from courses.models import (
    Category, Course, CourseModule, CourseAssessment, CourseAssessmentQuestion
)
from learning.models import Lesson


class Command(BaseCommand):
    help = 'Seeds diverse courses for Management, Science, AI, and Cloud students with 16 lessons each.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting Diverse Courses Seeding for SkillSphere...'))

        # ---------------------------------------------------------------------
        # 1. Categories
        # ---------------------------------------------------------------------
        categories_data = [
            {
                'name': 'Management & Business Leadership',
                'slug': 'management-business',
                'description': 'Product strategy, corporate finance, business analytics, agile leadership, and executive decision modeling.',
                'icon': 'briefcase'
            },
            {
                'name': 'Scientific Computing & Applied Sciences',
                'slug': 'applied-sciences',
                'description': 'Computational physics, numerical mathematics, bioinformatics, genomic data science, and scientific simulation.',
                'icon': 'activity'
            },
            {
                'name': 'Artificial Intelligence',
                'slug': 'artificial-intelligence',
                'description': 'Machine learning, deep neural networks, generative AI, LLMs, prompt engineering, and computer vision.',
                'icon': 'cpu'
            },
            {
                'name': 'Cloud & DevOps Engineering',
                'slug': 'cloud-devops',
                'description': 'Cloud architecture, AWS infrastructure, Docker containerization, CI/CD automation, and site reliability.',
                'icon': 'cloud'
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
        # 2. Courses Curriculum Specification (7 Courses x 4 Modules x 4 Lessons = 112 Lessons)
        # ---------------------------------------------------------------------
        courses_spec = [
            # -----------------------------------------------------------------
            # COURSE 1: Management - Product Management & Agile Strategy
            # -----------------------------------------------------------------
            {
                'title': 'Product Management & Agile Product Strategy',
                'slug': 'product-management-agile-strategy',
                'category_slug': 'management-business',
                'difficulty': 'Beginner',
                'instructor_name': 'Sarah Jenkins',
                'instructor_title': 'VP of Product & Agile Coach',
                'estimated_duration': '14 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=800&q=80',
                'short_description': 'Master modern product discovery, customer interviews, PRDs, RICE prioritization, Scrum sprints, and GTM launches.',
                'description': 'A comprehensive, end-to-end masterclass for aspiring and practicing product managers. Learn to identify high-value customer problems, conduct user interviews, translate market insights into technical Product Requirement Documents (PRDs), prioritize features using RICE and MoSCoW frameworks, orchestrate cross-functional Agile engineering sprints, track north-star product metrics (CAC, LTV, Retention, Churn), and execute successful Go-To-Market launches.',
                'learning_objectives': "Conduct qualitative customer interviews and synthesize actionable user personas\nDraft structured, engineer-ready Product Requirement Documents (PRDs)\nApply quantitative feature prioritization matrices (RICE, Kano, MoSCoW)\nFacilitate Scrum sprint ceremonies: planning, backlog grooming, and retrospectives\nDefine and measure north-star metrics, cohort retention, and unit economics\nBuild and execute data-driven Go-to-Market (GTM) launch strategies",
                'prerequisites': "No prior programming experience required\nBasic familiarity with digital web or mobile applications\nAnalytical curiosity and enthusiasm for solving user problems",
                'modules': [
                    {
                        'order': 1,
                        'title': 'Module 1: Product Discovery & User Needs',
                        'description': 'Uncover customer pain points, conduct user research, and evaluate market opportunities.',
                        'lessons': [
                            (1, 'The Product Lifecycle', 'Introduction to Modern Product Management', 20, 'sPh6S4wIqC4',
                             '<h3>Introduction to Modern Product Management</h3><p>Understand the intersection of user experience, business viability, and engineering feasibility. Explore the core responsibilities of a product manager versus a project manager.</p><h4>The PM Venn Diagram</h4><p>A Product Manager operates at the crossroads of:</p><ul><li><strong>Business:</strong> Ensuring the product creates economic value and sustainable competitive advantage.</li><li><strong>Technology:</strong> Partnering with engineering to understand constraints and possibilities.</li><li><strong>User Experience:</strong> Advocating relentlessly for the end customer\'s needs.</li></ul>',
                             'Product Managers discover what to build; project managers ensure how and when it gets built.\nBalance commercial viability with technical feasibility and customer value.\nEarly discovery prevents expensive post-launch pivots.',
                             'Treating the PM role as a passive feature coordinator rather than an outcome-driven leader.\nConfusing customer feature requests with underlying customer problems.'),
                            (2, 'Customer Discovery', 'User Persona Development & Customer Interviews', 25, 'k8lSgL32_5U',
                             '<h3>User Persona Development & Customer Interviews</h3><p>Master continuous discovery habits. Formulate non-leading interview questions, synthesize empathy maps, and extract behavioral pain points to craft actionable user personas.</p><h4>The Mom Test Framework</h4><p>Never ask customers if they like your idea. Instead, ask about their past behavior, current workarounds, and how much time or money they currently spend solving the problem.</p>',
                             'Formulate open-ended, non-leading interview questions based on past behaviors.\nDistinguish primary personas from secondary and anti-personas.\nDocument jobs-to-be-done (JTBD) rather than superficial demographic traits.',
                             'Asking speculative hypothetical questions like "Would you buy this feature?".\nBuilding personas based on internal team assumptions without direct user evidence.'),
                            (3, 'Market Opportunity', 'Market Sizing, TAM/SAM/SOM & Competitive Analysis', 25, 'Z52G4y1o6Jc',
                             '<h3>Market Sizing, TAM/SAM/SOM & Competitive Analysis</h3><p>Quantify business opportunities using top-down and bottom-up market sizing models. Map competitive landscapes with 2x2 matrices and Blue Ocean value curves.</p><h4>Market Sizing Hierarchy</h4><ul><li><strong>TAM (Total Addressable Market):</strong> The entire global demand for your product category.</li><li><strong>SAM (Serviceable Addressable Market):</strong> The portion of TAM targeted by your business model.</li><li><strong>SOM (Serviceable Obtainable Market):</strong> The realistic market share you can capture in 1-3 years.</li></ul>',
                             'Bottom-up sizing based on unit economics is far more credible than top-down percentages.\nCompetitive analysis must identify indirect and substitute alternatives, not just direct rivals.\nDefine your defensible moat early.',
                             'Assuming a top-down "1% of China/India" estimation model is sufficient for investors.\nIgnoring non-consumption (the status quo of doing nothing) as your biggest competitor.'),
                            (4, 'Product Strategy', 'Value Proposition Design & Product-Market Fit', 25, 'jC6wGg8e33o',
                             '<h3>Value Proposition Design & Product-Market Fit</h3><p>Connect customer pains and gains directly to product features. Formulate clear hypotheses and test for true product-market fit using Sean Ellis retention criteria.</p>',
                             'Product-Market Fit occurs when retention curves flatten over time.\nValue propositions must articulate a distinct 10x improvement on a critical dimension.\nIterate rapidly before scaling marketing spend.',
                             'Premature scaling before reaching measurable retention and repeat engagement.\nConflating initial acquisition surges with true product-market fit.')
                        ]
                    },
                    {
                        'order': 2,
                        'title': 'Module 2: Defining the Product & PRDs',
                        'description': 'Translate insights into engineer-ready requirements, wireframes, and prioritization frameworks.',
                        'lessons': [
                            (5, 'Requirements Engineering', 'Writing Actionable Product Requirement Docs (PRDs)', 30, '97H0a3Xl-1M',
                             '<h3>Writing Actionable Product Requirement Docs (PRDs)</h3><p>Structure clear, concise PRDs that empower engineering and design teams. Learn the anatomy of problem statements, user flows, acceptance criteria, and technical constraints.</p>',
                             'PRDs define the problem, goals, scope, and success criteria—not the prescriptive implementation.\nInclude explicit non-goals to prevent scope creep.\nAlways write testable acceptance criteria with Given/When/Then formatting.',
                             'Writing bloated 40-page waterfall specs that go unread by engineers.\nSpecifying implementation details that disempower software architects.'),
                            (6, 'Prioritization', 'Feature Prioritization Frameworks: RICE & MoSCoW', 25, '1P8j3J9gE0I',
                             '<h3>Feature Prioritization Frameworks: RICE & MoSCoW</h3><p>Remove cognitive bias from roadmap decisions. Calculate RICE scores (Reach * Impact * Confidence / Effort) and apply MoSCoW matrices to negotiate MVP scope with executives.</p>',
                             'RICE formula: (Reach × Impact × Confidence) ÷ Effort = Prioritization Score.\nUse confidence scoring to penalize unvalidated assumptions and prioritize user research.\nMoSCoW (Must, Should, Could, Won\'t have) aligns executive expectations for sprint boundaries.',
                             'Treating effort as a fixed constant without engineering estimation.\nAllowing the Highest Paid Person\'s Opinion (HiPPO) to override analytical prioritization scores.'),
                            (7, 'Wireframing & Prototyping', 'Rapid Wireframing & MVP Prototyping Workflows', 25, 'm2XyE_K0918',
                             '<h3>Rapid Wireframing & MVP Prototyping Workflows</h3><p>Collaborate effectively with UI/UX designers. Build low-fidelity clickable wireframes in Figma to validate usability and information architecture before writing code.</p>',
                             'Low-fidelity wireframes test information hierarchy without visual styling distractions.\nClickable prototypes expose navigation bottlenecks in minutes rather than weeks.\nSeparate usability testing from customer desirability testing.',
                             'Jumping straight into high-fidelity visual design before validating underlying task flows.\nSpending weeks polishing pixel-perfect designs before validating core user journeys.'),
                            (8, 'MVP Definition', 'Minimum Viable Product (MVP) Strategy & De-risking', 25, 'b023f9v_4jA',
                             '<h3>Minimum Viable Product (MVP) Strategy & De-risking</h3><p>Master the true spirit of the MVP: the smallest experiment that generates validated learning. Explore concierge MVPs, Wizard of Oz prototypes, and smoke-test landing pages.</p>',
                             'An MVP is a learning vehicle, not an excuse for broken or poor-quality software.\nChoose the right experiment type: Wizard of Oz, concierge, or landing page test.\nDefine clear pass/fail success gates prior to running any experiment.',
                             'Building a full automated platform when a manual spreadsheet could test the hypothesis.\nAbandoning an MVP experiment halfway through without recording quantitative learnings.')
                        ]
                    },
                    {
                        'order': 3,
                        'title': 'Module 3: Agile Execution & Sprint Delivery',
                        'description': 'Partner with engineering teams to plan sprints, groom backlogs, and track delivery velocity.',
                        'lessons': [
                            (9, 'Agile Frameworks', 'Scrum vs Kanban: Choosing the Right Agile Delivery Model', 25, 'zS8Y7T36J80',
                             '<h3>Scrum vs Kanban: Choosing the Right Agile Delivery Model</h3><p>Compare timeboxed sprint cycles (Scrum) with continuous flow systems (Kanban). Understand story points, team velocity, WIP limits, and burndown charts.</p>',
                             'Scrum suits predictable feature roadmaps with stable team composition.\nKanban suits interrupt-driven teams such as DevOps, maintenance, or high-uncertainty research.\nStory points measure relative complexity and uncertainty, never exact calendar hours.',
                             'Equating 1 story point to 1 developer hour in sprint planning.\nViolating Work-In-Progress (WIP) limits, causing context switching and delivery thrashing.'),
                            (10, 'Backlog Management', 'User Story Mapping & Backlog Grooming Best Practices', 25, '6p873K6G5sQ',
                             '<h3>User Story Mapping & Backlog Grooming Best Practices</h3><p>Organize user stories along the customer journey timeline. Decompose epic features into INVEST-compliant user stories with unambiguous definitions of done.</p>',
                             'Apply the INVEST criteria: Independent, Negotiable, Valuable, Estimable, Small, Testable.\nStory mapping visualizes horizontal MVP releases across the entire end-to-end user workflow.\nConduct weekly backlog grooming to ensure top stories are ready for sprint planning.',
                             'Writing technical tasks disguised as user stories without specifying user value.\nFailing to involve QA engineers in defining acceptance criteria.'),
                            (11, 'Product Metrics', 'North Star Metrics, OKRs & Unit Economics', 25, 'vX9vFh33p54',
                             '<h3>North Star Metrics, OKRs & Unit Economics</h3><p>Align company goals with product delivery. Define Objectives and Key Results (OKRs), calculate Customer Acquisition Cost (CAC), Lifetime Value (LTV), and establish your North Star Metric.</p>',
                             'The North Star Metric captures the moment user value aligns with business profitability.\nHealthy SaaS unit economics require an LTV to CAC ratio greater than 3:1.\nKey Results must be measurable outcomes (retention rate), not task outputs (launch feature).',
                             'Selecting vanity metrics (total registered users) instead of engagement metrics (weekly active users).\nMeasuring outputs instead of business outcomes.'),
                            (12, 'Cross-Functional Leadership', 'Managing Stakeholders, Engineers & Executive Reviews', 25, 'nF8g90M5k1w',
                             '<h3>Managing Stakeholders, Engineers & Executive Reviews</h3><p>Exercise influence without authority. Manage conflicting priorities between Sales, Legal, Engineering, and Executive leadership while maintaining team trust.</p>',
                             'Lead with data, customer testimonials, and transparent trade-offs.\nPre-wire critical executive meetings by briefing key stakeholders individually beforehand.\nProtect engineering focus by saying "no" to unplanned executive pet projects gracefully.',
                             'Committing to sales deadlines without consulting engineering leads.\nSurprising executive stakeholders with bad news during all-hands presentations.')
                        ]
                    },
                    {
                        'order': 4,
                        'title': 'Module 4: Launch, Growth & Product Mastery',
                        'description': 'Execute go-to-market playbooks, run A/B experiments, and build your capstone portfolio.',
                        'lessons': [
                            (13, 'Launch Playbook', 'Go-to-Market (GTM) Strategy & Phased Rollouts', 25, 'xM6i93Q4eWw',
                             '<h3>Go-to-Market (GTM) Strategy & Phased Rollouts</h3><p>Coordinate seamless product launches. Execute alpha/beta test programs, feature flagging with phased canary releases, and marketing alignment.</p>',
                             'Use feature flags to separate code deployment from business release.\nPhased canary rollouts (5% -> 25% -> 100%) catch production defects before impacting the entire user base.\nCoordinate customer support documentation and training before public announcements.',
                             'Treating launch day as the finish line rather than the starting line of product iteration.\nDeploying major releases on Friday afternoons without monitoring coverage.'),
                            (14, 'Growth & Experimentation', 'A/B Testing, Funnel Analytics & Product-Led Growth', 30, 'w0r3v583b6c',
                             '<h3>A/B Testing, Funnel Analytics & Product-Led Growth</h3><p>Drive organic user expansion with Product-Led Growth (PLG) loops. Formulate testable experimentation hypotheses, calculate statistical significance, and eliminate funnel drop-offs.</p>',
                             'Statistical significance requires adequate sample size and run duration; avoid peeking early.\nPLG loops turn product usage directly into acquisition (e.g., Slack invite loops, Zoom watermarks).\nSegment funnel drop-offs by device, browser, and user cohort to pinpoint friction.',
                             'Calling an A/B test a winner before reaching sufficient statistical power.\nOptimizing local micro-conversions at the expense of long-term customer retention.'),
                            (15, 'Product-Led Growth', 'Virality, Expansion Loops & Retention Modeling', 25, 'e94k0jB77eE',
                             '<h3>Virality, Expansion Loops & Retention Modeling</h3><p>Analyze cohort retention charts to detect user churn early. Engineer viral expansion loops and self-serve upgrade paths that compound over time.</p>',
                             'Retention is the foundation of growth; pouring acquisition into a leaky bucket fails.\nCalculate viral coefficient K: invites sent per user multiplied by invite conversion rate.\nBuild onboarding experiences that deliver the "Aha!" moment in the first session.',
                             'Relying solely on paid ads for growth without an organic expansion engine.\nComplicating user onboarding with unnecessary mandatory sign-up steps.'),
                            (16, 'Capstone Project', 'Capstone: Complete Product Pitch & Executive Roadmap', 35, 'kqtD5dpn9C8',
                             '<h3>Capstone Project: Complete Product Pitch & Executive Roadmap</h3><p>Synthesize everything you have learned. Deliver a comprehensive product portfolio piece featuring a customer discovery brief, PRD, RICE prioritization matrix, clickable prototype spec, and 12-month executive roadmap.</p>',
                             'A world-class product portfolio tells a compelling narrative of customer discovery and validation.\nTie every feature directly to business revenue, retention, or cost reduction.\nPresent your roadmap with confidence, backed by data, clear trade-offs, and customer empathy.',
                             'Presenting a feature wish list without prioritizing trade-offs or justifying ROI.\nOmitting risk mitigation and edge-case handling from the executive summary.')
                        ]
                    }
                ],
                'quiz': {
                    'title': 'Product Management & Agile Strategy Final Quiz',
                    'questions': [
                        ('What is the primary difference between a Product Manager and a Project Manager?',
                         'Product Managers define what gets built and why; Project Managers oversee how and when it gets built.',
                         'Product Managers write backend code; Project Managers write frontend code.',
                         'Project Managers manage marketing budgets; Product Managers manage server deployments.',
                         'There is no difference; the terms are completely interchangeable.', 'A',
                         'Product Managers are responsible for product strategy, customer problem discovery, and business outcomes. Project Managers focus on timeline, resource allocation, and project delivery.'),
                        ('In the RICE prioritization framework, what does the "C" stand for?',
                         'Cost of Development', 'Customer Lifetime Value', 'Confidence score in the estimates', 'Complexity rating', 'C',
                         'RICE stands for Reach, Impact, Confidence, and Effort. Confidence serves as a discount factor when estimates are speculative.'),
                        ('What criteria must a well-crafted Agile User Story satisfy?',
                         'COBIT criteria', 'INVEST criteria (Independent, Negotiable, Valuable, Estimable, Small, Testable)', 'REST criteria', 'ACID criteria', 'B',
                         'Bill Wake formulated the INVEST acronym: Independent, Negotiable, Valuable, Estimable, Small, and Testable.'),
                        ('What is the definition of a healthy SaaS LTV to CAC ratio?',
                         'Less than 1:1', 'Between 1:2 and 1:1', 'Greater than or equal to 3:1', 'Exactly 0.5:1', 'C',
                         'An LTV:CAC ratio of 3:1 or higher indicates a healthy business model where customer lifetime value comfortably exceeds acquisition expenses.'),
                        ('What is the true purpose of a Minimum Viable Product (MVP)?',
                         'To release incomplete, buggy code to the public as quickly as possible',
                         'To maximize validated learning about customers with the least amount of effort and resources',
                         'To finalize the permanent architecture for the next decade',
                         'To spend 12 months in stealth mode before any user interaction', 'B',
                         'As formulated by Eric Ries in Lean Startup, an MVP is the smallest experiment that generates validated customer learning.')
                    ]
                }
            },

            # -----------------------------------------------------------------
            # COURSE 2: Management - Business Analytics & Financial Modeling
            # -----------------------------------------------------------------
            {
                'title': 'Business Analytics & Financial Decision Modeling',
                'slug': 'business-analytics-financial-modeling',
                'category_slug': 'management-business',
                'difficulty': 'Intermediate',
                'instructor_name': 'David Reynolds, CFA',
                'instructor_title': 'Director of Financial Planning & Analysis (FP&A)',
                'estimated_duration': '16 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800&q=80',
                'short_description': 'Build dynamic 3-statement financial models, DCF valuations, SaaS unit economics, cohort analytics, and executive dashboards.',
                'description': 'Master the financial and analytical principles that drive corporate decision making. Learn to parse and interlink the three core financial statements (Income Statement, Balance Sheet, Cash Flow), build fully dynamic financial forecasting models in Excel/Google Sheets, value companies using Discounted Cash Flow (DCF) and comparable multiples, evaluate capital investments via NPV and IRR, conduct Monte Carlo sensitivity analysis, and create executive KPI storytelling dashboards.',
                'learning_objectives': "Build dynamic, interconnected 3-statement financial models with zero hardcoded errors\nPerform Discounted Cash Flow (DCF) company valuations using WACC and terminal value\nEvaluate capital projects and acquisitions with Net Present Value (NPV) and Internal Rate of Return (IRR)\nAnalyze corporate liquidity, solvency, and operational efficiency using financial ratios\nModel customer acquisition costs (CAC), lifetime value (LTV), and cohort retention matrices\nDesign executive BI dashboards that translate complex financial data into strategic decisions",
                'prerequisites': "Basic comfort with basic mathematics (percentages, algebra)\nFamiliarity with spreadsheets (Excel or Google Sheets)\nInterest in corporate finance, business operations, or startup economics",
                'modules': [
                    {
                        'order': 1,
                        'title': 'Module 1: Corporate Financial Foundations & Statements',
                        'description': 'Analyze the mechanics and connections between the three core financial statements.',
                        'lessons': [
                            (1, 'Financial Statements', 'Understanding the Income Statement, Balance Sheet & Cash Flow', 25, 'xX34e891jLw',
                             '<h3>Understanding the Three Financial Statements</h3><p>Explore the fundamental accounting equation (Assets = Liabilities + Equity). Connect revenue recognition on the Income Statement to asset changes on the Balance Sheet and cash movements on the Cash Flow Statement.</p>',
                             'Net income flows from the Income Statement into retained earnings on the Balance Sheet.\nOperating cash flow reconciles net income with working capital changes and non-cash depreciation.\nCash is king: a company can report positive accounting profit while simultaneously going bankrupt from cash insolvency.',
                             'Confusing accounting revenue (accrual) with actual cash collections.\nTreating depreciation as a cash outflow rather than a non-cash accounting allocation.'),
                            (2, 'Working Capital', 'Working Capital & Liquidity Ratio Analysis', 25, 'k8L0_4fB88e',
                             '<h3>Working Capital & Liquidity Ratio Analysis</h3><p>Calculate current ratios, quick ratios, and cash conversion cycles (CCC). Learn how optimizing inventory turns and accounts receivable collections unlocks operational liquidity.</p>',
                             'Working Capital = Current Assets minus Current Liabilities.\nCash Conversion Cycle measures the days required to turn cash spent on inventory into cash collected from customers.\nNegative working capital can be advantageous for subscription and retail businesses (e.g., Amazon).',
                             'Failing to exclude illiquid inventory when evaluating short-term solvency with the Quick Ratio.\nIgnoring seasonal fluctuations when calculating average working capital balances.'),
                            (3, 'Profitability & Solvency', 'DuPont Analysis & Corporate Solvency Metrics', 25, 'm94X17L_5kM',
                             '<h3>DuPont Analysis & Corporate Solvency Metrics</h3><p>Deconstruct Return on Equity (ROE) into profit margin, asset turnover, and financial leverage. Gauge corporate solvency with debt-to-equity and interest coverage ratios.</p>',
                             'DuPont Formula: ROE = Net Profit Margin × Asset Turnover × Financial Leverage multiplier.\nDeconstructing ROE reveals whether high returns stem from operating excellence or risky borrowing.\nInterest Coverage Ratio (EBIT / Interest Expense) measures safety against debt default.',
                             'Evaluating ROE in isolation without checking whether debt leverage inflated the ratio.\nUsing EBITDA instead of EBIT when calculating interest coverage on capital-heavy businesses.'),
                            (4, 'Time Value of Money', 'Time Value of Money, Compounding & Discounting Principles', 25, 'p891X_43kLe',
                             '<h3>Time Value of Money, Compounding & Discounting Principles</h3><p>Master present value (PV), future value (FV), discount rates, and compounding periods. Understand why a dollar received today is always worth more than a dollar received tomorrow.</p>',
                             'Present Value formula: PV = FV / (1 + r)^n.\nDiscount rates reflect both the opportunity cost of capital and investment risk.\nContinuous compounding mathematically approaches e^(rt).',
                             'Using a nominal annual discount rate on quarterly or monthly cash flows without adjustment.\nConfusing simple interest with compound interest over multi-year horizons.')
                        ]
                    },
                    {
                        'order': 2,
                        'title': 'Module 2: Dynamic Financial Modeling & Forecasting',
                        'description': 'Construct fully dynamic, interconnected multi-year financial forecast models in spreadsheets.',
                        'lessons': [
                            (5, 'Spreadsheet Architecture', 'Best Practices in Financial Modeling & Model Design', 30, 'b8m6wJ1_51s',
                             '<h3>Best Practices in Financial Modeling</h3><p>Establish strict color-coding standards (blue for inputs, black for formulas, green for inter-sheet links). Build modular workbook structures that eliminate circular references.</p>',
                             'Separate input assumptions, calculations, and financial output summaries into dedicated worksheets.\nNever hardcode numeric constants inside formulas; always reference assumption cells.\nImplement error checks (Balance Sheet check: Assets minus Liabilities & Equity must equal zero).',
                             'Embedding hardcoded numbers inside formulas (e.g., =B5*1.08).\nAllowing circular references that create unstable calculation loops.'),
                            (6, '3-Statement Modeling', 'Building an Integrated 3-Statement Forecasting Model', 35, 'p53_k_8X6yM',
                             '<h3>Building an Integrated 3-Statement Model</h3><p>Drive revenue forecasts using pricing and volume drivers. Link depreciation schedules, debt interest schedules, and working capital schedules to complete the balance sheet loop.</p>',
                             'Build dedicated supporting schedules for Depreciation, Debt, and Working Capital.\nCash generated on the Cash Flow Statement becomes the ending Cash balance on the Balance Sheet.\nThe Balance Sheet must balance automatically without a "plug" figure.',
                             'Forcing balance sheets to balance using arbitrary plug numbers instead of rigorous schedules.\nNeglecting tax rate timing differences and net operating losses.'),
                            (7, 'Revenue Drivers', 'Bottom-Up Revenue Drivers & Cost Structure Modeling', 25, 'm47X_89Lp2e',
                             '<h3>Bottom-Up Revenue Drivers & Cost Structure Modeling</h3><p>Model variable vs fixed costs, gross margins, and contribution margins. Forecast revenues using funnel conversion rates, average contract values (ACV), and expansion upsells.</p>',
                             'Bottom-up driver models (Number of reps × quota attainment × average contract value) outperform naive percentage escalations.\nFixed costs remain constant over volume bands; variable costs scale directly with units sold.\nContribution margin indicates how each unit contributes to covering fixed overhead.',
                             'Treating semi-variable costs (e.g., customer support staffing) as purely fixed.\nForecasting perpetual linear growth without accounting for market saturation.'),
                            (8, 'Scenario Planning', 'Scenario Modeling & Sensitivity Analysis (Data Tables)', 25, 'w7xX_19L3pM',
                             '<h3>Scenario Modeling & Sensitivity Analysis (Data Tables)</h3><p>Use Excel Two-Variable Data Tables and Scenario Managers to model Bull, Base, and Bear cases. Identify which input assumptions exert the greatest sensitivity on EBITDA.</p>',
                             'Two-way data tables reveal the simultaneous impact of changing price and volume.\nBuild dynamic scenario switches using INDEX and MATCH or OFFSET functions.\nTornado diagrams visualize which variables introduce the greatest financial volatility.',
                             'Running static models that require manual copy-pasting to view alternate scenarios.\nFailing to test catastrophic downside scenarios (e.g., 50% revenue drop).')
                        ]
                    },
                    {
                        'order': 3,
                        'title': 'Module 3: Valuation, Capital Budgeting & Unit Economics',
                        'description': 'Master DCF valuation, NPV/IRR capital allocation, and SaaS unit economics modeling.',
                        'lessons': [
                            (9, 'DCF Valuation', 'Discounted Cash Flow (DCF) Modeling & Free Cash Flow to Firm', 30, 'z14f9m_28eK',
                             '<h3>Discounted Cash Flow (DCF) Modeling</h3><p>Calculate Unlevered Free Cash Flow (UFCF). Project cash flows across a 5-year discrete period, estimate terminal value using Gordon Growth and Exit Multiple approaches, and discount at WACC.</p>',
                             'Unlevered Free Cash Flow = NOPAT + D&A - CapEx - Change in Working Capital.\nWeighted Average Cost of Capital (WACC) combines the after-tax cost of debt and cost of equity.\nTerminal Value typically accounts for 60-80% of total enterprise value in DCF models.',
                             'Using Levered Free Cash Flow with WACC (mismatching capital claims and discount rates).\nAssuming an unrealistic terminal growth rate that exceeds long-term GDP growth.'),
                            (10, 'Comparable Multiples', 'Relative Valuation: Trading Comps & Precedent Transactions', 25, 'z8e01X_34Lm',
                             '<h3>Relative Valuation: Trading Comps & Precedent Transactions</h3><p>Value companies using market multiples: EV/Revenue, EV/EBITDA, and Price-to-Earnings (P/E). Understand when enterprise multiples are mandatory over equity multiples.</p>',
                             'Enterprise Value (EV) = Market Cap + Total Debt - Cash.\nEV multiples (EV/EBITDA, EV/Sales) are capital structure neutral; P/E depends on debt leverage.\nNormalize earnings by adjusting for one-off litigation, restructuring, or non-operating assets.',
                             'Comparing companies with fundamentally different accounting standards or revenue models without adjustment.\nApplying P/E ratios to unprofitable or high-debt companies.'),
                            (11, 'Capital Budgeting', 'Capital Budgeting Decisions: NPV vs IRR vs Payback Period', 25, 'V8jW_6QfX7A',
                             '<h3>Capital Budgeting Decisions: NPV vs IRR vs Payback</h3><p>Evaluate enterprise capital expenditures. Understand why Net Present Value (NPV) is mathematically superior to Internal Rate of Return (IRR) for mutually exclusive projects.</p>',
                             'NPV rule: accept any project with NPV > 0 discounted at the hurdle rate.\nIRR assumes cash flows are reinvested at the project\'s internal rate, which can inflate expectations.\nNPV accounts for project scale and reinvestment rate realism.',
                             'Selecting projects solely by IRR without considering absolute dollar value created (NPV).\nUsing simple payback period which ignores all cash flows after the payback date.'),
                            (12, 'SaaS Unit Economics', 'Modern Unit Economics: CAC, LTV & Cohort Retention', 25, 't4e9X72P_4J',
                             '<h3>Modern Unit Economics: CAC, LTV & Cohort Retention</h3><p>Deconstruct recurring revenue mechanics. Calculate Customer Acquisition Cost (CAC), Months to Recover CAC, Lifetime Value (LTV), Net Revenue Retention (NRR), and Logo Churn.</p>',
                             'Fully Loaded CAC must include all sales/marketing salaries, commissions, software tools, and ad spend.\nNet Revenue Retention (NRR) > 100% means the business grows even without adding a single new customer.\nCAC payback period should ideally be under 12 months for high-growth SaaS.',
                             'Excluding sales team salaries and overhead from the CAC calculation.\nCalculating LTV with gross revenue instead of gross margin (LTV = Gross Margin × ARPU / Churn).')
                        ]
                    },
                    {
                        'order': 4,
                        'title': 'Module 4: Business Intelligence & Executive Storytelling',
                        'description': 'Transform complex tabular data into actionable executive dashboards and decision presentations.',
                        'lessons': [
                            (13, 'Cohort Analysis', 'Cohort Analysis & Customer Lifetime Behavioral Modeling', 25, 'n83M_19eLpQ',
                             '<h3>Cohort Analysis & Customer Lifetime Modeling</h3><p>Build triangular cohort retention tables to track customer behavior across acquisition months. Detect product quality improvements or degradation over time.</p>',
                             'Triangle cohort tables expose whether newer cohorts retain better than older cohorts.\nSeparate logo retention (customer count) from dollar retention (revenue expansion/contraction).\nDetect the retention "smile" where resurrected customers offset churn.',
                             'Averaging churn across the entire customer base, masking high churn in recent signups.\nIgnoring contraction within retained accounts.'),
                            (14, 'Dashboard Architecture', 'Executive Dashboard Architecture & KPI Scorecards', 25, 'b74X_88e01J',
                             '<h3>Executive Dashboard Architecture & KPI Scorecards</h3><p>Design visual executive dashboards in spreadsheets or BI tools. Apply visual hierarchy, choose appropriate chart types (waterfall, bridge, trendline), and prevent clutter.</p>',
                             'Bridge (waterfall) charts clearly explain the variance between budget and actual performance.\nLimit executive dashboards to 5-7 core north-star metrics to maintain focus.\nProvide drill-down capability from high-level summaries into underlying drivers.',
                             'Using 3D pie charts or misleading dual-axis scales that distort data relationships.\nOverwhelming decision-makers with raw data tables lacking clear visual takeaways.'),
                            (15, 'Variance & Forecasting', 'Budget vs Actual (BvA) Variance Analysis & Rolling Forecasts', 25, 'p53_k_8X6yM',
                             '<h3>Budget vs Actual (BvA) Variance Analysis</h3><p>Decompose financial variances into volume, price, and mix variances. Transition legacy static annual budgets into dynamic 12-month rolling forecasts.</p>',
                             'Volume variance measures impact of selling more/fewer units; price variance measures pricing realization.\nRolling forecasts look forward 12-18 months regardless of fiscal year-end boundaries.\nTreat variances as diagnostic clues to operational bottlenecks rather than mere accounting deviations.',
                             'Treating the annual budget as an immutable operational document rather than updating rolling forecasts.\nBlaming sales teams for revenue shortfalls without isolating macroeconomic pricing shocks.'),
                            (16, 'Capstone Project', 'Capstone Project: Complete Acquisition Valuation & Board Deck', 35, 'kqtD5dpn9C8',
                             '<h3>Capstone Project: Acquisition Valuation & Board Deck</h3><p>Synthesize financial modeling and business analytics skills. Build a comprehensive M&A financial model with synergistic cost reductions, debt financing schedules, DCF valuation, and a boardroom investment memo.</p>',
                             'A complete investment memo pairs quantitative financial rigor with strategic qualitative narrative.\nClearly delineate standalone company value from post-merger synergy value.\nStress-test debt service covenants under severe downside operating conditions.',
                             'Assuming 100% of projected merger synergies will be realized immediately without implementation costs.\nFailing to include clear exit scenarios and capital return metrics for shareholders.')
                        ]
                    }
                ],
                'quiz': {
                    'title': 'Business Analytics & Financial Decision Modeling Final Quiz',
                    'questions': [
                        ('On which financial statement does Net Income directly link to Retained Earnings?',
                         'Balance Sheet', 'Income Statement', 'Statement of Cash Flows', 'Statement of Shareholder Equity', 'A',
                         'Net income from the Income Statement increases Retained Earnings on the Balance Sheet (minus any dividends paid).'),
                        ('What does the DuPont Analysis formula deconstruct Return on Equity (ROE) into?',
                         'Net Profit Margin × Asset Turnover × Financial Leverage',
                         'EBITDA × CapEx × Debt Ratio',
                         'Revenue × Gross Margin × Tax Rate',
                         'Operating Cash Flow ÷ Total Assets', 'A',
                         'DuPont analysis breaks ROE down into operational efficiency (profit margin), asset utilization (asset turnover), and financial risk (leverage).'),
                        ('Why is Net Present Value (NPV) mathematically superior to Internal Rate of Return (IRR)?',
                         'NPV is easier to calculate by hand',
                         'NPV assumes realistic reinvestment at the cost of capital and accounts for absolute project scale',
                         'NPV always equals zero at market equilibrium',
                         'NPV does not require a discount rate', 'B',
                         'IRR assumes cash flows are reinvested at the project\'s own internal rate (which can be unrealistically high) and ignores project scale. NPV assumes reinvestment at the opportunity cost of capital.'),
                        ('What does Net Revenue Retention (NRR) greater than 100% indicate for a SaaS business?',
                         'The business loses money on customer renewals',
                         'Revenue from existing customers grows organically through upsells and expansion, even without acquiring new customers',
                         'Customer acquisition cost is negative',
                         'The business has zero marketing expenses', 'B',
                         'NRR above 100% demonstrates negative net churn, where expansion revenue from retained accounts exceeds all lost revenue from churn and downgrades.'),
                        ('What is the formula for Unlevered Free Cash Flow (FCFF)?',
                         'Net Income + Cash Flow from Financing',
                         'NOPAT + Depreciation & Amortization - Capital Expenditures - Change in Net Working Capital',
                         'Gross Profit - Operating Expenses',
                         'EBITDA ÷ Total Debt', 'B',
                         'Unlevered Free Cash Flow represents cash generated by operations available to all capital providers before interest payments: NOPAT + non-cash charges - CapEx - ΔNWC.')
                    ]
                }
            },

            # -----------------------------------------------------------------
            # COURSE 3: Science - Computational Science & Mathematical Modeling
            # -----------------------------------------------------------------
            {
                'title': 'Computational Science & Mathematical Modeling with Python',
                'slug': 'computational-science-math-modeling',
                'category_slug': 'applied-sciences',
                'difficulty': 'Intermediate',
                'instructor_name': 'Dr. Elena Rostova',
                'instructor_title': 'Computational Physicist & Applied Mathematician',
                'estimated_duration': '15 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?auto=format&fit=crop&w=800&q=80',
                'short_description': 'Simulate physical systems, solve differential equations (ODEs), apply Monte Carlo methods, and analyze scientific data.',
                'description': 'Bridge the gap between theoretical science and high-performance computing. Designed for science, engineering, and mathematics students who want to model real-world physical and biological systems. Master numerical precision and floating-point errors, vectorized computations with NumPy and SciPy, numerical differentiation and integration (Simpson, Gauss-Legendre), ordinary differential equation solvers (Euler, Runge-Kutta 4, scipy.integrate), Monte Carlo stochastic simulations, chaotic dynamical systems, and Fourier transform signal analysis.',
                'learning_objectives': "Prevent numerical precision loss and catastrophic cancellation in scientific computation\nVectorize scientific simulations with NumPy broadcasting and SciPy algorithms\nImplement numerical integration (Trapezoidal, Simpson, adaptive quadrature)\nSolve non-linear Ordinary Differential Equations (ODEs) for physical and biological systems\nSimulate stochastic phenomena using Monte Carlo random walk algorithms\nModel non-linear dynamical systems, phase portraits, and bifurcation chaos",
                'prerequisites': "Basic understanding of Python programming (functions, loops)\nFamiliarity with introductory calculus (derivatives and basic integrals)\nBasic knowledge of linear algebra (vectors and matrices)",
                'modules': [
                    {
                        'order': 1,
                        'title': 'Module 1: Foundations of Scientific Computing & Vectorization',
                        'description': 'Master floating-point precision, vectorized array computations, and scientific data visualization.',
                        'lessons': [
                            (1, 'Numerical Representation', 'Floating-Point Arithmetic & Numerical Precision in Science', 25, 'fNk_zzaMoSs',
                             '<h3>Floating-Point Arithmetic & Precision</h3><p>Explore IEEE 754 floating-point standards. Understand machine epsilon, catastrophic cancellation, overflow/underflow, and numerical stability in scientific programming.</p>',
                             'Floating-point numbers have finite precision (float64 has ~15-17 significant decimal digits).\nAvoid subtracting nearly equal numbers to prevent catastrophic cancellation.\nAlways compare floating-point numbers with relative tolerances (e.g., math.isclose) rather than exact equality.',
                             'Using exact equality (a == b) with floating-point calculations.\nIgnoring error accumulation across millions of iterative calculation loops.'),
                            (2, 'NumPy Foundations', 'Vectorized Scientific Computing with NumPy', 25, '8Y0qQEh7dJg',
                             '<h3>Vectorized Scientific Computing with NumPy</h3><p>Leverage contiguous memory buffers, multidimensional ndarrays, broadcasting rules, and universal functions (ufuncs) to execute computations at C speed without Python loop overhead.</p>',
                             'NumPy operations bypass Python interpreter overhead by executing compiled C loops.\nBroadcasting allows element-wise operations between arrays of different compatible shapes.\nAvoid explicit Python for-loops over arrays; express operations as vectorized vector/matrix math.',
                             'Iterating over NumPy arrays using Python for-loops instead of vectorized ufuncs.\nCreating unnecessary array copies in memory rather than utilizing array slicing views.'),
                            (3, 'SciPy Toolkit', 'Scientific Algorithms & Optimization with SciPy', 25, 'vmEHCJofslg',
                             '<h3>Scientific Algorithms with SciPy</h3><p>Utilize scipy.optimize for non-linear root finding (Newton-Raphson, Brentq) and curve fitting. Explore sparse matrices, linear algebra solvers, and interpolation routines.</p>',
                             'scipy.optimize.brentq guarantees root convergence when bounds have opposite signs.\nCurve fitting finds optimal physical parameters by minimizing sum of squared residuals.\nSparse matrix representations conserve gigabytes of RAM in physical grid simulations.',
                             'Using gradient descent for root finding when bounded bracket methods (Brent) provide guaranteed convergence.\nNeglecting bounds on physical parameters during non-linear curve fitting.'),
                            (4, 'Scientific Visualization', 'Publishable Scientific Plotting with Matplotlib & Seaborn', 25, '3Xc3CA655Y4',
                             '<h3>Publishable Scientific Plotting</h3><p>Create publication-ready figures. Master contour plots, vector field streamplots, 3D surface meshes, error bars, and LaTeX math typography in figures.</p>',
                             'Always label axes with physical quantities and measurement units.\nUse error bars to reflect experimental and simulation uncertainty bounds.\nExport figures as vector graphics (.pdf, .svg) for publication crispness at any scale.',
                             'Omitting physical units on plot axes (e.g., labeling an axis "Time" without specifying seconds vs hours).\nUsing rainbow color maps (Jet) that distort data perception and are color-blind inaccessible.')
                        ]
                    },
                    {
                        'order': 2,
                        'title': 'Module 2: Numerical Calculus & Differential Equations',
                        'description': 'Implement finite difference approximations, numerical quadrature, and solve initial-value ODEs.',
                        'lessons': [
                            (5, 'Numerical Differentiation', 'Finite Difference Approximations & Error Convergence', 25, 'O4nC_4Q1X3k',
                             '<h3>Finite Difference Approximations</h3><p>Derive forward, backward, and central difference formulas from Taylor series expansions. Analyze truncation error versus round-off error trade-offs to choose optimal step sizes.</p>',
                             'Central difference approximation achieves second-order accuracy O(h^2) versus forward difference O(h).\nDecreasing step size h reduces truncation error until machine precision round-off error dominates.\nUse Richardson extrapolation to cancel leading-order error terms.',
                             'Making step size h too small (e.g., 1e-18), causing catastrophic floating-point cancellation.\nUsing first-order forward differences when high accuracy is required.'),
                            (6, 'Numerical Integration', 'Numerical Quadrature: Trapezoidal, Simpson & Gauss-Legendre', 25, 'b81X94_Le3m',
                             '<h3>Numerical Quadrature & Integration</h3><p>Evaluate definite integrals numerically when analytical antiderivatives do not exist. Implement Trapezoidal Rule, Simpson\'s 1/3 Rule, and Gauss-Legendre quadrature.</p>',
                             'Simpson\'s rule approximates integrands with piecewise quadratic polynomials, achieving O(h^4) accuracy.\nGauss-Legendre quadrature achieves exact results for polynomials of degree 2n-1 using only n evaluation points.\nAdaptive quadrature concentrates evaluation points dynamically in regions of high curvature.',
                             'Using simple Riemann sums for production scientific models.\nFailing to handle integrands with endpoint singularities or discontinuities.'),
                            (7, 'ODE Solvers: Foundations', 'Solving Initial Value ODEs: Euler vs Runge-Kutta 4 (RK4)', 30, 'q94_x7812Le',
                             '<h3>Solving Initial Value ODEs</h3><p>Model dynamic physical systems. Implement Euler\'s method and the classical 4th-Order Runge-Kutta (RK4) algorithm. Measure global truncation error and numerical stability limits.</p>',
                             'Euler\'s method has first-order error O(h) and frequently causes numerical instability or energy drift.\nRunge-Kutta 4 evaluates four trial slopes across the time step, achieving fourth-order error O(h^4).\nSymplectic integrators (Verlet) preserve energy over long time horizons in Hamiltonian mechanics.',
                             'Using Euler\'s method for oscillatory physical systems, which artificially inflates system energy to infinity.\nUsing fixed step sizes for systems with rapid transient bursts.'),
                            (8, 'Coupled Systems', 'Modeling Coupled Non-Linear Systems: Lotka-Volterra & Orbit Mechanics', 30, 'z41X78_eL9p',
                             '<h3>Modeling Coupled Non-Linear Systems</h3><p>Formulate multi-variable systems of first-order differential equations. Simulate predator-prey population dynamics (Lotka-Volterra) and planetary orbital mechanics.</p>',
                             'Any n-th order ODE can be converted into a system of n coupled first-order ODEs.\nConserved quantities (total energy, angular momentum) verify simulation correctness.\nscipy.integrate.solve_ivp provides battle-tested adaptive Runge-Kutta solvers (DOP853, Radau).',
                             'Attempting to solve second-order equations directly without converting to coupled state-space vectors.\nIgnoring conservation of momentum and energy as validation benchmarks.')
                        ]
                    },
                    {
                        'order': 3,
                        'title': 'Module 3: Stochastic Simulation & Scientific Signal Analysis',
                        'description': 'Apply Monte Carlo methods, simulate random walks, and analyze scientific signals with Fourier transforms.',
                        'lessons': [
                            (9, 'Monte Carlo Methods', 'Monte Carlo Methods & Stochastic Simulation', 25, 'w47X90_pLe1',
                             '<h3>Monte Carlo Stochastic Simulation</h3><p>Utilize pseudo-random number generators to solve deterministic and probabilistic problems. Calculate multidimensional integrals, estimate Pi, and model particle diffusion.</p>',
                             'Monte Carlo convergence error scales as 1 / sqrt(N), independent of dimensionality.\nFor high-dimensional integration (d > 4), Monte Carlo substantially outperforms deterministic grid quadrature.\nAlways set explicit random seeds to ensure scientific experiment reproducibility.',
                             'Using unseeded random number generators, preventing peer review and reproducibility.\nAssuming Monte Carlo error decreases linearly with sample size rather than square root.'),
                            (10, 'Random Walks & Diffusion', 'Brownian Motion, Random Walks & Diffusion PDEs', 25, 'k81X34_eL7m',
                             '<h3>Brownian Motion & Random Walks</h3><p>Model particle diffusion and financial random walks. Derive the connection between macroscopic Fickian diffusion equations and microscopic stochastic random walks.</p>',
                             'Mean squared displacement of a random walk scales linearly with time: <r^2> = 2Dt.\nThe central limit theorem guarantees random walk positions converge to Gaussian distributions.\nSimulate microscopic particle dynamics to extract macroscopic diffusion coefficients.',
                             'Confusing root mean square displacement (scales as sqrt(t)) with mean displacement (equals zero).\nNeglecting boundary collision conditions in bounded domains.'),
                            (11, 'Chaos & Non-linear Dynamics', 'Chaos Theory, Strange Attractors & The Lorenz System', 30, 'p47X19_eL2k',
                             '<h3>Chaos Theory & The Lorenz Attractor</h3><p>Explore sensitive dependence on initial conditions (the butterfly effect). Solve the Lorenz equations, compute Lyapunov exponents, and visualize 3D strange attractors.</p>',
                             'Deterministic systems can exhibit unpredictable, chaotic behavior without any random noise.\nPositive Lyapunov exponents quantify the exponential divergence of infinitesimally close trajectories.\nStrange attractors possess fractal dimension and bounded phase space.',
                             'Confusing non-deterministic randomness with deterministic chaos.\nBelieving that increasing numerical precision can eliminate chaos predictability horizons.'),
                            (12, 'Fourier Analysis', 'Fast Fourier Transforms (FFT) & Scientific Signal Processing', 25, 'm81X34_pLe9',
                             '<h3>Fast Fourier Transforms (FFT)</h3><p>Decompose complex time-series signals into frequency spectrum components using the Cooley-Tukey FFT algorithm. Filter noise, detect resonant modes, and avoid aliasing.</p>',
                             'The Nyquist-Shannon sampling theorem requires sampling at least twice the highest frequency present: f_s > 2*f_max.\nFFT reduces the computational complexity of discrete Fourier transforms from O(N^2) to O(N log N).\nApply windowing functions (Hanning, Blackman) to suppress spectral leakage.',
                             'Sampling signals below the Nyquist rate, causing high frequencies to disguise as false low frequencies (aliasing).\nPerforming FFT on non-periodic boundaries without applying a window function.')
                        ]
                    },
                    {
                        'order': 4,
                        'title': 'Module 4: Boundary Value Problems & Applied Capstone',
                        'description': 'Solve partial differential equations and execute a complete scientific simulation deliverable.',
                        'lessons': [
                            (13, 'PDEs & Heat Diffusion', 'Partial Differential Equations: Heat Diffusion on a 2D Grid', 30, 't81X49_pLe0',
                             '<h3>2D Heat Diffusion & Finite Difference Grids</h3><p>Discretize continuous spatial domains. Implement explicit and implicit finite-difference methods to solve the 2D heat equation and verify the CFL stability condition.</p>',
                             'The CFL condition requires alpha * dt / (dx^2) <= 0.5 for explicit 2D diffusion stability.\nImplicit methods (Crank-Nicolson) are unconditionally stable and permit larger time steps.\nVectorize Laplacian calculations using spatial slice slicing or scipy.ndimage.convolve.',
                             'Violating the CFL stability limit in explicit schemes, producing immediate exponential divergence (NaNs).\nUsing slow nested for-loops to update 2D grid cells instead of vectorized array operations.'),
                            (14, 'Optimization in Science', 'Global Optimization: Simulated Annealing & Genetic Algorithms', 25, 'w81X78_pLe4',
                             '<h3>Global Optimization & Simulated Annealing</h3><p>Find global minima in complex, multi-modal physical energy landscapes. Implement Simulated Annealing inspired by statistical thermodynamics to escape local minima.</p>',
                             'Gradient descent gets trapped in local minima; simulated annealing accepts uphill moves probabilistically.\nMetropolis acceptance probability: P = exp(-dE / T).\nCooling schedules determine the transition from exploration (high T) to exploitation (low T).',
                             'Cooling temperature too rapidly ("quenching"), freezing the simulation in sub-optimal local minima.\nUsing global optimization algorithms when smooth analytical gradients are available for faster methods.'),
                            (15, 'High Performance Python', 'Accelerating Scientific Python with Numba & JIT Compilation', 25, 'n81X49_eL1p',
                             '<h3>Accelerating Scientific Python with Numba</h3><p>Compile numerical Python functions directly into machine code at runtime using LLVM and Numba @jit(nopython=True). Unlock C/Fortran execution performance in pure Python.</p>',
                             'Numba compiles typed numerical Python code to native CPU assembly via LLVM.\nUse @njit(parallel=True) to distribute loop iterations across multiple CPU cores automatically.\nKeep compiled functions strictly numerical; avoid passing complex Python objects or dictionaries.',
                             'Falling back to object mode in Numba by using unsupported Python features.\nNeglecting first-call compilation overhead during performance benchmarking.'),
                            (16, 'Capstone Project', 'Capstone: Epidemic Simulation with SIR Model & Network Diffusion', 35, '1vR3W4666RQ',
                             '<h3>Capstone Project: Multi-Scale Epidemic Network Diffusion</h3><p>Synthesize all scientific computing techniques. Build a multi-scale epidemiological simulator combining coupled differential equations (SEIR model), Monte Carlo agent-based contact networks, and interactive phase plots.</p>',
                             'Epidemic thresholds depend strictly on the basic reproduction number R_0.\nNetwork topology (scale-free vs random) dramatically alters contagion percolation thresholds.\nDeliver clean, reproducible scientific code with automated parameter sweeps and publication-grade figures.',
                             'Assuming homogeneous population mixing when real contagion occurs across clustered social networks.\nHardcoding simulation parameters without programmatic configuration.')
                        ]
                    }
                ],
                'quiz': {
                    'title': 'Computational Science & Mathematical Modeling Final Quiz',
                    'questions': [
                        ('Why does the classical Runge-Kutta 4th Order (RK4) method outperform Euler\'s method for ODEs?',
                         'RK4 has lower computational complexity than Euler',
                         'RK4 achieves fourth-order error O(h^4) by evaluating four intermediate slopes across each step',
                         'RK4 does not require calculating derivatives',
                         'RK4 only works for linear algebraic equations', 'B',
                         'Euler\'s method evaluates the slope once at the beginning of the interval (O(h) error), whereas RK4 evaluates four weighted trial slopes across the interval, resulting in O(h^4) global accuracy.'),
                        ('What is the convergence rate of standard Monte Carlo integration as sample size N increases?',
                         'O(1/N)', 'O(1/N^2)', 'O(1/sqrt(N))', 'O(log N)', 'C',
                         'Due to the Central Limit Theorem, Monte Carlo integration error scales as 1/sqrt(N), making its convergence rate independent of the problem dimensionality.'),
                        ('What fundamental requirement must be satisfied to prevent aliasing when digitizing a continuous signal with Fast Fourier Transform?',
                         'The sampling frequency must be at least twice the maximum frequency in the signal (Nyquist Criterion)',
                         'The signal must be strictly linear',
                         'The sample size must be an odd number',
                         'The amplitude must be normalized to exactly 1.0', 'A',
                         'The Nyquist-Shannon sampling theorem states that the sampling frequency f_s must exceed 2 * f_max to accurately reconstruct all frequencies without aliasing artifacts.'),
                        ('What happens in an explicit finite-difference simulation of heat diffusion if the CFL condition is violated?',
                         'The simulation runs slightly slower',
                         'The simulation becomes numerically unstable and results blow up exponentially to NaNs/infinity',
                         'The boundary conditions become periodic',
                         'The temperature cools to absolute zero instantly', 'B',
                         'In explicit time-stepping schemes for parabolic PDEs, exceeding the CFL stability threshold causes errors to amplify exponentially with each step, destroying the simulation.'),
                        ('What is catastrophic cancellation in floating-point scientific calculations?',
                         'A hardware failure in the CPU floating-point unit',
                         'The severe loss of precision that occurs when subtracting two nearly equal floating-point numbers',
                         'Rounding numbers to the nearest integer',
                         'Dividing any number by zero', 'B',
                         'When subtracting two nearly identical floating-point numbers, the most significant digits cancel out, leaving only low-precision rounding error in the result.')
                    ]
                }
            },

            # -----------------------------------------------------------------
            # COURSE 4: Science - Bioinformatics & Genomics Data Analysis
            # -----------------------------------------------------------------
            {
                'title': 'Bioinformatics & Genomics Data Analysis',
                'slug': 'bioinformatics-genomics-data',
                'category_slug': 'applied-sciences',
                'difficulty': 'Beginner',
                'instructor_name': 'Dr. Marcus Vance',
                'instructor_title': 'Computational Biologist & Genomicist',
                'estimated_duration': '14 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1530497610245-94d3c16cda28?auto=format&fit=crop&w=800&q=80',
                'short_description': 'Parse DNA/RNA sequencing datasets, align genomic sequences (BLAST), call genetic variants (VCF), and visualize molecular structures.',
                'description': 'Enter the high-demand field at the crossroads of molecular biology, computer science, and data analytics. Learn how raw biological sequences are digitized and decoded into actionable scientific insights. Master standard genomics file formats (FASTA, FASTQ, SAM, BAM, VCF), manipulate biological records using Biopython, understand dynamic programming sequence alignment (Needleman-Wunsch, Smith-Waterman, BLAST heuristics), construct phylogenetic evolutionary trees, execute Next-Generation Sequencing (NGS) quality control, call single nucleotide polymorphisms (SNPs), and render 3D protein structures with PyMOL.',
                'learning_objectives': "Parse and manipulate FASTA and FASTQ biological sequence datasets with Biopython\nImplement dynamic programming algorithms for global and local sequence alignment\nPerform high-throughput sequence similarity searches using BLAST heuristics\nProcess Next-Generation Sequencing (NGS) read quality metrics and alignment (BWA/SAMtools)\nIdentify and annotate genetic variants from VCF datasets\nVisualize and analyze 3D macromolecular protein structures from PDB files",
                'prerequisites': "Basic programming literacy in Python (strings, dictionaries, file I/O)\nIntroductory high school or college biology knowledge (DNA, RNA, proteins)\nCuriosity about modern genetics and computational healthcare",
                'modules': [
                    {
                        'order': 1,
                        'title': 'Module 1: Molecular Biology Foundations & Biopython',
                        'description': 'Master the central dogma of molecular biology and computational sequence manipulation with Biopython.',
                        'lessons': [
                            (1, 'Central Dogma', 'The Central Dogma & Computational Biology Principles', 20, '3e_X147Le9m',
                             '<h3>The Central Dogma & Computational Biology</h3><p>Explore DNA, RNA transcription, and protein translation. Understand the four nucleotide bases (A, C, G, T), complementary base pairing, codons, and open reading frames (ORFs).</p>',
                             'DNA is transcribed into messenger RNA (A->U, T->A, C->G, G->C), which is translated into 20 amino acids.\nGenetic information is directional: 5\' to 3\' prime ends.\nComputational biology treats genetic sequences as informational strings with strict biochemical constraints.',
                             'Forgetting that RNA replaces Thymine (T) with Uracil (U).\nIgnoring sequence directionality (reading a sequence 3\' to 5\' instead of 5\' to 3\').'),
                            (2, 'Genomics Formats', 'Genomic Data Formats: FASTA, FASTQ & Quality Scores', 25, 'q81X49_eLe7',
                             '<h3>Genomic Data Formats: FASTA & FASTQ</h3><p>Deconstruct standard bioinformatics file formats. Understand FASTA headers and parse FASTQ quality scores encoded in ASCII Phred characters (Phred Q-scores).</p>',
                             'FASTA files store reference biological sequences with header lines beginning with ">".\nFASTQ files store 4 lines per sequencing read: ID, sequence, separator, and ASCII quality string.\nPhred score Q = -10 * log10(P_error); a Q30 score indicates a 99.9% base call accuracy (1 in 1,000 error rate).',
                             'Modifying FASTA headers carelessly, breaking downstream pipeline parsers.\nTreating FASTQ ASCII characters as plain text without decoding them to Phred probability scores.'),
                            (3, 'Biopython Core', 'Manipulating Sequences with Biopython: Seq, SeqRecord & SeqIO', 25, 'w47X89_pLe3',
                             '<h3>Manipulating Sequences with Biopython</h3><p>Use Biopython\'s Seq and SeqRecord objects to calculate GC-content, reverse complements, transcription, and translation into amino acid polypeptides.</p>',
                             'Biopython Seq objects behave like immutable Python strings with biological methods (reverse_complement, translate).\nSeqIO.parse processes massive multi-gigabyte sequence files iteratively without exhausting RAM.\nGC-content influences DNA thermal stability (melting temperature) and sequencing depth.',
                             'Loading an entire 50GB FASTQ file into a Python list in RAM instead of using iterator streams.\nTranslating non-coding DNA strands without identifying the correct reading frame.'),
                            (4, 'Motif Discovery', 'Pattern Matching, Motif Discovery & Regular Expressions', 25, 'b81X78_eL4m',
                             '<h3>Pattern Matching & Genomic Motifs</h3><p>Identify biological signals: restriction enzyme cleavage sites, transcription factor binding motifs, and CpG islands using regular expressions and consensus sequence matrices.</p>',
                             'Position Weight Matrices (PWMs) quantify the probability of each nucleotide at each motif position.\nCpG islands often indicate active gene promoter regions in vertebrate genomes.\nUse regex to search for IUPAC degenerate nucleotide codes (e.g., R for A or G, Y for C or T).',
                             'Relying on exact string matches when biological binding motifs permit degenerate variation.\nSearching only one strand and missing motifs situated on the reverse complement strand.')
                        ]
                    },
                    {
                        'order': 2,
                        'title': 'Module 2: Sequence Alignment & Phylogenetics',
                        'description': 'Implement dynamic programming alignment algorithms and reconstruct evolutionary family trees.',
                        'lessons': [
                            (5, 'Dynamic Programming Alignment', 'Global Sequence Alignment: Needleman-Wunsch Algorithm', 30, 'z47X19_eLe0',
                             '<h3>Global Sequence Alignment: Needleman-Wunsch</h3><p>Master dynamic programming in bioinformatics. Construct scoring matrices with match bonuses, mismatch penalties, and gap costs to find the optimal end-to-end alignment.</p>',
                             'Needleman-Wunsch guarantees the mathematically optimal global alignment between two sequences.\nScoring matrix recurrence: S(i,j) = max(diag + match/mismatch, up + gap, left + gap).\nTraceback from the bottom-right corner to the top-left yields the optimal aligned sequence.',
                             'Confusing global alignment (comparing entire homologous genes) with local alignment (finding shared domains).\nNeglecting affine gap penalties, which penalize gap openings more heavily than gap extensions.'),
                            (6, 'Local Alignment', 'Local Sequence Alignment: Smith-Waterman Algorithm', 30, 'p81X78_pLe9',
                             '<h3>Local Sequence Alignment: Smith-Waterman</h3><p>Locate conserved sub-regions and functional protein domains within divergent sequences. Understand why Smith-Waterman resets negative matrix scores to zero.</p>',
                             'Smith-Waterman resets scoring cells to zero when all parent paths are negative: S(i,j) = max(0, ...).\nTraceback begins at the highest score anywhere in the matrix and stops when a cell with score 0 is encountered.\nIdeal for identifying shared structural domains between distantly related organisms.',
                             'Starting the Smith-Waterman traceback from the bottom-right corner instead of the maximum matrix value.\nUsing local alignment when sequences are already known to be identical end-to-end.'),
                            (7, 'BLAST Heuristics', 'High-Throughput Sequence Search: BLAST Algorithm', 25, 'm81X49_pLe2',
                             '<h3>BLAST: Basic Local Alignment Search Tool</h3><p>Explore the heuristic algorithm that revolutionized bioinformatics. Learn how BLAST breaks queries into k-mer words, extends seeds, and evaluates statistical E-values.</p>',
                             'BLAST trades a tiny margin of optimality for a 1,000x speed increase over Smith-Waterman.\nThe Expect value (E-value) represents the number of false-positive matches expected purely by random chance.\nLower E-values (e.g., 1e-50) signify biologically significant evolutionary homology.',
                             'Relying solely on percent identity without verifying the E-value and query coverage.\nInterpreting a high score on low-complexity repetitious sequences (e.g., poly-A tails) as a true match.'),
                            (8, 'Phylogenetic Trees', 'Phylogenetics: Reconstructing Evolutionary Trees', 25, 'k47X89_eLe1',
                             '<h3>Reconstructing Phylogenetic Trees</h3><p>Infer evolutionary relationships between species. Calculate genetic distance matrices, build trees using UPGMA and Neighbor-Joining algorithms, and validate branches with bootstrap resampling.</p>',
                             'Phylogenetic trees depict inferred evolutionary branching patterns from common ancestors.\nNeighbor-Joining produces unrooted additive trees without assuming a strict molecular clock.\nBootstrap values (>70-80%) indicate statistical confidence in specific phylogenetic clades.',
                             'Assuming all branches evolve at an identical constant evolutionary rate (molecular clock fallacy).\nMisinterpreting horizontal node rotation in tree diagrams as an evolutionary ordering.')
                        ]
                    },
                    {
                        'order': 3,
                        'title': 'Module 3: Next-Generation Sequencing & Variant Calling',
                        'description': 'Process raw NGS sequencing reads, map to reference genomes, and detect genetic variants.',
                        'lessons': [
                            (9, 'NGS Technologies', 'Next-Generation Sequencing (NGS) Technologies & Workflows', 25, 'w81X49_pLe7',
                             '<h3>Next-Generation Sequencing Technologies</h3><p>Compare Illumina sequencing-by-synthesis with long-read sequencing (Pacific Biosciences, Oxford Nanopore). Understand library preparation, paired-end reads, and coverage depth.</p>',
                             'Illumina short reads offer high base accuracy (>99.9%) but struggle to resolve genomic repeats.\nNanopore long reads span thousands of bases, facilitating structural variant detection and de novo assembly.\nSequencing coverage depth (e.g., 30x) ensures statistical confidence across diploid alleles.',
                             'Treating PCR duplication artifacts as true biological sequencing depth.\nUsing short reads alone to assemble highly repetitive genomic centromeres.'),
                            (10, 'Quality Control & Trimming', 'NGS Quality Control: FastQC & Adapter Trimming', 25, '3e_X147Le9m',
                             '<h3>NGS Quality Control & Preprocessing</h3><p>Assess raw sequencing data quality using FastQC metrics. Detect base quality degradation at read ends, adapter contamination, and trim low-quality bases with cutadapt.</p>',
                             'Examine per-base sequence quality, per-tile quality, and adapter contamination profiles.\nTrim sequencing adapters and filter out reads whose average Phred quality falls below Q20.\nQuality control before alignment prevents wasted computational hours and false-positive variant calls.',
                             'Aligning raw sequencing reads without removing sequencing adapters.\nOver-trimming reads so aggressively that remaining fragments lose unique genomic alignment specificity.'),
                            (11, 'Read Mapping', 'Read Mapping to Reference Genomes: BWA & SAM/BAM Format', 30, 'q81X49_eLe7',
                             '<h3>Mapping Reads with BWA & SAM/BAM Files</h3><p>Align millions of short reads against multi-gigabyte reference genomes using the Burrows-Wheeler Transform (BWT). Index and filter BAM alignments with SAMtools.</p>',
                             'Burrows-Wheeler Transform (BWT) enables indexing whole human genomes into <4GB of memory for rapid searching.\nSAM (Sequence Alignment/Map) format stores read coordinates, CIGAR alignment strings, and mapping quality.\nBAM is the compressed, indexed binary version of SAM required for rapid random access.',
                             'Attempting to edit or view massive multi-gigabyte BAM files with text editors.\nFailing to sort and index BAM files prior to running variant callers.'),
                            (12, 'Variant Calling', 'Variant Calling: SNPs, Indels & VCF File Analysis', 30, 'n47X78_eLe3',
                             '<h3>Variant Calling & VCF Files</h3><p>Identify Single Nucleotide Polymorphisms (SNPs) and small Insertions/Deletions (Indels) using GATK best practices. Parse VCF (Variant Call Format) files and filter false positives.</p>',
                             'VCF files record chromosome, position, reference allele, alternate allele, quality score, and genotype (0/0, 0/1, 1/1).\nApply hard filtering or Variant Quality Score Recalibration (VQSR) to remove PCR artifacts.\nAnnotate variants with databases (ClinVar, dbSNP) to determine clinical pathogenic significance.',
                             'Treating every raw mismatch in a BAM alignment as a true genetic mutation.\nIgnoring read strand bias and low mapping quality around repetitive genomic regions.')
                        ]
                    },
                    {
                        'order': 4,
                        'title': 'Module 4: Structural Biology & Applied Genomics Capstone',
                        'description': 'Analyze 3D protein structures, evaluate gene expression, and execute a complete variant pipeline.',
                        'lessons': [
                            (13, 'RNA-Seq Analysis', 'RNA-Seq: Gene Expression Profiling & Differential Expression', 25, 't81X19_pLe2',
                             '<h3>RNA-Seq Gene Expression Profiling</h3><p>Measure transcriptome-wide gene activity. Quantify transcript abundance with TPM/FPKM, model read count distributions with negative binomial models (DESeq2), and identify differentially expressed genes.</p>',
                             'RNA-Seq raw read counts follow negative binomial distributions due to biological overdispersion.\nNormalize counts by library size and gene length (TPM - Transcripts Per Million).\nVolcano plots visualize both statistical significance (p-value) and biological magnitude (log2 fold change).',
                             'Comparing raw read counts directly across different sequencing libraries without normalization.\nUsing standard t-tests on raw RNA-seq counts rather than generalized linear models (DESeq2).'),
                            (14, 'Structural Bioinformatics', '3D Protein Structures, PDB Files & PyMOL Visualization', 25, 'b47X49_eLe9',
                             '<h3>3D Protein Structures & PDB Files</h3><p>Explore the Protein Data Bank (PDB). Understand atomic coordinate records, secondary structure elements (alpha helices, beta sheets), and visualize binding pockets with PyMOL.</p>',
                             'PDB files record 3D spatial (X, Y, Z) Cartesian coordinates for every atom in a biomolecule.\nHydrogen bonding patterns dictate secondary structure folding (alpha-helices and beta-sheets).\nIdentify active catalytic sites and drug binding pockets by analyzing electrostatic surface potentials.',
                             'Assuming all PDB structures are 100% rigid; real macromolecules undergo dynamic thermal fluctuations.\nIgnoring the resolution (in Angstroms) of crystal structures when evaluating atomic detail.'),
                            (15, 'Genome Assembly', 'De Novo Genome Assembly & Graph Algorithms', 25, 'm81X78_pLe0',
                             '<h3>De Novo Genome Assembly: Overlap & De Bruijn Graphs</h3><p>Assemble whole genomes without a reference template. Compare Overlap-Layout-Consensus (OLC) methods with De Bruijn graph algorithms based on k-mer decomposition.</p>',
                             'De Bruijn graphs decompose reads into k-mers and represent assembly as finding an Eulerian path through the graph.\nChoice of k-mer size balances graph connectivity against repeat resolution.\nContigs are evaluated using the N50 metric: the length where half the genome is contained in contigs of that size or larger.',
                             'Choosing a k-mer size smaller than repetitive elements, causing the De Bruijn graph to collapse into tangled loops.\nInterpreting a high contig count as high assembly quality without checking the N50 metric.'),
                            (16, 'Capstone Project', 'Capstone: End-to-End Rare Disease Variant Discovery Pipeline', 35, '1vR3W4666RQ',
                             '<h3>Capstone Project: Rare Disease Variant Discovery Pipeline</h3><p>Synthesize all bioinformatics skills. Process a patient\'s paired-end whole-exome sequencing dataset from raw FASTQ reads through alignment, variant calling, and clinical annotation to identify a causal pathogenic mutation.</p>',
                             'A production bioinformatics pipeline combines quality control, read mapping, variant calling, and clinical annotation.\nFilter variants against population frequency databases (gnomAD): rare disease mutations typically have <0.1% allele frequency.\nDocument pipeline execution with reproducible Nextflow or Snakemake workflow syntax.',
                             'Overlooking heterozygous versus homozygous inheritance models when filtering family trios.\nFailing to preserve software version records and random seeds for clinical compliance.')
                        ]
                    }
                ],
                'quiz': {
                    'title': 'Bioinformatics & Genomics Data Analysis Final Quiz',
                    'questions': [
                        ('In a FASTQ sequencing file, what does a Phred quality score of Q30 represent?',
                         'A 30% error rate',
                         'A 1 in 10 error rate (90% accuracy)',
                         'A 1 in 1,000 error rate (99.9% accuracy)',
                         'A sequence of 30 adenine bases', 'C',
                         'The Phred quality formula is Q = -10 * log10(P). A score of Q30 corresponds to a probability of error of 0.001, or 99.9% base call accuracy.'),
                        ('What is the key algorithmic difference between Needleman-Wunsch and Smith-Waterman sequence alignment?',
                         'Needleman-Wunsch is heuristic; Smith-Waterman is exact',
                         'Needleman-Wunsch calculates global alignment; Smith-Waterman calculates local alignment by resetting negative matrix values to 0',
                         'Smith-Waterman only works on RNA, not DNA',
                         'Needleman-Wunsch does not support gap penalties', 'B',
                         'Needleman-Wunsch aligns entire sequences from end to end (global). Smith-Waterman searches for optimal matching subsequences (local) by setting negative cell scores to zero.'),
                        ('What does an E-value of 1e-45 indicate in a NCBI BLAST search result?',
                         'The match has a 45% chance of being wrong',
                         'The match is statistically significant and highly unlikely to occur by random chance',
                         'The sequence is 45 base pairs long',
                         'The query sequence has 45 mutations', 'B',
                         'The BLAST E-value (Expect value) represents the number of expected false-positive matches with equal or better score by random chance. Values close to zero (e.g., 1e-45) reflect strong evolutionary homology.'),
                        ('In a Variant Call Format (VCF) file, what does the genotype 0/1 signify for a diploid organism?',
                         'Homozygous for the reference allele',
                         'Homozygous for the alternate allele',
                         'Heterozygous (one reference allele and one alternate allele)',
                         'A sequencing error with no alleles called', 'C',
                         'In standard VCF encoding, 0 represents the reference allele and 1 represents the alternate allele. 0/1 denotes a heterozygous call, while 0/0 is homozygous reference and 1/1 is homozygous alternate.'),
                        ('Why is the Burrows-Wheeler Transform (BWT) widely used in NGS read alignment tools like BWA?',
                         'It permanently translates DNA into protein sequences',
                         'It compresses and indexes gigabase reference genomes so reads can be mapped in memory at high speed',
                         'It eliminates all sequencing errors automatically',
                         'It converts short reads into long reads', 'B',
                         'The Burrows-Wheeler Transform (BWT) combined with FM-indexing allows multi-gigabyte reference genomes (such as the human genome) to reside in RAM (<4GB) for extremely rapid short-read pattern matching.')
                    ]
                }
            },

            # -----------------------------------------------------------------
            # COURSE 5: AI - Applied Generative AI, LLMs & Prompt Engineering
            # -----------------------------------------------------------------
            {
                'title': 'Applied Generative AI, Large Language Models & Prompt Engineering',
                'slug': 'applied-generative-ai-llms',
                'category_slug': 'artificial-intelligence',
                'difficulty': 'Intermediate',
                'instructor_name': 'Dr. Alex Morgan',
                'instructor_title': 'Staff AI Research Scientist & GenAI Lead',
                'estimated_duration': '18 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1677442136019-21780efad99a?auto=format&fit=crop&w=800&q=80',
                'short_description': 'Build production GenAI systems: Prompt Engineering patterns, RAG pipelines, ChromaDB vector databases, LangChain, and AI agents.',
                'description': 'Master the architectures, patterns, and production engineering practices that power the modern Generative AI revolution. Move beyond naive chatbot wrappers to build resilient, enterprise-grade AI applications. Explore Transformer attention mechanisms and tokenization mechanics, master systematic Prompt Engineering patterns (Chain-of-Thought, ReAct, Few-Shot), implement production Retrieval-Augmented Generation (RAG) with vector databases (ChromaDB, FAISS), optimize chunking and semantic re-ranking, orchestrate autonomous multi-tool AI agents with function calling, evaluate hallucinations with RAGAS, and manage latency, security, and inference costs.',
                'learning_objectives': "Deconstruct Transformer attention mechanisms, positional encodings, and tokenization math\nApply systematic prompt engineering frameworks: Few-Shot, Chain-of-Thought (CoT), and ReAct\nImplement vector databases (ChromaDB/FAISS) with high-dimensional embedding similarity search\nBuild production Retrieval-Augmented Generation (RAG) pipelines with hybrid search and re-ranking\nOrchestrate tool-calling AI agents using function calling and structured JSON outputs\nEvaluate GenAI applications systematically using RAGAS and deploy safety guardrails",
                'prerequisites': "Proficiency with Python programming (classes, functions, async)\nBasic familiarity with REST APIs and JSON data structures\nConceptual understanding of machine learning vectors and basic linear algebra",
                'modules': [
                    {
                        'order': 1,
                        'title': 'Module 1: Transformer Architecture & Modern Prompt Engineering',
                        'description': 'Understand how modern LLMs work and implement systematic prompt engineering frameworks.',
                        'lessons': [
                            (1, 'LLM Foundations', 'Transformer Architecture, Attention & Tokenization Mechanics', 25, 'mEsleV16qdo',
                             '<h3>Transformer Architecture & Attention Mechanics</h3><p>Demystify modern Large Language Models. Explore self-attention mechanisms, query-key-value dot products, causal masking, byte-pair encoding (BPE) tokenization, and temperature sampling.</p>',
                             'Transformers process all tokens in parallel using multi-head self-attention mechanisms.\nBPE tokenization splits words into sub-word tokens; models compute probabilities over tokens, not whole words.\nTemperature scales logit distribution: lower values (0.1) yield deterministic output; higher values (0.8) increase diversity.',
                             'Confusing token counts with character or word counts (1,000 words ~ 1,333 tokens).\nSetting high temperature for structured JSON extraction tasks where determinism is critical.'),
                            (2, 'Prompt Patterns', 'Advanced Prompt Engineering: Few-Shot, CoT & System Instructions', 30, 'b_xURk9jZ84',
                             '<h3>Advanced Prompt Engineering Patterns</h3><p>Structure professional prompt templates. Compare Zero-Shot, Few-Shot exemplars, and Chain-of-Thought (CoT) reasoning to force models to show intermediate logic steps.</p>',
                             'Few-shot prompt exemplars anchor output format, stylistic tone, and edge-case handling.\nChain-of-Thought ("Think step-by-step") dramatically reduces reasoning errors in arithmetic and logic.\nUse role-prompting and clear markdown delimiters (###, XML tags) to isolate untrusted user inputs.',
                             'Using vague, conversational requests without specifying expected output schemas.\nAllowing raw user inputs to concatenate into prompts without delimiters, opening prompt injection vulnerabilities.'),
                            (3, 'Structured Outputs', 'Structured Outputs & Enforcing JSON Schemas with LLMs', 25, 'PqFKRqpHrjw',
                             '<h3>Structured Outputs & Enforcing JSON Schemas</h3><p>Extract clean, machine-parseable data from unstructured text. Use OpenAI/Anthropic/Gemini JSON mode, Pydantic validation, and constrained decoding grammars.</p>',
                             'Constrained decoding forces LLM token sampling to strictly adhere to Pydantic JSON schemas.\nAlways validate LLM outputs using schema parsers before feeding data into database queries.\nInclude retry mechanisms with feedback loops when schema validation fails.',
                             'Relying on regex to parse freeform text when native JSON schema mode guarantees valid syntax.\nFailing to handle JSON truncation when context window or token limits are exceeded.'),
                            (4, 'API Integrations', 'Calling LLM APIs: Streaming, Rate Limiting & Error Handling', 25, 'kqtD5dpn9C8',
                             '<h3>Calling LLM APIs at Scale</h3><p>Integrate frontier LLM APIs (OpenAI, Anthropic, Gemini). Implement Server-Sent Events (SSE) token streaming for responsive UX, exponential backoff retries, and token budgeting.</p>',
                             'Streaming tokens via SSE dramatically reduces Perceived Time to First Token (TTFT) from 5s to 200ms.\nImplement exponential backoff with jitter to handle HTTP 429 rate limit errors gracefully.\nTrack prompt and completion token counts per user to maintain cost governance.',
                             'Blocking web server request threads while waiting for long completion generations.\nHardcoding secret API keys in client-side frontend code.'),
                        ]
                    },
                    {
                        'order': 2,
                        'title': 'Module 2: Embeddings & Vector Databases',
                        'description': 'Master vector embeddings, similarity search mathematics, and ChromaDB vector stores.',
                        'lessons': [
                            (5, 'Embeddings Theory', 'Vector Embeddings & Semantic Similarity Search Math', 25, 'wjZofJX0v4U',
                             '<h3>Vector Embeddings & Semantic Similarity</h3><p>Understand how neural networks project words and documents into high-dimensional vector spaces. Calculate cosine similarity, Euclidean distance, and dot product metrics.</p>',
                             'Embedding models map semantic meaning into dense high-dimensional vectors (e.g., 1536 dimensions).\nCosine similarity measures the angle between vectors, normalizing for document length variations.\nSemantic search finds conceptual matches even when query and document share zero exact keywords.',
                             'Comparing embeddings generated from two different embedding models.\nUsing Euclidean distance on unnormalized embedding vectors.'),
                            (6, 'Vector Databases', 'Implementing Vector Stores with ChromaDB & FAISS', 30, 'L_Guz73e6fw',
                             '<h3>Vector Stores with ChromaDB & FAISS</h3><p>Store, index, and query millions of vectors efficiently. Compare Approximate Nearest Neighbor (ANN) index algorithms: HNSW (Hierarchical Navigable Small World) versus IVF (Inverted File).</p>',
                             'Vector databases store embedding vectors alongside rich metadata for hybrid filtering.\nHNSW indexes offer logarithmic search time by creating multi-layer skip-list graph structures.\nPersist vector collections locally with ChromaDB or in memory with Facebook FAISS.',
                             'Performing brute-force k-NN linear searches on millions of vectors instead of using indexed ANN.\nFailing to persist vector index collections across server restarts.'),
                            (7, 'Document Chunking', 'Document Chunking Strategies & Overlap Optimization', 25, '1vR3W4666RQ',
                             '<h3>Document Chunking Strategies</h3><p>Break large PDF, Markdown, and HTML documents into semantic pieces. Compare fixed-character chunking, recursive character chunking, sentence splitting, and semantic boundary detection.</p>',
                             'Chunk size represents a trade-off: large chunks provide broader context but dilute specific embeddings.\nChunk overlap (10-20%) preserves boundary sentences that would otherwise be severed across chunks.\nRecursive character splitting preserves natural paragraph and markdown heading hierarchies.',
                             'Using huge 2,000-token chunks that bury the specific answer in irrelevant noise.\nZero overlap between chunks, creating information loss at split boundaries.'),
                            (8, 'Hybrid Search', 'Hybrid Search: Combining BM25 Keyword Search with Dense Vectors', 25, 'aywZrzNaKjs',
                             '<h3>Hybrid Search: BM25 + Dense Vectors</h3><p>Overcome the limitations of pure vector search. Combine sparse keyword matching (BM25) for exact product IDs and acronyms with dense vector embeddings for semantic context using Reciprocal Rank Fusion (RRF).</p>',
                             'Dense vectors excel at semantic meaning but fail on exact part numbers, acronyms, and names.\nBM25 keyword search guarantees exact lexical matches.\nReciprocal Rank Fusion (RRF) scores and merges ranked lists from both systems into an optimal result set.',
                             'Relying solely on vector search for queries containing specialized technical part codes.\nNormalizing disparate search scores with naive addition instead of rank-based fusion (RRF).'),
                        ]
                    },
                    {
                        'order': 3,
                        'title': 'Module 3: Production Retrieval-Augmented Generation (RAG)',
                        'description': 'Architect end-to-end RAG pipelines with re-ranking, query transformation, and evaluation.',
                        'lessons': [
                            (9, 'RAG Architecture', 'Building an End-to-End RAG Pipeline with LangChain', 30, 'aywZrzNaKjs',
                             '<h3>End-to-End RAG Architecture</h3><p>Construct production RAG pipelines: query embedding, vector retrieval, prompt grounding, context injection, and synthesis generation. Prevent common RAG pitfalls.</p>',
                             'RAG grounds LLM generation in authoritative external documentation, eliminating knowledge cutoffs.\nAlways cite source documents and page numbers in retrieved context.\nInstruct models explicitly: "Answer based only on the provided context; if unsure, state that the context is insufficient."',
                             'Allowing the LLM to hallucinate answers when retrieved documents contain no relevant information.\nStuffing dozens of irrelevant retrieved documents into the context window, causing needle-in-a-haystack lost-in-the-middle issues.'),
                            (10, 'Advanced Retrieval', 'Query Expansion, Multi-Query & HyDE (Hypothetical Embeddings)', 30, '1vR3W4666RQ',
                             '<h3>Advanced Retrieval Techniques</h3><p>Enhance retrieval recall. Generate multiple sub-queries with LLM query expansion, generate hypothetical documents with HyDE, and resolve multi-turn conversational coreferences.</p>',
                             'Users frequently ask underspecified or colloquial queries that mismatch document terminology.\nHyDE prompts the LLM to generate a hypothetical answer first, then embeds that answer for retrieval.\nMulti-query expansion generates 3-5 variations of a query to maximize retrieval recall.',
                             'Embedding raw conversational user follow-up questions ("What about the second one?") without resolving prior chat context.\nUsing computationally expensive HyDE for simple factual queries where latency is critical.'),
                            (11, 'Re-Ranking', 'Context Re-ranking with Cross-Encoder Models (Cohere/BGE)', 25, 'ZDa-Z5JzLYM',
                             '<h3>Context Re-ranking with Cross-Encoders</h3><p>Apply two-stage retrieval. Retrieve top 50 candidates rapidly with bi-encoder vector search, then re-rank top 5 candidates with a computationally intensive cross-encoder model.</p>',
                             'Bi-encoders embed query and document independently (fast, lower precision).\nCross-encoders feed query and document simultaneously through attention layers (slower, maximum precision).\nRe-ranking ensures only the highest-relevance context chunks occupy precious prompt tokens.',
                             'Feeding all 50 retrieved chunks directly into the LLM without re-ranking.\nUsing cross-encoders for the initial search across millions of documents (which would be impractically slow).'),
                            (12, 'RAG Evaluation', 'Systematic RAG Evaluation with RAGAS Metrics', 25, '8ext9G7xspg',
                             '<h3>Systematic RAG Evaluation with RAGAS</h3><p>Quantify RAG quality without manual human inspection. Measure Faithfulness (hallucination detection), Answer Relevance, Context Precision, and Context Recall using automated LLM-as-a-judge pipelines.</p>',
                             'Faithfulness measures whether the generated answer is strictly derived from retrieved context.\nContext Recall measures whether all information needed to answer the question was successfully retrieved.\nTrack quantitative benchmark scores over time across every prompt or pipeline iteration.',
                             'Deploying RAG pipelines to production based purely on subjective "vibe checks".\nOptimizing for high answer relevance while ignoring low faithfulness (hallucinations).'),
                        ]
                    },
                    {
                        'order': 4,
                        'title': 'Module 4: Autonomous AI Agents & Production Deployment',
                        'description': 'Build multi-tool AI agents, deploy safety guardrails, and optimize production costs.',
                        'lessons': [
                            (13, 'Tool-Calling Agents', 'Building Autonomous AI Agents with Function Calling', 30, 'rfscVS0vtbw',
                             '<h3>Building Tool-Calling AI Agents</h3><p>Empower LLMs to take actions in the real world. Define JSON tool schemas for SQL databases, web search, and external APIs. Execute tool calls iteratively with the ReAct framework.</p>',
                             'LLMs do not execute code themselves; they generate structured tool invocation arguments.\nThe agent loop: Think -> Call Tool -> Observe Output -> Decide Next Step -> Final Answer.\nAlways validate and sandbox tool execution environments to prevent dangerous actions.',
                             'Granting AI agents unrestricted write/delete permissions on production databases without human-in-the-loop confirmation.\nFailing to limit maximum agent iteration loops, causing infinite loops that consume thousands of dollars in API credits.'),
                            (14, 'Multi-Agent Systems', 'Multi-Agent Orchestration & Workflow Memory', 30, 'daefaLgNkw0',
                             '<h3>Multi-Agent Orchestration & Memory</h3><p>Decompose complex tasks into specialized collaborative agents (Researcher, Coder, Critic). Implement short-term working memory and long-term episodic memory.</p>',
                             'Specialized agents with narrow system prompts outperform single monolithic prompts on complex tasks.\nA critic/supervisor agent reviews and refines work produced by worker agents before presentation.\nEpisodic memory stores key user preferences and past session summaries in vector databases.',
                             'Creating overly complex multi-agent graphs for simple tasks that a single prompt could solve in seconds.\nUnconstrained agent-to-agent chatter loops that amplify hallucinations.'),
                            (15, 'Cost & Safety Guardrails', 'GenAI Cost Optimization, Latency & Security Guardrails', 25, '8DvywoWv6fI',
                             '<h3>Cost Optimization, Latency & Guardrails</h3><p>Optimize operational unit economics. Implement prompt caching, semantic embedding caching, smaller distilled models (GPT-4o-mini, Claude Haiku), and NeMo Guardrails to prevent prompt injections.</p>',
                             'Prompt caching reduces token costs by up to 80% on repetitive system prompts.\nRoute simple requests to fast, inexpensive models; escalate complex reasoning to frontier models.\nGuardrails detect jailbreaks, prompt injections, and PII leakage before data reaches the model.',
                             'Sending full document context on every turn without utilizing vendor prompt caching.\nFailing to sanitize user inputs against indirect prompt injection embedded inside third-party websites or PDFs.'),
                            (16, 'Capstone Project', 'Capstone Project: Enterprise Multimodal Customer Intelligence Agent', 35, '0pd36apRe34',
                             '<h3>Capstone Project: Enterprise Customer Intelligence Agent</h3><p>Build and deploy an enterprise-grade autonomous customer intelligence agent. Integrates hybrid RAG across documentation, SQL database querying via function calling, semantic caching, and real-time streaming.</p>',
                             'A production GenAI system harmonizes vector retrieval, structured DB access, safety guardrails, and streaming UX.\nImplement automated trace logging (LangSmith, OpenTelemetry) for every LLM call.\nDeliver a comprehensive deployment with Docker, environment variables, and integration tests.',
                             'Failing to implement fallback responses when external LLM APIs experience downtime.\nNeglecting to monitor token latency and cost metrics in production.')
                        ]
                    }
                ],
                'quiz': {
                    'title': 'Applied Generative AI & Prompt Engineering Final Quiz',
                    'questions': [
                        ('What is the core mathematical mechanism behind Transformer models that allows them to process all tokens in parallel?',
                         'Recurrent hidden state loops',
                         'Multi-Head Self-Attention mechanisms',
                         'Convolutional kernel filters',
                         'Markov decision chains', 'B',
                         'Unlike RNNs which process tokens sequentially, Transformers use Multi-Head Self-Attention to compute relationships between all tokens simultaneously in parallel.'),
                        ('In the context of Prompt Engineering, what is the Chain-of-Thought (CoT) prompting technique?',
                         'Chaining multiple API calls together in a bash script',
                         'Instructing the model to show intermediate reasoning steps before providing the final answer',
                         'Concatenating 50 different prompts into one gigantic string',
                         'Repeating the user question three times', 'B',
                         'Chain-of-Thought prompting encourages the model to break complex reasoning into intermediate steps ("Let\'s think step by step"), significantly improving accuracy on logic and mathematical tasks.'),
                        ('Why is hybrid search (BM25 + Dense Vectors) superior to pure vector search alone in enterprise RAG?',
                         'Hybrid search requires no embedding models',
                         'Dense vectors capture semantic meaning, while BM25 guarantees exact keyword matching for specific product codes, names, and acronyms',
                         'BM25 is faster than vector search in every scenario',
                         'Dense vectors cannot store text', 'B',
                         'Vector embeddings excel at semantic similarity but frequently fail when searching for exact alphanumeric codes, SKU numbers, or rare acronyms where BM25 keyword matching is essential.'),
                        ('In RAG evaluation with RAGAS, what does the "Faithfulness" metric measure?',
                         'How quickly the LLM generates tokens',
                         'Whether the generated claims can be inferred directly from the retrieved context without hallucination',
                         'How polite the AI is to the user',
                         'The number of tokens in the prompt', 'B',
                         'Faithfulness measures factual consistency: it computes the proportion of claims in the generated response that are directly grounded in and supported by the retrieved context chunks.'),
                        ('What role does an AI Agent\'s tool definition play during LLM execution?',
                         'The LLM directly executes the tool\'s Python code inside its weights',
                         'The LLM receives tool schemas in JSON and generates structured tool arguments when it decides a tool is needed',
                         'The tool compiles the LLM into binary machine code',
                         'Tools are only used to format the final markdown text', 'B',
                         'LLMs do not run code themselves; they are language engines. When equipped with tools, they decide when to call a tool and output valid JSON parameters, which the application executes before returning results to the LLM.')
                    ]
                }
            },

            # -----------------------------------------------------------------
            # COURSE 6: AI - Computer Vision & Deep Learning with PyTorch
            # -----------------------------------------------------------------
            {
                'title': 'Computer Vision & Deep Learning with PyTorch',
                'slug': 'computer-vision-pytorch',
                'category_slug': 'artificial-intelligence',
                'difficulty': 'Intermediate',
                'instructor_name': 'Rachel Vance',
                'instructor_title': 'Lead Deep Learning & Perception Engineer',
                'estimated_duration': '16 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1507146426996-ef05306b995a?auto=format&fit=crop&w=800&q=80',
                'short_description': 'Master modern computer vision: convolutional networks, transfer learning, YOLO object detection, segmentation, and vision transformers.',
                'description': 'Dive into the visual perception technologies powering autonomous vehicles, medical imaging, and robotics. Learn to train, evaluate, and optimize deep neural networks using PyTorch. Master tensor operations and Autograd backpropagation, build custom Convolutional Neural Networks (CNNs), utilize transfer learning with modern backbones (ResNet, EfficientNet), implement data augmentation pipelines (Albumentations), detect objects with YOLO architectures, segment images with Mask R-CNN, visualize feature activations with Grad-CAM, and explore cutting-edge Vision Transformers (ViTs).',
                'learning_objectives': "Master PyTorch tensors, automatic differentiation (Autograd), and GPU acceleration (CUDA/MPS)\nBuild and train custom Convolutional Neural Networks (CNNs) from scratch\nFine-tune pre-trained models with transfer learning and adaptive learning rate schedulers\nImplement high-performance image augmentation pipelines with Albumentations\nTrain and deploy real-time object detection models using modern YOLO architectures\nVisualize model decisions and explainability using Grad-CAM heatmaps",
                'prerequisites': "Proficiency with Python programming and object-oriented principles\nUnderstanding of multi-dimensional arrays (NumPy)\nBasic knowledge of calculus (partial derivatives, gradients) and linear algebra",
                'modules': [
                    {
                        'order': 1,
                        'title': 'Module 1: PyTorch Foundations & Neural Network Core',
                        'description': 'Master PyTorch tensors, computational graphs, Autograd, and modular training loops.',
                        'lessons': [
                            (1, 'PyTorch Tensors', 'PyTorch Tensors, CUDA/MPS Hardware Acceleration & Autograd', 25, 'tPYj3fF55Mo',
                             '<h3>PyTorch Tensors & Autograd</h3><p>Explore PyTorch tensor manipulation, broadcasting, memory layouts (strides), device management (CPU/CUDA/MPS), and reverse-mode automatic differentiation with torch.autograd.</p>',
                             'PyTorch tensors are multidimensional arrays that execute on GPUs and record computational operation graphs.\nSetting requires_grad=True tracks operations for automatic backpropagation gradient calculation.\nAlways call loss.backward() followed by optimizer.step() and optimizer.zero_grad().',
                             'Forgetting to call optimizer.zero_grad(), causing gradients to accumulate across training batches.\nLeaving tensors on the CPU when calling models deployed to GPU device memory.'),
                            (2, 'Training Loops', 'Custom Dataset Loaders, Loss Functions & Optimizers', 30, 'V_xro1bcAuA',
                             '<h3>Custom Dataset Loaders & Training Loops</h3><p>Construct modular training pipelines. Subclass torch.utils.data.Dataset and DataLoader with multi-worker pre-fetching. Compare SGD with momentum versus AdamW optimizers.</p>',
                             'Subclass torch.utils.data.Dataset by implementing __len__ and __getitem__ methods.\nUse pin_memory=True and num_workers > 0 in DataLoaders to maximize GPU utilization.\nAdamW decouples weight decay from gradient updates, stabilizing training convergence.',
                             'Performing heavy I/O operations inside the training step instead of within DataLoader worker threads.\nNeglecting to switch models between model.train() and model.eval() modes during validation.'),
                            (3, 'CNN Foundations', 'Convolutional Layers, Pooling & Feature Map Arithmetic', 25, 'grG44GphzJ8',
                             '<h3>Convolutional Layers & Feature Maps</h3><p>Understand how 2D convolutions extract spatial hierarchies. Calculate feature map output dimensions given input size, kernel size, stride, and padding.</p>',
                             'Convolution formula: Output Size = ((Input - Kernel + 2*Padding) / Stride) + 1.\nConvolutional filters share weights across spatial positions (translation equivariance).\nPooling layers reduce spatial resolution while preserving dominant feature activations.',
                             'Confusing the channel dimension with batch or spatial dimensions (PyTorch expects BCHW format).\nCausing negative dimension errors by applying too many downsampling pooling layers.'),
                            (4, 'Data Augmentation', 'Data Augmentation Pipelines with Albumentations', 25, 'DHvZLI7Db8E',
                             '<h3>Data Augmentation with Albumentations</h3><p>Prevent model overfitting on visual datasets. Apply affine transformations, random crops, color jittering, Gaussian blur, and CutMix/MixUp augmentations.</p>',
                             'Data augmentation artificially expands dataset diversity, reducing overfitting on limited training images.\nAlbumentations executes rapid image and bounding-box augmentations simultaneously.\nApply augmentations strictly to the training split, never to validation or test splits.',
                             'Applying destructive augmentations that obscure critical diagnostic features (e.g., extreme rotation on digits).\nAugmenting validation or test images, corrupting objective evaluation metrics.'),
                        ]
                    },
                    {
                        'order': 2,
                        'title': 'Module 2: Transfer Learning & Model Architectures',
                        'description': 'Leverage pre-trained image backbones and fine-tune deep vision models.',
                        'lessons': [
                            (5, 'Transfer Learning', 'Transfer Learning Principles & Feature Extraction', 30, 'mEsleV16qdo',
                             '<h3>Transfer Learning with Pre-trained Models</h3><p>Harness representations learned on ImageNet. Compare feature extraction (freezing base layers) with full fine-tuning. Replace classification head linear layers.</p>',
                             'Early convolutional layers learn universal visual primitives (edges, textures, color gradients).\nHigher layers learn domain-specific semantic concepts.\nFreeze backbone weights initially; fine-tune with a low learning rate once the new head stabilizes.',
                             'Training deep vision models from scratch with small custom datasets when pre-trained weights exist.\nUsing an aggressive learning rate on pre-trained backbones, destroying valuable learned weights.'),
                            (6, 'Modern Backbones', 'Modern Vision Architectures: ResNet, DenseNet & EfficientNet', 25, 'aircAruvnKk',
                             '<h3>Modern Vision Architectures: ResNet & EfficientNet</h3><p>Deconstruct revolutionary vision architectures. Understand residual skip connections that conquer vanishing gradients in ResNet, and compound scaling in EfficientNet.</p>',
                             'Residual skip connections (y = F(x) + x) allow gradients to flow unimpeded through hundreds of layers.\nCompound scaling scales network depth, width, and image resolution simultaneously.\nBatch Normalization accelerates training convergence and provides mild regularization.',
                             'Removing skip connections, reintroducing the degradation and vanishing gradient problem.\nScaling image input resolution without proportionally increasing model depth.'),
                            (7, 'Explainability', 'Model Explainability: Grad-CAM & Feature Visualization', 25, '8ext9G7xspg',
                             '<h3>Model Explainability with Grad-CAM</h3><p>Inspect what deep networks actually look at. Compute Gradient-weighted Class Activation Mapping (Grad-CAM) to generate visual heatmaps explaining classification decisions.</p>',
                             'Grad-CAM calculates gradients of the target class score with respect to the final convolutional feature maps.\nHeatmaps highlight the specific image regions responsible for model predictions.\nCritical for clinical medical imaging, autonomous navigation, and bias auditing.',
                             'Deploying black-box computer vision models into safety-critical environments without explainability auditing.\nComputing Grad-CAM on early convolutional layers which lack high-level semantic meaning.'),
                            (8, 'Optimization & Schedulers', 'Learning Rate Schedulers, Mixed Precision & Regularization', 25, 'kqtD5dpn9C8',
                             '<h3>Optimization & Mixed Precision Training</h3><p>Accelerate training and improve generalization. Implement Cosine Annealing learning rate schedules, torch.cuda.amp Automatic Mixed Precision (AMP), and label smoothing.</p>',
                             'Automatic Mixed Precision (FP16/BF16) cuts GPU memory usage in half and accelerates compute up to 3x.\nCosine Annealing schedules smoothly decay the learning rate to escape poor local minima.\nLabel smoothing prevents models from becoming overly confident in incorrect predictions.',
                             'Using mixed precision without gradient scaling, leading to numerical underflow in small gradients.\nKeeping learning rates constant throughout the entire training process.'),
                        ]
                    },
                    {
                        'order': 3,
                        'title': 'Module 3: Object Detection & Segmentation',
                        'description': 'Detect multi-class bounding boxes with YOLO and segment images at the pixel level.',
                        'lessons': [
                            (9, 'Object Detection Core', 'Object Detection Principles: Anchors, IoU & mAP Evaluation', 30, 'wjZofJX0v4U',
                             '<h3>Object Detection Foundations</h3><p>Understand bounding box regression, Intersection over Union (IoU), Non-Maximum Suppression (NMS), anchor boxes, and mean Average Precision (mAP@50, mAP@50:95) metrics.</p>',
                             'Intersection over Union (IoU) measures overlap area divided by union area of bounding boxes.\nNon-Maximum Suppression (NMS) eliminates duplicate overlapping bounding boxes for the same object.\nMean Average Precision (mAP) integrates precision-recall curves across multiple IoU thresholds.',
                             'Confusing object classification accuracy with object detection localization mAP.\nSetting NMS IoU thresholds too high, failing to remove duplicate overlapping predictions.'),
                            (10, 'YOLO Architectures', 'Real-Time Object Detection with YOLO', 35, '1vR3W4666RQ',
                             '<h3>Real-Time Object Detection with YOLO</h3><p>Train state-of-the-art single-stage detectors. Structure custom datasets in YOLO format, configure loss functions (CIoU loss, focal loss), and deploy real-time inference on video streams.</p>',
                             'Single-stage detectors (YOLO) predict bounding boxes and class probabilities simultaneously in one pass.\nModern YOLO versions achieve over 60 FPS on edge hardware while maintaining high mAP.\nCIoU loss incorporates overlap area, aspect ratio consistency, and center point distance.',
                             'Training YOLO models with mismatched image sizes that distort bounding box coordinates.\nOverlooking class imbalance in datasets where one object class dominates.'),
                            (11, 'Image Segmentation', 'Semantic & Instance Segmentation: U-Net & Mask R-CNN', 30, '1vR3W4666RQ',
                             '<h3>Image Segmentation: U-Net & Mask R-CNN</h3><p>Classify every pixel in an image. Implement U-Net encoder-decoder architectures with skip connections for medical segmentation, and Mask R-CNN for instance segmentation.</p>',
                             'Semantic segmentation assigns every pixel a class label without distinguishing individual object instances.\nInstance segmentation (Mask R-CNN) detects individual objects and generates a distinct binary mask for each.\nU-Net skip connections recover fine spatial details lost during encoder downsampling.',
                             'Using standard cross-entropy loss on segmentation tasks with severe background class imbalance.\nAttempting instance segmentation with pure semantic segmentation models.'),
                            (12, 'Vision Transformers', 'Vision Transformers (ViT) & Multimodal Vision Models', 30, 'rfscVS0vtbw',
                             '<h3>Vision Transformers (ViT) & Multimodal Models</h3><p>Apply Transformer self-attention directly to computer vision. Break images into 16x16 flattened patches, apply positional embeddings, and explore multimodal models (CLIP).</p>',
                             'Vision Transformers (ViT) treat 16x16 pixel patches as "tokens" in a standard transformer encoder.\nViTs lack CNN inductive bias (translation equivariance), requiring massive datasets or pre-training to excel.\nCLIP bridges vision and language by training image and text encoders with contrastive loss.',
                             'Training Vision Transformers from scratch on tiny datasets without pre-training.\nDiscarding spatial positional embeddings, destroying the model\'s awareness of image geometry.'),
                        ]
                    },
                    {
                        'order': 4,
                        'title': 'Module 4: Video Processing & Production Deployment',
                        'description': 'Process video streams, track objects across frames, and export models with ONNX.',
                        'lessons': [
                            (13, 'Video Analysis', 'Video Processing & Real-Time Webcam Pipelines', 25, 'PqFKRqpHrjw',
                             '<h3>Video Processing & OpenCV Pipelines</h3><p>Read, process, and render video streams with OpenCV. Calculate optical flow for motion estimation, manage frame buffers, and maintain real-time FPS throughput.</p>',
                             'Process video frames asynchronously in dedicated worker threads to decouple I/O from model inference.\nLucas-Kanade optical flow tracks feature point motion vectors across consecutive frames.\nMaintain frame queues to prevent memory leaks during video processing bottlenecks.',
                             'Reading video frames sequentially on the main UI thread, causing lag and stuttering.\nAllocating new memory buffers for every incoming video frame.'),
                            (14, 'Multi-Object Tracking', 'Multi-Object Tracking: DeepSORT & ByteTrack', 30, '0pd36apRe34',
                             '<h3>Multi-Object Tracking: DeepSORT & ByteTrack</h3><p>Maintain consistent object identities across video frames. Combine Kalman filter motion prediction with Hungarian matching and deep visual appearance embeddings.</p>',
                             'Kalman filters predict future bounding box positions based on prior velocity vectors.\nHungarian algorithm performs optimal bipartite matching between detections and existing tracks.\nByteTrack associates low-score detection boxes to maintain tracks through partial occlusions.',
                             'Relying solely on visual appearance embeddings when lighting changes dramatically.\nCreating new identity IDs every time an object is briefly occluded behind an obstacle.'),
                            (15, 'Model Export & Edge', 'Production Model Export: ONNX, TensorRT & Quantization', 25, 'daefaLgNkw0',
                             '<h3>Production Model Export with ONNX & TensorRT</h3><p>Bridge the gap from PyTorch research to edge production. Export models to Open Neural Network Exchange (ONNX) format, apply INT8 post-training quantization, and optimize inference with TensorRT.</p>',
                             'ONNX decouples trained models from the PyTorch runtime for deployment in C++, Rust, or mobile.\nTensorRT fuses layers and optimizes kernel selection for NVIDIA GPU hardware.\nINT8 quantization reduces model size by 4x and boosts throughput with negligible loss in accuracy.',
                             'Exporting models with fixed batch sizes when production requires dynamic batching.\nDeploying full FP32 PyTorch models to resource-constrained edge devices.'),
                            (16, 'Capstone Project', 'Capstone Project: Autonomous Retail Checkout Vision System', 35, '0pd36apRe34',
                             '<h3>Capstone Project: Autonomous Retail Checkout Perception System</h3><p>Build a production multi-camera retail vision system. Combines real-time YOLO object detection for inventory items, DeepSORT tracking across checkout lanes, and ONNX runtime inference.</p>',
                             'A production vision system integrates hardware camera feeds, fast detection, stable tracking, and structured reporting.\nValidate detection precision under varied illumination and overlapping package conditions.\nDeliver clean, modular code with automated evaluation benchmarks and edge deployment instructions.',
                             'Testing the system only on clean single-item images rather than cluttered retail checkout baskets.\nNeglecting model latency benchmarks under high-concurrency multi-camera loads.')
                        ]
                    }
                ],
                'quiz': {
                    'title': 'Computer Vision & Deep Learning with PyTorch Final Quiz',
                    'questions': [
                        ('Why is it mandatory to call optimizer.zero_grad() before loss.backward() in a PyTorch training loop?',
                         'To clear model weights to zero',
                         'Because PyTorch accumulates gradients by default; without clearing, gradients from previous batches add together',
                         'To reset the GPU memory buffer',
                         'To set the learning rate to zero', 'B',
                         'In PyTorch, gradients accumulate on tensor .grad attributes with every backward() call. Calling optimizer.zero_grad() resets these to zero before computing fresh gradients for the current batch.'),
                        ('What is the formula for the spatial output dimension of a 2D convolutional layer with input size W, kernel size K, padding P, and stride S?',
                         '((W - K + 2*P) / S) + 1',
                         '(W * K) + P - S',
                         '(W + K + P) / S',
                         'W - K + P', 'A',
                         'The standard spatial dimension formula is: Output = ((Input - Kernel + 2*Padding) / Stride) + 1.'),
                        ('What architectural breakthrough enabled ResNet to train neural networks over 100 layers deep without suffering from vanishing gradients?',
                         'Dropout layers',
                         'Residual skip connections (identity shortcut connections)',
                         'Max pooling layers',
                         'Sigmoid activation functions', 'B',
                         'Residual skip connections allow the gradient signal to flow directly through identity shortcuts without diminishing, solving the vanishing gradient and degradation problems in very deep networks.'),
                        ('In object detection evaluation, what does Mean Average Precision (mAP) measure?',
                         'The percentage of pixels correctly classified as background',
                         'The area under the Precision-Recall curve averaged across object classes at specified IoU thresholds',
                         'The inference speed of the model in milliseconds',
                         'The memory size of the model on disk', 'B',
                         'mAP (Mean Average Precision) measures both classification accuracy and localization precision by calculating the area under the precision-recall curve across multiple IoU thresholds (e.g., mAP@0.50:0.95).'),
                        ('How does a Vision Transformer (ViT) ingest a continuous 2D image into its standard Transformer encoder?',
                         'By converting the image into audio spectrograms',
                         'By flattening 2D image patches (e.g., 16x16 pixels) into 1D token vectors and adding positional embeddings',
                         'By using standard convolutional filters with 1x1 stride',
                         'By averaging all pixels in the image into a single scalar value', 'B',
                         'Vision Transformers split an image into a grid of non-overlapping patches (e.g., 16x16), linearly project each patch into an embedding vector, prepend a class token, add learnable 1D position embeddings, and pass the sequence to a standard Transformer encoder.')
                    ]
                }
            },

            # -----------------------------------------------------------------
            # COURSE 7: Cloud - Cloud Architecture & DevOps with AWS & Docker
            # -----------------------------------------------------------------
            {
                'title': 'Cloud Architecture & DevOps with AWS & Docker',
                'slug': 'cloud-architecture-devops-aws',
                'category_slug': 'cloud-devops',
                'difficulty': 'Beginner',
                'instructor_name': 'Marcus Brody',
                'instructor_title': 'Principal Cloud Architect & DevOps Lead',
                'estimated_duration': '15 hours',
                'thumbnail_url': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80',
                'short_description': 'Deploy scalable infrastructure using AWS services, Docker containers, GitHub Actions CI/CD pipelines, and Terraform IaC.',
                'description': 'Master the cloud engineering and DevOps foundations that underpin modern software infrastructure. Move from running code solely on localhost to deploying resilient, highly available production systems on Amazon Web Services (AWS). Learn core cloud networking (VPC, Subnets, Route Tables, Security Groups), compute (EC2, Auto Scaling, ALB, Lambda), storage (S3, EBS), relational databases (RDS PostgreSQL), containerization with Docker and multi-container Docker Compose, automated CI/CD pipelines with GitHub Actions, Infrastructure as Code with Terraform, and cloud monitoring with CloudWatch.',
                'learning_objectives': "Design secure, highly available cloud VPC networks with public and private subnets on AWS\nProvision and configure virtual servers (EC2), auto-scaling groups, and load balancers (ALB)\nContainerize multi-tier web applications using production Dockerfiles and multi-stage builds\nOrchestrate multi-container environments locally and in the cloud with Docker Compose\nAutomate continuous integration and continuous deployment (CI/CD) pipelines with GitHub Actions\nManage cloud infrastructure deterministically using Terraform Infrastructure as Code (IaC)",
                'prerequisites': "Basic understanding of the Linux terminal and bash commands\nFamiliarity with web application architectures (client-server, databases)\nNo prior cloud or DevOps experience required",
                'modules': [
                    {
                        'order': 1,
                        'title': 'Module 1: Cloud Principles & Core AWS Networking',
                        'description': 'Master cloud computing fundamentals, AWS global infrastructure, and custom VPC networking.',
                        'lessons': [
                            (1, 'Cloud Principles', 'Cloud Computing Models & AWS Global Infrastructure', 25, 'ulprqHHWlng',
                             '<h3>Cloud Computing & AWS Global Infrastructure</h3><p>Compare On-Premises, IaaS, PaaS, and SaaS models. Explore AWS Regions, Availability Zones (AZs), edge locations, and the Shared Responsibility Model for cloud security.</p>',
                             'AWS Regions consist of multiple geographically isolated Availability Zones connected by low-latency fiber.\nShared Responsibility Model: AWS secures the cloud (hardware, data centers); the customer secures in the cloud (data, OS, firewall rules).\nHigh availability requires distributing workloads across at least two distinct Availability Zones.',
                             'Deploying production workloads to a single Availability Zone, leaving the application vulnerable to localized outages.\nAssuming AWS automatically backups or encrypts customer database data without explicit configuration.'),
                            (2, 'VPC Architecture', 'VPC Networking: Subnets, Route Tables & Internet Gateways', 30, 'wjZofJX0v4U',
                             '<h3>VPC Architecture & Subnet Isolation</h3><p>Architect isolated Virtual Private Clouds (VPCs). Configure Classless Inter-Domain Routing (CIDR) blocks, public subnets with Internet Gateways, and private subnets with NAT Gateways.</p>',
                             'Public subnets have direct routes to an Internet Gateway for user-facing load balancers.\nPrivate subnets route outbound traffic through NAT Gateways, preventing direct inbound internet access to databases.\nSecurity Groups operate as stateful instance-level firewalls; Network ACLs operate as stateless subnet boundaries.',
                             'Placing production databases in public subnets with direct internet access.\nConfusing stateful Security Groups (return traffic automatically allowed) with stateless NACLs.'),
                            (3, 'Compute: EC2', 'Compute Infrastructure: Amazon EC2 & Auto Scaling Groups', 25, 'wjZofJX0v4U',
                             '<h3>Amazon EC2 & Elastic Scaling</h3><p>Provision and configure virtual compute instances. Master Amazon Machine Images (AMIs), instance sizing, SSH key pair access, launch templates, and Auto Scaling Groups (ASG).</p>',
                             'EC2 provides resizable compute capacity; select instance types optimized for compute, memory, or storage.\nAuto Scaling Groups automatically adjust instance count in response to CPU load or traffic spikes.\nAttach Application Load Balancers (ALBs) to distribute incoming traffic evenly across healthy target instances.',
                             'Storing persistent application state or user uploads directly on ephemeral EC2 root volumes.\nManaging EC2 instances manually instead of defining launch templates and auto-scaling policies.'),
                            (4, 'Storage & Databases', 'Storage & Databases: S3, EBS & Amazon RDS PostgreSQL', 25, '1vR3W4666RQ',
                             '<h3>Cloud Storage & Managed Databases</h3><p>Compare object storage (Amazon S3), block storage (EBS), and managed relational databases (Amazon RDS). Configure S3 bucket policies, versioning, and RDS Multi-AZ failover.</p>',
                             'Amazon S3 provides 99.999999999% (11 9s) of data durability for object storage.\nAmazon RDS automates software patching, point-in-time backups, and synchronous Multi-AZ failover.\nUse IAM roles rather than permanent access keys to grant EC2 instances permissions to access S3 buckets.',
                             'Leaving S3 buckets publicly readable without bucket policy restrictions.\nRunning self-managed databases on EC2 without automated backups when RDS handles failover automatically.')
                        ]
                    },
                    {
                        'order': 2,
                        'title': 'Module 2: Containerization with Docker & Multi-Stage Builds',
                        'description': 'Master Docker containers, images, multi-stage builds, and container networking.',
                        'lessons': [
                            (5, 'Docker Core', 'Containerization Principles: Containers vs Virtual Machines', 25, 'fqMOX6JJhGo',
                             '<h3>Containers vs Virtual Machines</h3><p>Understand OS-level virtualization. Explore Linux namespaces, cgroups, UnionFS, and discover why Docker containers are lightweight, fast, and eliminate "it works on my machine" issues.</p>',
                             'Virtual machines virtualize hardware with full guest operating systems; containers share the host Linux kernel.\nNamespaces isolate processes, networks, and mount points; cgroups constrain CPU and memory consumption.\nDocker containers start in milliseconds and consume negligible memory overhead compared to full VMs.',
                             'Treating containers like heavy virtual machines by trying to run multiple disparate services in a single container.\nStoring persistent application data inside container filesystems without using mounted Docker volumes.'),
                            (6, 'Writing Dockerfiles', 'Writing Production Dockerfiles & Multi-Stage Builds', 30, 'fqMOX6JJhGo',
                             '<h3>Writing Production Dockerfiles</h3><p>Craft clean, secure container images. Master FROM, RUN, COPY, WORKDIR, EXPOSE, and CMD instructions. Utilize multi-stage builds to shrink production image sizes from 1GB to 50MB.</p>',
                             'Order Dockerfile instructions from least-frequently changed to most-frequently changed to maximize build cache reuse.\nMulti-stage builds compile code in a build stage and copy only the final binary into a minimal scratch/distroless runtime image.\nNever run container processes as the default root user; create and switch to a non-privileged user.',
                             'Copying the entire codebase before running dependency installs (e.g., COPY . . before pip install), busting cache on every edit.\nRunning production containers as the root user, creating host escalation security risks.'),
                            (7, 'Docker Networking & Volumes', 'Docker Storage Volumes & Bridge Networking', 25, 'rfscVS0vtbw',
                             '<h3>Docker Storage Volumes & Networking</h3><p>Manage persistent data across container lifecycles with named Docker volumes. Connect isolated containers using user-defined bridge networks and DNS service discovery.</p>',
                             'Named volumes persist database data independently of container restarts and deletions.\nUser-defined bridge networks provide automatic internal DNS resolution between containers by container name.\nBind mounts mirror host directories into containers, ideal for active local development workflows.',
                             'Losing database records when removing a container because data was not stored on a persistent volume.\nUsing legacy container links instead of modern user-defined bridge networks.'),
                            (8, 'Docker Compose', 'Multi-Container Orchestration with Docker Compose', 25, 'rfscVS0vtbw',
                             '<h3>Multi-Container Orchestration with Docker Compose</h3><p>Define multi-tier applications in a single declarative docker-compose.yml file. Coordinate web servers, API backends, PostgreSQL databases, and Redis caching layers.</p>',
                             'docker-compose.yml defines services, networks, volumes, and environment variables declaratively.\nUse depends_on and healthchecks to ensure dependent databases are fully initialized before starting web apps.\nManage local vs production overrides using docker-compose.override.yml files.',
                             'Assuming depends_on waits for a database to be ready to accept SQL queries (it only waits for container startup; use healthcheck).\nCommitting unencrypted production passwords into docker-compose.yml files.')
                        ]
                    },
                    {
                        'order': 3,
                        'title': 'Module 3: CI/CD Automation & GitHub Actions',
                        'description': 'Automate testing, linting, container builds, and cloud deployments with CI/CD pipelines.',
                        'lessons': [
                            (9, 'CI/CD Foundations', 'Continuous Integration & Continuous Delivery (CI/CD) Principles', 25, 'RGOj5yH7evk',
                             '<h3>CI/CD Principles & Pipeline Architecture</h3><p>Explore the philosophy of trunk-based development, automated quality gates, continuous integration, and continuous deployment. Eliminate manual release bottlenecks.</p>',
                             'Continuous Integration merges code frequently, running automated unit tests on every pull request.\nContinuous Delivery ensures every build passing automated testing is immediately deployable to production.\nAutomated pipelines eliminate human deployment errors and dramatically reduce mean time to recovery (MTTR).',
                             'Maintaining long-lived feature branches for months, leading to catastrophic merge conflicts.\nTreating failing CI test runs as acceptable or ignoring broken builds.'),
                            (10, 'GitHub Actions Core', 'Automated Testing & Linting with GitHub Actions', 30, '7xngnjfIlK4',
                             '<h3>Automated Testing with GitHub Actions</h3><p>Create workflow files (.github/workflows). Understand workflow triggers (push, pull_request), jobs, steps, action runners, environment secrets, and test matrix builds.</p>',
                             'Workflows are defined in YAML under .github/workflows/.\nUse matrix strategies to test code across multiple Python versions and operating systems simultaneously.\nStore sensitive API credentials and deployment tokens in GitHub Repository Secrets.',
                             'Exposing secret tokens in plaintext inside workflow YAML configuration files.\nRunning slow integration tests on every minor documentation commit without trigger filtering.'),
                            (11, 'Automated Image Pipelines', 'Building & Pushing Container Images to Amazon ECR', 25, 'ZDa-Z5JzLYM',
                             '<h3>Building & Pushing Images to Amazon ECR</h3><p>Automate Docker builds in CI. Authenticate GitHub Actions with AWS using OpenID Connect (OIDC), tag images with Git commit SHA hashes, and push to Amazon Elastic Container Registry (ECR).</p>',
                             'Use AWS OpenID Connect (OIDC) to authenticate GitHub Actions without storing long-lived AWS secret keys.\nTag every container image with the immutable Git commit SHA hash rather than only the mutable "latest" tag.\nScan container images for known vulnerabilities (CVEs) automatically during the build step.',
                             'Deploying images tagged only with "latest", making it impossible to identify which code version is running or rollback.\nStoring permanent AWS root credentials in CI secrets.'),
                            (12, 'Automated Cloud Deployments', 'Zero-Downtime Deployment Strategies: Rolling & Blue-Green', 25, '8DvywoWv6fI',
                             '<h3>Zero-Downtime Deployment Strategies</h3><p>Deploy application updates without dropping active user connections. Compare Rolling deployments, Canary releases, and Blue/Green environment cutovers.</p>',
                             'Rolling deployments gradually replace old instances with new ones, maintaining continuous availability.\nBlue-Green deployments maintain two identical environments; traffic switches instantaneously at the router level.\nImplement health checks so that unhealthy new containers are automatically terminated and rolled back.',
                             'Deploying directly to production servers without automated rollback capabilities.\nPerforming database schema migrations that are backward-incompatible with active running application code.')
                        ]
                    },
                    {
                        'order': 4,
                        'title': 'Module 4: Infrastructure as Code (Terraform) & Cloud Operations',
                        'description': 'Provision cloud infrastructure with Terraform and monitor production systems with CloudWatch.',
                        'lessons': [
                            (13, 'Terraform Core', 'Infrastructure as Code (IaC) Foundations with Terraform', 30, 'SLB_c_daJDC',
                             '<h3>Infrastructure as Code with Terraform</h3><p>Manage cloud resources as code. Understand HCL syntax, providers, resources, variables, outputs, and the core workflow: terraform init, plan, and apply.</p>',
                             'IaC makes cloud infrastructure version-controlled, auditable, and completely reproducible.\nterraform plan previews exact infrastructure modifications before any cloud resources are created or altered.\nNever make manual modifications via the AWS web console on Terraform-managed resources (prevents configuration drift).',
                             'Applying Terraform changes without reviewing the execution plan.\nManually tweaking cloud resources in the web console, causing state drift and synchronization failures.'),
                            (14, 'Terraform State & Modules', 'Terraform State Management & Reusable Infrastructure Modules', 25, 'SLB_c_daJDC',
                             '<h3>Terraform State Management & Modules</h3><p>Safeguard infrastructure state files. Store terraform.tfstate in remote S3 buckets with DynamoDB state locking to prevent concurrent team execution corruption.</p>',
                             'The Terraform state file maps real-world cloud resources to your configuration files.\nAlways store state files in remote encrypted S3 buckets with DynamoDB distributed state locking.\nPackage recurring architecture patterns (VPC, ECS clusters) into reusable Terraform modules.',
                             'Committing local terraform.tfstate files containing database passwords into Git repositories.\nRunning concurrent terraform apply executions without distributed state locking.'),
                            (15, 'Cloud Monitoring', 'CloudWatch Monitoring, Centralized Logging & Alerting', 25, 'kqtD5dpn9C8',
                             '<h3>CloudWatch Monitoring & Alerting</h3><p>Maintain operational visibility. Configure Amazon CloudWatch metrics (CPU, RAM, HTTP 5xx errors), stream application logs, and configure SNS alerts for on-call engineers.</p>',
                             'Monitor high-level Golden Signals: Latency, Traffic, Errors, and Saturation.\nConfigure CloudWatch Alarms to trigger auto-scaling or notify on-call teams via Amazon SNS when error rates spike.\nAggregate structured JSON application logs centrally for fast search and debugging.',
                             'Alerting on noisy, low-priority symptoms rather than actionable, user-impacting errors.\nFailing to configure synthetic health-check monitors that verify critical user journeys end-to-end.'),
                            (16, 'Capstone Project', 'Capstone Project: Automated Cloud Microservices Deployment', 35, '0pd36apRe34',
                             '<h3>Capstone Project: Automated Cloud Microservices Deployment</h3><p>Synthesize all cloud and DevOps skills. Provision an AWS VPC network and ECS cluster with Terraform, containerize a full-stack application with Docker, and configure a complete GitHub Actions CI/CD pipeline.</p>',
                             'A complete modern DevOps implementation pairs declarative IaC with automated CI/CD and monitoring.\nEnforce the principle of least privilege across all IAM roles and security groups.\nDeliver a comprehensive README with architecture diagrams, setup scripts, and teardown instructions.',
                             'Leaving orphaned cloud resources running after completing testing, generating unexpected AWS bills.\nUsing overly broad IAM wildcard permissions (Action: "*", Resource: "*").')
                        ]
                    }
                ],
                'quiz': {
                    'title': 'Cloud Architecture & DevOps Final Quiz',
                    'questions': [
                        ('In the AWS Shared Responsibility Model, which of the following is the customer\'s responsibility?',
                         'Physical security of the AWS data centers',
                         'Patching and maintaining the hypervisor firmware',
                         'Managing operating system patches, firewall rules (Security Groups), and application data encryption',
                         'Replacing failed server power supply units', 'C',
                         'AWS is responsible for security OF the cloud (physical infrastructure, hardware, virtualization). The customer is responsible for security IN the cloud (customer data, IAM, OS updates, firewall configuration).'),
                        ('What is the key benefit of a multi-stage Docker build?',
                         'It allows running multiple different applications in the same container simultaneously',
                         'It compiles code in a build environment and copies only the minimal required runtime artifacts into a slim, secure final image',
                         'It eliminates the need for Dockerfiles',
                         'It automatically installs a full Ubuntu desktop inside the container', 'B',
                         'Multi-stage builds allow developers to use large SDKs and compilers in early stages, then copy only the finalized binary/assets into a lightweight minimal production image, drastically reducing image size and attack surface.'),
                        ('What is the primary difference between public subnets and private subnets in an AWS VPC?',
                         'Public subnets have direct routing to an Internet Gateway; private subnets do not and route outbound traffic via a NAT Gateway',
                         'Private subnets cannot host any servers',
                         'Public subnets are free of charge, while private subnets cost money',
                         'Public subnets only accept IPv6 traffic', 'A',
                         'Public subnets have a route to an Internet Gateway (IGW), allowing instances with public IPs to receive inbound internet traffic. Private subnets route outbound requests through a NAT Gateway and are shielded from inbound internet access.'),
                        ('Why should you always run "terraform plan" before "terraform apply"?',
                         'To delete all existing cloud resources',
                         'To review the exact execution plan and preview which resources will be created, modified, or destroyed before making real changes',
                         'To compress the state file',
                         'To format the syntax of HCL files', 'B',
                         '"terraform plan" reads the current cloud state, compares it to your configuration files, and displays an execution plan showing exactly what will be added, changed, or destroyed before you apply any real modifications.'),
                        ('In modern CI/CD, why is it recommended to tag Docker images with the Git commit SHA rather than just "latest"?',
                         'The Git commit SHA is shorter to type',
                         'The "latest" tag is immutable and cannot be updated',
                         'Tagging with the commit SHA creates an immutable, verifiable link between the deployed container image and the exact source code commit',
                         'Docker does not support the word "latest"', 'C',
                         'The "latest" tag is mutable and can point to different code versions over time. Tagging with the unique Git commit SHA ensures that every image is permanent, traceable to the exact commit, and enables reliable, instant rollbacks.')
                    ]
                }
            }
        ]

        total_courses_created = 0
        total_modules_created = 0
        total_lessons_created = 0
        total_quizzes_created = 0

        for cspec in courses_spec:
            cat = cat_objects[cspec['category_slug']]
            course, created = Course.objects.update_or_create(
                slug=cspec['slug'],
                defaults={
                    'title': cspec['title'],
                    'category': cat,
                    'difficulty': cspec['difficulty'],
                    'instructor_name': cspec['instructor_name'],
                    'instructor_title': cspec['instructor_title'],
                    'estimated_duration': cspec['estimated_duration'],
                    'thumbnail_url': cspec['thumbnail_url'],
                    'short_description': cspec['short_description'],
                    'description': cspec['description'],
                    'learning_objectives': cspec['learning_objectives'],
                    'prerequisites': cspec['prerequisites'],
                    'curriculum_version': 2,
                    'is_published': True,
                }
            )
            total_courses_created += 1
            action_str = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action_str} Course: {course.title} [{course.slug}]'))

            # Modules and Lessons
            for mod_data in cspec['modules']:
                module, _ = CourseModule.objects.update_or_create(
                    course=course,
                    order=mod_data['order'],
                    defaults={
                        'title': mod_data['title'],
                        'description': mod_data['description'],
                        'is_published': True,
                    }
                )
                total_modules_created += 1

                for (order, chapter, title, mins, vid_id, content, takeaways, mistakes) in mod_data['lessons']:
                    video_url = f"https://www.youtube.com/embed/{vid_id}?enablejsapi=1&rel=0"
                    Lesson.objects.update_or_create(
                        course=course,
                        lesson_order=order,
                        defaults={
                            'module': module,
                            'chapter_name': chapter,
                            'title': title,
                            'estimated_minutes': mins,
                            'video_url': video_url,
                            'video_duration_seconds': mins * 60,
                            'video_type': 'optional',
                            'content': content,
                            'key_takeaways': takeaways,
                            'common_mistakes': mistakes,
                            'curriculum_version': 2,
                        }
                    )
                    total_lessons_created += 1

            # Final Quiz Assessment
            qspec = cspec.get('quiz')
            if qspec:
                assessment, _ = CourseAssessment.objects.update_or_create(
                    course=course,
                    assessment_type='final_quiz',
                    defaults={
                        'title': qspec['title'],
                        'description': '100% Optional final assessment. Test your knowledge to earn up to +20% bonus progress.',
                        'duration_minutes': 30,
                        'passing_percentage': 70,
                        'max_attempts': 5,
                        'is_active': True,
                    }
                )
                total_quizzes_created += 1

                for q_idx, (q_text, opt_a, opt_b, opt_c, opt_d, ans, expl) in enumerate(qspec['questions'], start=1):
                    CourseAssessmentQuestion.objects.update_or_create(
                        assessment=assessment,
                        order=q_idx,
                        defaults={
                            'question_text': q_text,
                            'topic': 'Core Concepts',
                            'option_a': opt_a,
                            'option_b': opt_b,
                            'option_c': opt_c,
                            'option_d': opt_d,
                            'correct_answer': ans,
                            'explanation': expl,
                        }
                    )

        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully seeded diverse courses!'
            f'\nCourses: {total_courses_created}'
            f'\nModules: {total_modules_created}'
            f'\nLessons: {total_lessons_created}'
            f'\nQuizzes: {total_quizzes_created}'
        ))
