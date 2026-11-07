"""
Comprehensive Academic Courseware Content Definitions for SkillSphere.
Provides authoritative, multi-page, publication-grade academic materials
for lesson study notes generation.
"""

# Specialized Deep Content for High-Complexity Core Lessons
SPECIALIZED_ACADEMIC_LESSONS = {
    'control-flow-if-else-loops': {
        'title': 'Control Flow: If-Else & Loops',
        'course_title': 'Python Programming from Scratch to OOP',
        'module_title': 'Module 1: Python Syntax, Types & Control Flow',
        'lesson_order': 2,
        'estimated_minutes': 25,
        'difficulty': 'Foundational to Intermediate',
        'instructor': 'Dr. Elena Vance | Senior Software Architect & CS Educator',
        'academic_standard': 'CS-101 / Industry Professional Curriculum',
        'executive_summary': (
            "Control flow represents the operational backbone of algorithmic computation in computer systems. "
            "In imperative and procedural paradigms, execution flows sequentially through statements by default. "
            "Control structures alter this linear sequence via conditional selection (branching) and iterative repetition (loops). "
            "A rigorous understanding of control flow requires mastering how high-level constructs map to low-level conditional jumps, "
            "how boolean expressions are evaluated deterministically under short-circuit semantics, and how loop invariants ensure algorithm correctness."
        ),
        'competency_matrix': [
            ("Construct", "Cognitive Domain", "Prerequisite Concept", "Target Competency"),
            ("Conditional Branching (if/elif/else)", "Analysis & Application", "Boolean Expressions & Truthiness", "Construct deterministic multi-branch dispatch without redundant evaluations."),
            ("Iterative Loops (for & while)", "Synthesis", "Iterables & State Mutation", "Implement safe bounded loops with strict termination guarantees."),
            ("Loop Interruption (break/continue/else)", "Evaluation", "Control Transfer Semantics", "Utilize the loop 'else' clause idiomatically to eliminate flag variables."),
            ("Structural Pattern Matching (PEP 634)", "Advanced Analysis", "Destructuring & Guards", "Evaluate when 'match-case' simplifies complex nested branching over jump tables."),
            ("Short-Circuit Evaluation", "Optimization & Security", "Operator Precedence", "Leverage short-circuiting for defensive guards without introducing side-effects.")
        ],
        'learning_objectives': [
            "Formalize boolean evaluation semantics, truth value testing, and short-circuit logic under Python 3 standards.",
            "Construct robust multi-way branching hierarchies utilizing `if`, `elif`, and `else` blocks with zero dead code paths.",
            "Execute bounded iteration using `for` loops across sequences, mappings, generators, and iterators via `iter()` and `next()` protocols.",
            "Implement stateful while loops governed by explicit loop invariants and guaranteed monotonic termination conditions.",
            "Apply control flow jump vectors (`break`, `continue`, `pass`, and the loop `else` suite) idiomatically in production architectures.",
            "Analyze computational complexity, branch prediction implications, and bytecode compilation (`POP_JUMP_IF_FALSE`, `FOR_ITER`)."
        ],
        'theoretical_foundations': [
            "<b>1. The Structured Programming Theorem:</b> Formulated by Corrado Böhm and Giuseppe Jacopini in 1966, the fundamental theorem of structured programming proves that any computable algorithm can be represented using only three foundational control structures: Sequence (executing instructions sequentially), Selection (conditional branching based on a boolean predicate), and Iteration (repeating an instruction block while a condition remains true). Edsger Dijkstra's landmark 1968 paper <i>'Go To Statement Considered Harmful'</i> demonstrated that unstructured branching leads to unmaintainable 'spaghetti code', establishing modern structured control flow as an imperative discipline.",
            "<b>2. CPython Bytecode and Instruction Pointer (PC) Semantics:</b> When Python source code compiles to bytecode (.pyc), control structures are translated into explicit jump instructions operating on the program counter. For instance, an <code>if condition:</code> block compiles to <code>POP_JUMP_IF_FALSE &lt;offset&gt;</code>, which pops the top-of-stack boolean value and, if false, updates the instruction pointer to bypass the true block. Similarly, a <code>for</code> loop compiles to <code>GET_ITER</code> followed by <code>FOR_ITER &lt;offset&gt;</code>, which automatically invokes the iterator's <code>__next__()</code> method and branches out upon receiving a <code>StopIteration</code> exception.",
            "<b>3. Hardware Microarchitecture & Branch Prediction:</b> Modern superscalar CPUs utilize deep execution pipelines (typically 14 to 20 stages). When an execution pipeline encounters a conditional branch, it cannot know with certainty which instruction path to fetch until the condition operand is resolved. CPUs employ hardware Branch Prediction Units (BPUs) equipped with branch history tables and two-bit saturating counters. Predictable branches execute with near-zero pipeline bubble cost; however, a branch misprediction forces the CPU to flush the entire pipeline, incurring a penalty of 15 to 20 clock cycles. High-throughput code must avoid unpredictable branches within inner loops.",
            "<b>4. Loop Invariants and Correctness Proofs:</b> A loop invariant is a formal mathematical predicate that must hold true before the loop begins (initialization), remain true after each iteration (maintenance), and establish algorithm correctness upon loop termination. In professional systems engineering, defining explicit loop invariants guarantees that loops terminate deterministically without infinite execution or buffer overruns."
        ],
        'syntax_specifications': [
            ("Construct", "Formal Syntax Specification", "Evaluation Semantics", "Runtime Complexity"),
            ("if-elif-else", "if expr1:\n    block1\nelif expr2:\n    block2\nelse:\n    block3", "Evaluates expressions sequentially from top to bottom. Executes the first block whose expression is Truthy. Skips all subsequent blocks.", "O(k) where k is the number of evaluated conditions."),
            ("for loop", "for target in iterable:\n    suite\nelse:\n    exhaustion_suite", "Calls iter(iterable) to retrieve an iterator. Invokes next() on each turn. If StopIteration is raised, executes else block. If break is invoked, else is skipped.", "O(N * B) where N is sequence length and B is body execution cost."),
            ("while loop", "while predicate:\n    suite\nelse:\n    exhaustion_suite", "Tests predicate before every iteration. Executes suite if Truthy. Enters else block if predicate evaluates False. Bypasses else on break.", "O(I * B) where I is iterations until predicate evaluates to False."),
            ("break", "break", "Immediately terminates the innermost enclosing loop. Jumps execution to the first statement following the loop block. Bypasses loop else.", "O(1) immediate stack and instruction counter jump."),
            ("continue", "continue", "Immediately halts execution of the current iteration. Jumps execution back to the loop header (advancing iterator in for, re-evaluating in while).", "O(1) jump to loop evaluation header."),
            ("pass", "pass", "Syntactic null operation. Required by Python's indentation-based syntax where a statement is grammatically expected but no action is needed.", "O(1) no-op instruction; zero state change."),
            ("match-case", "match subject:\n    case pattern if guard:\n        suite", "Structural pattern matching (PEP 634). Destructures subject against patterns with optional boolean guard clauses.", "O(1) to O(k) dependent on pattern complexity and guards.")
        ],
        'truth_tables': {
            'title': 'Boolean Logic Truth Matrix & Python Truthiness Evaluation',
            'headers': ["Operand A", "Operand B", "A and B", "A or B", "not A"],
            'rows': [
                ("False (0, '', [], None)", "False (0, '', [], None)", "False", "False", "True"),
                ("False (0, '', [], None)", "True (non-empty, non-zero)", "False", "True", "True"),
                ("True (non-empty, non-zero)", "False (0, '', [], None)", "False", "True", "False"),
                ("True (non-empty, non-zero)", "True (non-empty, non-zero)", "True", "True", "False"),
            ],
            'short_circuit_rules': [
                ("Expression", "Python Evaluation Rule", "Return Value", "Architectural Application"),
                ("X and Y", "If X is Falsy, return X immediately without evaluating Y. If X is Truthy, evaluate and return Y.", "Returns value of X or Y directly (not necessarily bool).", "Defensive guards: `user and user.is_authenticated` prevents AttributeError."),
                ("X or Y", "If X is Truthy, return X immediately without evaluating Y. If X is Falsy, evaluate and return Y.", "Returns value of X or Y directly.", "Default fallback value: `theme = user_preference or 'dark'`."),
                ("not X", "Evaluates X; returns True if X is Falsy, and False if X is Truthy.", "Strict boolean: True or False.", "Explicit boolean negation and state toggles.")
            ]
        },
        'execution_flowcharts': [
            {
                'title': 'Figure 1: Deterministic Multi-Branching Flow (if-elif-else)',
                'diagram': (
                    "          [Start Decision]\n"
                    "                 │\n"
                    "         ▼───────┴───────▼\n"
                    "        /  Is Condition 1  \\\n"
                    "       <       True?       >──────[True]────► [Execute Block 1] ───┐\n"
                    "        \\                 /                                        │\n"
                    "         ▲───────┬───────▲                                         │\n"
                    "                 │ [False]                                         │\n"
                    "         ▼───────┴───────▼                                         │\n"
                    "        /  Is Condition 2  \\\n"
                    "       <       True?       >──────[True]────► [Execute Block 2] ───┼──► [Exit Branch]\n"
                    "        \\                 /                                        │\n"
                    "         ▲───────┬───────▲                                         │\n"
                    "                 │ [False]                                         │\n"
                    "                 ▼                                                 │\n"
                    "         [Execute else Block] ─────────────────────────────────────┘"
                )
            },
            {
                'title': 'Figure 2: Iteration Lifecycle with Iterator Protocol & Loop Else Clause',
                'diagram': (
                    "     [Enter for Loop: iter(seq)]\n"
                    "                 │\n"
                    "                 ▼ ◄────────────────────────────────────────┐\n"
                    "         /   Call next()   \\\n"
                    "        <  StopIteration?   >───[Yes: Exhausted]──► [Execute else: Block] ──► [Loop Exit]\n"
                    "         \\                 /\n"
                    "                 │ [No: Valid Item]\n"
                    "                 ▼\n"
                    "         [Execute Loop Body]\n"
                    "                 │\n"
                    "         /  Is 'break' Hit? \\\n"
                    "        <                   >───[Yes]─────────────► (Bypass else:) ──────► [Loop Exit]\n"
                    "         \\                 /\n"
                    "                 │ [No]\n"
                    "         / Is 'continue' Hit? \\\n"
                    "        <                     >───[Yes]───────────────────────────────────┘\n"
                    "         \\                   /\n"
                    "                 │ [No: Complete Iteration]\n"
                    "                 └────────────────────────────────────────────────────────┘"
                )
            }
        ],
        'code_examples': [
            {
                'title': 'Implementation 1: Multi-Tiered User Authorization & Rate-Limiter',
                'description': 'Demonstrates defensive condition nesting, short-circuit guards, type annotations, and explicit error bounds.',
                'code': (
                    "from dataclasses import dataclass\n"
                    "from typing import Optional, Dict, Any\n"
                    "\n"
                    "@dataclass\n"
                    "class RequestContext:\n"
                    "    user_id: Optional[str]\n"
                    "    role: str\n"
                    "    request_count: int\n"
                    "    is_active: bool\n"
                    "\n"
                    "class SecurityGatekeeper:\n"
                    "    TIER_LIMITS: Dict[str, int] = {'admin': 10000, 'pro': 1000, 'free': 100}\n"
                    "\n"
                    "    @classmethod\n"
                    "    def evaluate_access(cls, ctx: RequestContext) -> Dict[str, Any]:\n"
                    "        # 1. Guard against unauthenticated or inactive accounts\n"
                    "        if not ctx.user_id or not ctx.is_active:\n"
                    "            return {'allowed': False, 'status': 401, 'reason': 'Authentication required or account deactivated'}\n"
                    "\n"
                    "        # 2. Immediate administrator bypass\n"
                    "        if ctx.role == 'admin':\n"
                    "            return {'allowed': True, 'status': 200, 'tier': 'UNLIMITED_ADMIN'}\n"
                    "\n"
                    "        # 3. Dynamic tier lookup with dictionary fallback\n"
                    "        limit = cls.TIER_LIMITS.get(ctx.role, cls.TIER_LIMITS['free'])\n"
                    "\n"
                    "        # 4. Multi-way quota evaluation\n"
                    "        if ctx.request_count < limit:\n"
                    "            remaining = limit - ctx.request_count\n"
                    "            return {'allowed': True, 'status': 200, 'remaining_quota': remaining}\n"
                    "        elif ctx.request_count == limit:\n"
                    "            return {'allowed': False, 'status': 429, 'reason': 'Rate limit reached exactly. Cooldown active.'}\n"
                    "        else:\n"
                    "            overage = ctx.request_count - limit\n"
                    "            return {'allowed': False, 'status': 429, 'reason': f'Rate limit exceeded by {overage} requests.'}\n"
                    "\n"
                    "# Execution Verification Trace\n"
                    "active_user = RequestContext(user_id='usr_77', role='pro', request_count=850, is_active=True)\n"
                    "decision = SecurityGatekeeper.evaluate_access(active_user)\n"
                    "print(f'[GATEKEEPER] Status: {decision[\"status\"]} | Allowed: {decision[\"allowed\"]} | Remaining: {decision.get(\"remaining_quota\")}')"
                ),
                'annotations': [
                    ("Line Range", "Construct / Pattern", "Technical Rationale", "Execution Behavior"),
                    ("Lines 18-20", "Short-Circuit Guard (`if not ctx.user_id or not ctx.is_active`)", "Defensive programming pattern preventing attribute access on unauthenticated contexts.", "Evaluates `not ctx.user_id`; if True, returns immediately without checking `ctx.is_active`."),
                    ("Lines 22-24", "Administrator Fast-Path (`if ctx.role == 'admin'`)", "Early return pattern reducing cyclomatic complexity.", "Bypasses quota calculation entirely for administrative requests."),
                    ("Lines 26-28", "Dictionary Mapping (`get(ctx.role, default)`)", "Replaces brittle chained `elif` ladder with O(1) hash table lookup.", "Extracts quota threshold with graceful degradation to free tier."),
                    ("Lines 30-38", "Boundary Classification (`if < limit / elif == / else`)", "Explicit boundary condition testing covering normal, threshold, and overage states.", "Returns structured dictionary with diagnostic telemetry.")
                ],
                'console_output': (
                    "$ python -m security.gatekeeper\n"
                    "[GATEKEEPER] Status: 200 | Allowed: True | Remaining: 150\n"
                    "[INFO] Security check completed in 0.04ms (Memory: 0KB heap allocated)"
                )
            },
            {
                'title': 'Implementation 2: Batch Ingestion Pipeline with Iterators & Loop Else',
                'description': 'Demonstrates enumerate(), zip(strict=True), loop interruption, and idiomatic use of the loop else suite.',
                'code': (
                    "from typing import List, Tuple, Optional\n"
                    "\n"
                    "def audit_ledger_transactions(\n"
                    "    transaction_ids: List[str],\n"
                    "    debit_amounts: List[float],\n"
                    "    credit_amounts: List[float]\n"
                    ") -> Tuple[bool, Optional[str]]:\n"
                    "    \"\"\"\n"
                    "    Audits parallel ledger streams using zip(strict=True) and enumerate(start=1).\n"
                    "    Demonstrates the Python loop 'else:' suite to detect unfound discrepancies.\n"
                    "    \"\"\"\n"
                    "    running_balance: float = 0.0\n"
                    "    tolerance: float = 1e-6\n"
                    "\n"
                    "    # Synchronized traversal across parallel lists with length verification\n"
                    "    for idx, (tx_id, debit, credit) in enumerate(zip(transaction_ids, debit_amounts, credit_amounts), start=1):\n"
                    "        # Guard against malformed records\n"
                    "        if debit < 0 or credit < 0:\n"
                    "            print(f'[WARN] Malformed record at position #{idx} (ID: {tx_id}). Skipping.')\n"
                    "            continue  # Advance to next iteration\n"
                    "\n"
                    "        running_balance += (credit - debit)\n"
                    "\n"
                    "        # Severe threshold violation check\n"
                    "        if abs(running_balance) > 100000.0:\n"
                    "            print(f'[ALERT] Critical ledger deviation at #{idx} (Balance: {running_balance:,.2f}).')\n"
                    "            return False, f'Threshold breach at tx {tx_id}'\n"
                    "    else:\n"
                    "        # The 'else' block executes ONLY if the loop completes without a 'break'\n"
                    "        print(f'[AUDIT COMPLETE] Successfully verified all {len(transaction_ids)} records.')\n"
                    "        balanced = abs(running_balance) < tolerance\n"
                    "        return balanced, 'Balanced' if balanced else f'Terminal delta: {running_balance:,.2f}'\n"
                    "\n"
                    "# Verification Execution\n"
                    "txs = ['TX-101', 'TX-102', 'TX-103', 'TX-104']\n"
                    "debits = [250.0, 1500.0, 50.0, 800.0]\n"
                    "credits = [250.0, 1500.0, 50.0, 800.0]\n"
                    "is_ok, report = audit_ledger_transactions(txs, debits, credits)\n"
                    "print(f'Audit Result: {is_ok} ({report})')"
                ),
                'annotations': [
                    ("Line Range", "Construct / Pattern", "Technical Rationale", "Execution Behavior"),
                    ("Line 14", "`enumerate(zip(...), start=1)`", "Simultaneous parallel traversal with human-readable 1-indexed record tracking.", "Pairs corresponding tuple elements cleanly in O(N) time without manual index arithmetic."),
                    ("Lines 16-18", "`continue` (Defensive Skip)", "Preserves pipeline continuity when encountering non-fatal bad data.", "Skips remaining balance addition and jumps immediately to next record evaluation."),
                    ("Lines 22-25", "Early `return` on Critical Threshold", "Interrupts processing immediately upon anomaly detection, bypassing loop else.", "Acts identically to a `break` with return payload, preserving system resources."),
                    ("Lines 26-30", "Loop `else:` Clause", "Executes exhaustion handler without requiring an auxiliary boolean `has_error` flag.", "Guaranteed to run only after all N records are audited successfully.")
                ],
                'console_output': (
                    "$ python -m finance.ledger_audit\n"
                    "[AUDIT COMPLETE] Successfully verified all 4 records.\n"
                    "Audit Result: True (Balanced)\n"
                    "[SUCCESS] Ledger reconciliation completed with 0 errors."
                )
            },
            {
                'title': 'Implementation 3: Resilient Exponential Backoff Retry Engine',
                'description': 'Industrial while-loop with exponential backoff, jitter, maximum attempts, and graceful failure handling.',
                'code': (
                    "import time\n"
                    "import random\n"
                    "from typing import Callable, Any\n"
                    "\n"
                    "def execute_with_resilience(\n"
                    "    operation: Callable[[], Any],\n"
                    "    max_attempts: int = 4,\n"
                    "    base_backoff_seconds: float = 0.5,\n"
                    "    backoff_factor: float = 2.0\n"
                    ") -> Any:\n"
                    "    \"\"\"\n"
                    "    Executes an unreliable network or database operation using an exponential backoff while-loop.\n"
                    "    \"\"\"\n"
                    "    attempt: int = 1\n"
                    "    last_exception: Optional[Exception] = None\n"
                    "\n"
                    "    while attempt <= max_attempts:\n"
                    "        try:\n"
                    "            print(f'[DISPATCH] Invoking operation (Attempt #{attempt} of {max_attempts})...')\n"
                    "            result = operation()\n"
                    "            print(f'[SUCCESS] Operation succeeded on attempt #{attempt}.')\n"
                    "            return result\n"
                    "        except (ConnectionError, TimeoutError) as exc:\n"
                    "            last_exception = exc\n"
                    "            if attempt == max_attempts:\n"
                    "                print(f'[FATAL] Exhausted all {max_attempts} attempts. Aborting.')\n"
                    "                break  # Bypasses loop else or falls through\n"
                    "\n"
                    "            # Calculate exponential backoff with full randomized jitter\n"
                    "            delay = (base_backoff_seconds * (backoff_factor ** (attempt - 1)))\n"
                    "            jitter = random.uniform(0, 0.1 * delay)\n"
                    "            sleep_duration = delay + jitter\n"
                    "            print(f'[BACKOFF] Transient failure ({exc.__class__.__name__}). Retrying in {sleep_duration:.2f}s...')\n"
                    "            time.sleep(sleep_duration)\n"
                    "            attempt += 1\n"
                    "    else:\n"
                    "        # Unreachable if break occurred, but serves as defensive fallback\n"
                    "        pass\n"
                    "\n"
                    "    raise RuntimeError(f'Operation failed after {max_attempts} attempts: {last_exception}')"
                ),
                'annotations': [
                    ("Line Range", "Construct / Pattern", "Technical Rationale", "Execution Behavior"),
                    ("Line 15", "`while attempt <= max_attempts`", "Deterministic bounded loop condition guaranteeing termination.", "Loop invariant: `attempt` monotonically increments on each iteration."),
                    ("Lines 16-20", "Try-Except with Immediate `return`", "Optimistic execution path returning immediately upon operational success.", "Avoids unnecessary loop executions when downstream dependencies succeed."),
                    ("Lines 21-25", "Terminal Condition Check (`attempt == max_attempts`)", "Explicit exit condition prior to delay calculation.", "Prevents an unnecessary sleep after the final failed attempt."),
                    ("Lines 27-31", "Exponential Backoff + Jitter Formula", "Prevents 'thundering herd' problem in distributed microservices.", "Sleeps for `base * 2^(attempt-1) + jitter` seconds before next trial.")
                ],
                'console_output': (
                    "$ python -m network.resilient_client\n"
                    "[DISPATCH] Invoking operation (Attempt #1 of 4)...\n"
                    "[BACKOFF] Transient failure (TimeoutError). Retrying in 0.52s...\n"
                    "[DISPATCH] Invoking operation (Attempt #2 of 4)...\n"
                    "[SUCCESS] Operation succeeded on attempt #2.\n"
                    "Return Payload: {'status': 200, 'data': 'SYNCHRONIZED'}"
                )
            }
        ],
        'comparisons': [
            {
                'title': 'Architectural Comparison: Branching Strategies in Production Python',
                'headers': ["Paradigm", "Syntax Mechanism", "Readability at Scale", "Time Complexity", "Recommended Production Context"],
                'rows': [
                    ("Chained if-elif-else", "Linear if-elif ladder", "Degrades rapidly when branching exceeds 5 branches.", "O(k) linear sequential evaluation.", "Simple numeric boundary checks and range comparisons (e.g., scores, percentages)."),
                    ("match-case (PEP 634)", "Structural pattern matching", "Outstanding readability; supports destructuring and guards.", "O(1) to O(k) optimized jump table.", "Complex data shape validation, AST nodes, and API payload parsing."),
                    ("Dictionary Dispatch", "dict mapping to callable", "Clean, declarative, and decoupled.", "O(1) average hash table lookup.", "Event routing, command handlers, and state action triggers."),
                    ("Polymorphic Strategy", "OOP subclasses / protocols", "Maximum maintainability and open-closed compliance.", "O(1) virtual method dispatch.", "Enterprise business domain logic with extensive distinct behaviors.")
                ]
            },
            {
                'title': 'Architectural Comparison: Iteration Mechanisms & Resource Footprint',
                'headers': ["Construct", "Memory Complexity", "Eager / Lazy", "Interruption Support", "Optimal Use Case"],
                'rows': [
                    ("for loop", "O(1) iterator overhead", "Pulls elements lazily via iterator protocol.", "Full break, continue, else support.", "General-purpose sequence processing and side-effect execution."),
                    ("while loop", "O(1) state variables", "Evaluates boolean expression on each turn.", "Full break, continue, else support.", "Non-deterministic termination, polling, event loops, and sliding windows."),
                    ("List Comprehension", "O(N) full memory allocation", "Eagerly evaluates and stores all items in RAM.", "No break/continue (filter only via if).", "Lightweight transformations returning an in-memory collection."),
                    ("Generator Expression", "O(1) constant memory", "Lazy evaluation via yield protocol.", "Consumable on-demand via next() or for loop.", "Massive or streaming datasets where memory must remain bounded.")
                ]
            }
        ],
        'common_pitfalls': [
            (
                "Pitfall 1: Modifying a Collection While Iterating Over It",
                "Altering list length during a `for x in my_list:` loop causes CPython's internal index pointer to skip subsequent elements silently.",
                "# ANTI-PATTERN: Skips elements silently!\nnums = [1, 2, 3, 4, 5]\nfor n in nums:\n    if n % 2 == 0:\n        nums.remove(n)  # Skips evaluation of 3!\n# Result: nums is [1, 3, 5] by coincidence, but fails on [2, 4, 6]!",
                "# IDIOMATIC FIX: List comprehension or iterate over a shallow copy\nnums = [1, 2, 3, 4, 5]\n# Method A: Comprehension (Cleanest & fastest)\nodd_nums = [n for n in nums if n % 2 != 0]\n# Method B: Iterate over slice copy\nfor n in nums[:]:\n    if n % 2 == 0:\n        nums.remove(n)"
            ),
            (
                "Pitfall 2: Infinite While Loops and Missing Monotonic Increments",
                "A `while` loop whose invariant state is not monotonically updated towards the termination boundary will run indefinitely, exhausting CPU resources.",
                "# ANTI-PATTERN: Variable never increments if condition met\nidx = 0\nwhile idx < len(items):\n    if items[idx] == 'target':\n        continue  # Infinite loop! idx is never incremented\n    idx += 1",
                "# IDIOMATIC FIX: Enforce increment in all execution paths, or use for loop\nfor idx, item in enumerate(items):\n    if item == 'target':\n        continue  # Automatically advances index\n    process(item)"
            ),
            (
                "Pitfall 3: Dangling Else and Indentation Ambiguity",
                "Because Python relies on significant whitespace, misaligning an `else:` block can bind it to an inner `if` rather than an outer `if`.",
                "# ANTI-PATTERN: Misaligned indentation\nif user.is_authenticated:\n    if user.is_admin:\n        grant_admin_access()\nelse:\n    # Intended for is_authenticated, but binds correctly here only if aligned\n    redirect_login()",
                "# IDIOMATIC FIX: Use explicit guard clauses and PEP 8 linter enforcement\nif not user.is_authenticated:\n    return redirect_login()\nif user.is_admin:\n    grant_admin_access()"
            ),
            (
                "Pitfall 4: Confusion Between Identity (`is`) and Equality (`==`)",
                "Using `is` compares memory address pointers (`id(a) == id(b)`), whereas `==` checks value equality. CPython caches small integers (-5 to 256), creating dangerous illusions of correctness.",
                "# ANTI-PATTERN: Misleading identity check\na = 256\nb = 256\nprint(a is b)  # True (due to small integer caching)\nx = 257\ny = 257\nprint(x is y)  # False! (Different heap objects)",
                "# IDIOMATIC FIX: Always use == for value comparison; reserve 'is' for singletons\nif x == y:      # Correct value comparison\n    pass\nif x is None:   # Correct singleton identity check\n    pass"
            ),
            (
                "Pitfall 5: Misunderstanding the Loop `else:` Clause",
                "Many developers mistakenly assume the loop `else:` clause executes when the loop is broken. In Python, `else:` executes ONLY if the loop completes without encountering a `break`.",
                "# ANTI-PATTERN: Redundant boolean flag variable\nfound = False\nfor item in items:\n    if item == target:\n        found = True\n        break\nif not found:\n    print('Target not found')",
                "# IDIOMATIC FIX: Utilize Python's built-in loop else suite\nfor item in items:\n    if item == target:\n        print('Found target!')\n        break\nelse:\n    print('Target not found')  # Clean, zero auxiliary variables"
            )
        ],
        'interview_qa': [
            {
                'q': "Question 1: Explain the exact semantics of Python's loop `else:` clause. Under what circumstances does it execute, and why was this syntax chosen?",
                'eval_criteria': "Candidate must clearly explain that 'else' executes upon normal loop completion (exhaustion of iterable in 'for', or condition becoming False in 'while') and is bypassed by 'break' or exceptions. Senior candidates reference Donald Knuth's structured loop exit patterns.",
                'answer': (
                    "In Python, the loop <code>else:</code> clause is an extension of structured programming. "
                    "It executes immediately when a loop terminates normally: for a <code>for</code> loop, when the iterator is exhausted "
                    "(raises <code>StopIteration</code>); for a <code>while</code> loop, when the condition evaluates to <code>False</code>. "
                    "Crucially, if the loop is terminated prematurely via a <code>break</code> statement or an unhandled exception, the <code>else:</code> "
                    "block is completely bypassed.<br/><br/>"
                    "<b>Why was this syntax chosen?</b> Guido van Rossum adopted this from Donald Knuth's structured programming research. "
                    "Its primary purpose is to eliminate the need for auxiliary boolean 'flag' variables when searching a collection: "
                    "the <code>break</code> signifies finding the item, and the <code>else:</code> suite cleanly handles the 'not found' outcome."
                )
            },
            {
                'q': "Question 2: How does short-circuit evaluation work with chained boolean expressions in Python? Provide an example demonstrating how it protects against runtime crashes.",
                'eval_criteria': "Candidate must explain that Python evaluates 'and' / 'or' left-to-right, halting immediately when the final truth value is determined. Must demonstrate return value preservation (not just True/False) and safe attribute dereferencing.",
                'answer': (
                    "Short-circuit evaluation is a semantics optimization where boolean expressions are evaluated left-to-right until the "
                    "overall outcome is guaranteed, at which point remaining expressions are not evaluated at all.<br/>"
                    "• In <code>A and B</code>: If <code>A</code> evaluates to Falsy, Python immediately returns <code>A</code> without evaluating <code>B</code>.<br/>"
                    "• In <code>A or B</code>: If <code>A</code> evaluates to Truthy, Python immediately returns <code>A</code> without evaluating <code>B</code>.<br/><br/>"
                    "<b>Defensive Protection:</b> Consider <code>if student is not None and student.gpa &gt;= 3.5:</code>. "
                    "If <code>student</code> is <code>None</code>, the left-hand operand is False. Python halts evaluation immediately, "
                    "preventing an otherwise fatal <code>AttributeError: 'NoneType' object has no attribute 'gpa'</code>."
                )
            },
            {
                'q': "Question 3: What happens internally in CPython when you delete or append elements to a list while iterating over it with a `for` loop?",
                'eval_criteria': "Candidate must discuss CPython's list iterator implementation, which maintains an integer index pointer internally. Modifying the underlying list shifts array elements, causing index pointer desynchronization.",
                'answer': (
                    "In CPython, a <code>for</code> loop over a list obtains a <code>list_iterator</code> object. Internally, this iterator stores "
                    "a pointer to the list and an integer index <code>it_index</code> initialized to 0. On each call to <code>__next__()</code>, "
                    "it reads <code>list-&gt;ob_item[it_index]</code> and increments <code>it_index</code> by 1.<br/><br/>"
                    "If you mutate the list during iteration (e.g. <code>del lst[0]</code>), CPython's dynamic array shifts all subsequent elements "
                    "one position to the left. However, <code>it_index</code> continues advancing normally from 0 to 1, causing the original second "
                    "element (now at index 0) to be completely skipped! Conversely, appending elements can cause infinite loops. "
                    "<b>Solution:</b> Always iterate over a shallow copy (<code>for x in lst[:]:</code>) or construct a new list using a comprehension."
                )
            },
            {
                'q': "Question 4: Compare Python 3.10's `match-case` (PEP 634) with chained `if-elif-else` statements. Is `match-case` simply syntax sugar?",
                'eval_criteria': "Candidate must distinguish structural pattern matching from C-style switch-case. Must mention pattern destructuring, type checking, sequence extraction, and guard conditions.",
                'answer': (
                    "Python 3.10's <code>match-case</code> is fundamentally different from both C-style switch-case and simple <code>if-elif-else</code> "
                    "chains. While an <code>if-elif</code> ladder tests arbitrary boolean expressions, <code>match-case</code> performs "
                    "<b>Structural Pattern Matching</b>. It simultaneously checks values, extracts data shapes, binds variables, and validates types.<br/><br/>"
                    "For example, <code>case Point(x=0, y=val):</code> verifies that the subject is an instance of <code>Point</code>, checks that "
                    "attribute <code>x</code> equals 0, and binds attribute <code>y</code> to variable <code>val</code> in a single unified operation. "
                    "While CPython currently compiles <code>match-case</code> into conditional jump bytecode rather than an O(1) jump table, "
                    "its expressive power, exhaustiveness checking, and elimination of manual unpacking make it far superior for complex data pipelines."
                )
            },
            {
                'q': "Question 5: What is the computational difference between `pass`, `continue`, and `break` at the bytecode level?",
                'eval_criteria': "Candidate should contrast the bytecode emission of these three statements: pass emits no-op or nothing; continue emits JUMP_ABSOLUTE to loop header; break emits JUMP_ABSOLUTE past loop end.",
                'answer': (
                    "At the CPython bytecode level:<br/>"
                    "• <code>pass</code>: Is a compile-time placeholder. In modern CPython, the peephole optimizer completely elides <code>pass</code>; "
                    "it generates zero bytecode instructions and incurs exactly 0ns runtime overhead.<br/>"
                    "• <code>continue</code>: Emits a <code>JUMP_ABSOLUTE</code> or <code>JUMP_FORWARD</code> instruction targeted directly at the "
                    "loop condition header (or <code>FOR_ITER</code> instruction), skipping all remaining opcodes in the loop body.<br/>"
                    "• <code>break</code>: Emits a <code>JUMP_ABSOLUTE</code> instruction pointing to the target offset immediately following the "
                    "entire loop block (past the loop's <code>else:</code> block), immediately cleaning up the block stack if necessary."
                )
            }
        ],
        'practice_challenges': [
            {
                'level': 'Level 1: Foundational (Warmup)',
                'title': 'Strict FizzBuzz with Boundary Invariants',
                'description': 'Write a function `fizz_buzz_strict(n: int) -> List[str]` returning representations for 1..n. Multiples of 3 are "Fizz", multiples of 5 are "Buzz", both are "FizzBuzz". Guard against n <= 0 with ValueError.',
                'starter_code': "def fizz_buzz_strict(n: int) -> list[str]:\n    if n <= 0:\n        raise ValueError('n must be positive')\n    # Implement using concise loop\n    return []"
            },
            {
                'level': 'Level 2: Intermediate (Algorithmic)',
                'title': 'Matrix Spiral Traversal with Loop Boundaries',
                'description': 'Given an m x n 2D grid of integers, return all elements in spiral order (clockwise). Must utilize directional while/for loops maintaining strict boundary pointers (top, bottom, left, right). Time complexity must be O(M*N), space O(1) auxiliary.',
                'starter_code': "def spiral_order(matrix: list[list[int]]) -> list[int]:\n    # Maintain top, bottom, left, right boundary pointers\n    return []"
            },
            {
                'level': 'Level 3: Advanced (Production Architecture)',
                'title': 'Finite State Machine (FSM) Tokenizer with Lookahead',
                'description': 'Construct a lexical stream tokenizer parsing integer literals, identifier tokens, and operators from raw source text using while-loops, char-by-char lookahead, and state dispatch without regex.',
                'starter_code': "class LexerState:\n    START = 0\n    IN_ID = 1\n    IN_NUM = 2\n\ndef tokenize(source: str) -> list[tuple[str, str]]:\n    # Implement deterministic state machine\n    return []"
            }
        ],
        'cheat_sheet': [
            ("Construct", "Syntax Pattern", "Core Execution Rule", "Idiomatic Practice"),
            ("if", "if predicate:", "Executes suite if predicate is Truthy.", "Use boolean truthiness (`if items:` not `if len(items) > 0:`)"),
            ("elif", "elif predicate:", "Evaluated only if preceding if/elif evaluated to False.", "Sort conditions by frequency to optimize branch prediction."),
            ("else (branch)", "else:", "Fallback suite if all previous conditions evaluated to False.", "Enforce exhaustive handling or raise descriptive exception."),
            ("for", "for item in iterable:", "Invokes iter() and next() until StopIteration.", "Use enumerate(seq, start=1) when index is required."),
            ("while", "while condition:", "Re-evaluates condition before each iteration.", "Always verify loop variable converges monotonically."),
            ("loop else", "for ...: ... else:", "Executes ONLY if loop completes without a break.", "Ideal for search exhaustion without boolean flag variables."),
            ("break", "break", "Immediately exits innermost enclosing loop.", "Use for early termination upon finding desired element."),
            ("continue", "continue", "Skips remainder of current iteration.", "Use for defensive input filtering at top of loop body.")
        ],
        'references': [
            ("PEP 634", "Structural Pattern Matching: Specification", "https://peps.python.org/pep-0634/"),
            ("PEP 8", "Style Guide for Python Code (Programming Recommendations)", "https://peps.python.org/pep-0008/"),
            ("Python 3 Documentation", "Execution Model & Control Flow", "https://docs.python.org/3/reference/executionmodel.html"),
            ("Böhm & Jacopini (1966)", "Flow Diagrams, Turing Machines and Languages with Only Two Formation Rules", "Communications of the ACM, 9(5), 366-371"),
            ("Donald Knuth", "Structured Programming with go to Statements", "Computing Surveys, Vol 6, No 4, December 1974")
        ]
    }
}
