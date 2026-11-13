/**
 * SkillSphere Universal Spotlight Command Palette
 * Trigger via Cmd+K (macOS), Ctrl+K (Windows/Linux), or UI search trigger.
 * Phase 6: Expanded Indexing, Coding Challenges, Quick Actions & Recruiter Scout
 */
(function() {
    const COMMAND_ITEMS = [
        // ==========================================
        // 1. Coding Challenges Index
        // ==========================================
        {
            category: "Coding Challenges",
            title: "Two Sum",
            desc: "Array hashing & two pointers — Find indices that sum to target O(N)",
            icon: "code-2",
            url: "/skill-assessment/challenges/two-sum/",
            keywords: "two sum array hashmap target leetcode easy pairs"
        },
        {
            category: "Coding Challenges",
            title: "Valid Parentheses",
            desc: "Stack evaluation — Verify balanced (), {}, [] bracket combinations",
            icon: "code-2",
            url: "/skill-assessment/challenges/valid-parentheses/",
            keywords: "valid parentheses stack brackets matching balanced leetcode easy"
        },
        {
            category: "Coding Challenges",
            title: "Binary Search",
            desc: "Logarithmic divide-and-conquer search in sorted arrays O(log N)",
            icon: "code-2",
            url: "/skill-assessment/challenges/binary-search/",
            keywords: "binary search sorted array divide conquer logarithmic easy"
        },
        {
            category: "Coding Challenges",
            title: "Maximum Subarray",
            desc: "Kadane's algorithm — Discover contiguous slice with maximum sum O(N)",
            icon: "code-2",
            url: "/skill-assessment/challenges/maximum-subarray/",
            keywords: "maximum subarray kadanes kadane dynamic programming contiguous medium"
        },
        {
            category: "Coding Challenges",
            title: "Best Time to Buy and Sell Stock",
            desc: "Single-pass profit optimization & greedy sliding window approach",
            icon: "code-2",
            url: "/skill-assessment/challenges/best-time-to-buy-and-sell-stock/",
            keywords: "best time to buy and sell stock profit greedy valley peak medium"
        },

        // ==========================================
        // 2. Quick Actions
        // ==========================================
        {
            category: "Quick Actions",
            title: "Open 1v1 Arena",
            desc: "Launch competitive real-time blitz duel with live buzzer against peers",
            icon: "swords",
            url: "/achievements/arena/",
            keywords: "arena 1v1 duel battle vs fight buzzer timer rating"
        },
        {
            category: "Quick Actions",
            title: "Export Resume PDF",
            desc: "Direct vector download of your Harvard FAANG formatted resume",
            icon: "download",
            url: "/resume-builder/",
            keywords: "export resume pdf download cv print ats direct"
        },
        {
            category: "Quick Actions",
            title: "Toggle Sound SFX",
            desc: "Enable or mute subtle acoustic haptic feedback across interactions",
            icon: "volume-2",
            action: () => {
                if (window.SkillSphereSFX) {
                    const state = window.SkillSphereSFX.toggle();
                    showPaletteToast(`Sound Effects ${state ? 'Enabled' : 'Muted'}`);
                }
            },
            keywords: "sound sfx audio volume mute unmute acoustic haptic"
        },
        {
            category: "Quick Actions",
            title: "Browse Courses",
            desc: "Explore 6 flagship production engineering curriculums & tracks",
            icon: "compass",
            url: "/courses/",
            keywords: "browse courses catalog learn syllabus tracks curriculum"
        },
        {
            category: "Quick Actions",
            title: "Browse Challenges",
            desc: "Online code judge with real-time testcase assertions and Pyodide WebAssembly",
            icon: "terminal",
            url: "/skill-assessment/challenges/",
            keywords: "browse challenges problems algorithmic leetcode judge testcases"
        },
        {
            category: "Quick Actions",
            title: "Open Pair Lounge",
            desc: "Live collaborative pair programming room with system design whiteboard",
            icon: "users",
            url: "/collaboration/lounge/",
            keywords: "pair programming lounge collaborate whiteboard room shared code"
        },
        {
            category: "Quick Actions",
            title: "Open Resume Studio",
            desc: "ATS keyword optimizer, live canvas zoom, and section reordering",
            icon: "file-text",
            url: "/resume-builder/",
            keywords: "resume builder cv studio ats faang zoom reorder"
        },
        {
            category: "Quick Actions",
            title: "Open Career Hub",
            desc: "Map verified courses and project capstones directly to industry roles",
            icon: "target",
            url: "/careers/career-hub/",
            keywords: "career hub jobs readiness tracker skills competencies"
        },
        {
            category: "Quick Actions",
            title: "Open Certificates",
            desc: "View and claim verified completion certificates with cryptographic hashes",
            icon: "award",
            url: "/certificates/",
            keywords: "certificates credentials verified claim awards badges proof"
        },
        {
            category: "Quick Actions",
            title: "Open Dashboard",
            desc: "Your daily overview, study streak, XP levels, and quick metrics",
            icon: "layout-dashboard",
            url: "/dashboard/",
            keywords: "dashboard home overview progress streak stats"
        },
        {
            category: "Quick Actions",
            title: "Start 60s Skill Duel",
            desc: "Compete in Python or SQL rapid-fire challenge with real Elo rewards",
            icon: "zap",
            url: "/achievements/leagues/",
            keywords: "duel 60s blitz sprint league rapid fire"
        },
        {
            category: "Quick Actions",
            title: "Track New Job Application",
            desc: "Add an employer to 6-stage Kanban board and run ATS keyword match",
            icon: "plus-circle",
            url: "/careers/tracker/",
            keywords: "track job application kanban pipeline employer ats"
        },
        {
            category: "Quick Actions",
            title: "Replay Cinematic Intro Splash",
            desc: "Trigger 3D orbital canvas and particle sphere splash animation",
            icon: "play",
            action: () => {
                if (window.playSkillSphereIntro) window.playSkillSphereIntro();
            },
            keywords: "intro splash animation 3d sphere replay"
        },
        {
            category: "Quick Actions",
            title: "Launch AI Coding Assistant",
            desc: "Ask technical architecture, algorithm design, and debugging questions",
            icon: "bot",
            url: "/assistant/",
            keywords: "ai assistant chat copilot help debug architecture"
        },

        // ==========================================
        // 3. Navigation Hubs
        // ==========================================
        { category: "Navigation", title: "My Learning", desc: "Active enrollments, course milestones, and certificates", icon: "book-marked", url: "/courses/my-learning/", keywords: "my learning enrollments progress" },
        { category: "Navigation", title: "Study Lounge & Pomodoro", desc: "Lofi ambient music, timer, and task manager", icon: "headphones", url: "/dashboard/study-lounge/", keywords: "study lounge lofi music pomodoro timer focus" },
        { category: "Navigation", title: "Spaced Repetition Flashcards (SM-2)", desc: "Memory retention decks and review drills", icon: "layers", url: "/learn/flashcards/", keywords: "flashcards anki spaced repetition memory sm2" },
        { category: "Navigation", title: "Weekly Competitive Leagues", desc: "Duolingo-style cohort standings and promotion zones", icon: "trophy", url: "/achievements/leagues/", keywords: "leagues leaderboard ranks xp division duolingo" },
        { category: "Navigation", title: "AI Voice Mock Interview Studio", desc: "Real-time speech evaluation and tech scoring", icon: "mic", url: "/career/mock-interview-studio/", keywords: "mock interview voice speech scoring hr tech" },
        { category: "Navigation", title: "AI Capstone Project Generator", desc: "Production blueprints with 1-click GitHub sync", icon: "sparkles", url: "/projects/generator/", keywords: "capstone generator project blueprint github repo" },
        { category: "Navigation", title: "Public Developer Portfolio", desc: "Showcase verified capstones and certifications", icon: "globe", url: "/portfolios/builder/", keywords: "portfolio showcase public profile developer link" },
        { category: "Navigation", title: "Verify Credential (QR)", desc: "Cryptographic certificate validation portal", icon: "qr-code", url: "/verify/", keywords: "verify credential certificate qr validate authenticity" },

        // ==========================================
        // 4. Recruiter Candidate Search (Authorized)
        // ==========================================
        {
            category: "Recruiter Scout",
            title: "Recruiter Talent Portal",
            desc: "Filter candidates by judge pass-rate, Elo blitz rating, and Harvard ATS score",
            icon: "scan-face",
            url: "/opportunities/talent/",
            keywords: "recruiter talent scout candidates hire applicants proof of work",
            recruiterOnly: true
        },
        {
            category: "Recruiter Scout",
            title: "Shortlisted Pipeline",
            desc: "View bookmarked candidates and track interview invitations",
            icon: "bookmark-check",
            url: "/opportunities/talent/shortlist/",
            keywords: "shortlist pipeline recruiter candidates interview bookmarks",
            recruiterOnly: true
        }
    ];

    let activeIndex = 0;
    let filteredItems = [...COMMAND_ITEMS];

    function isRecruiterUser() {
        const backdrop = document.getElementById('commandPaletteBackdrop');
        return backdrop && backdrop.getAttribute('data-is-recruiter') === 'true';
    }

    function initCommandPalette() {
        const backdrop = document.getElementById('commandPaletteBackdrop');
        const searchInput = document.getElementById('commandPaletteInput');
        if (!backdrop || !searchInput) return;

        // Global hotkey: Cmd+K or Ctrl+K
        document.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) {
                e.preventDefault();
                togglePalette();
            } else if (e.key === 'Escape' && backdrop.classList.contains('open')) {
                e.preventDefault();
                closePalette();
            } else if (backdrop.classList.contains('open')) {
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    navigateItems(1);
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    navigateItems(-1);
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    executeActiveItem();
                }
            }
        });

        // Click outside backdrop
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                closePalette();
            }
        });

        // Search filtering
        searchInput.addEventListener('input', (e) => {
            filterPalette(e.target.value);
        });

        // Initial populate
        filterPalette('');
    }

    function togglePalette() {
        const backdrop = document.getElementById('commandPaletteBackdrop');
        const searchInput = document.getElementById('commandPaletteInput');
        if (!backdrop) return;

        if (backdrop.classList.contains('open')) {
            closePalette();
        } else {
            backdrop.classList.add('open');
            if (window.SkillSphereSFX) window.SkillSphereSFX.play('click');
            if (searchInput) {
                searchInput.value = '';
                filterPalette('');
                setTimeout(() => searchInput.focus(), 50);
            }
        }
    }

    function closePalette() {
        const backdrop = document.getElementById('commandPaletteBackdrop');
        if (backdrop) backdrop.classList.remove('open');
    }

    function filterPalette(query) {
        const q = query.toLowerCase().trim();
        const isRecruiter = isRecruiterUser();

        // Base items accessible to current user
        const baseItems = COMMAND_ITEMS.filter(item => {
            if (item.recruiterOnly && !isRecruiter) return false;
            return true;
        });

        if (!q) {
            filteredItems = [...baseItems];
        } else {
            // Tokenized multi-word search
            const tokens = q.split(/\s+/).filter(Boolean);
            let matches = baseItems.filter(item => {
                const searchCorpus = `${item.title} ${item.desc} ${item.category} ${item.keywords || ''}`.toLowerCase();
                return tokens.every(tok => searchCorpus.includes(tok));
            });

            // Dynamic Recruiter Candidate Search item when authorized
            if (isRecruiter || q.startsWith('@') || q.startsWith('candidate:')) {
                const cleanQuery = q.replace(/^candidate:\s*|^@/, '').trim();
                if (cleanQuery) {
                    matches.unshift({
                        category: "Recruiter Scout",
                        title: `Search Candidates for "${cleanQuery}"`,
                        desc: "Scout talent pool verified by judge pass-rates & Elo ratings",
                        icon: "search",
                        url: `/opportunities/talent/?q=${encodeURIComponent(cleanQuery)}`,
                        keywords: "candidate talent search scout"
                    });
                }
            }

            filteredItems = matches;
        }

        activeIndex = 0;
        renderItems();
    }

    function renderItems() {
        const body = document.getElementById('commandPaletteResults');
        if (!body) return;

        if (filteredItems.length === 0) {
            body.innerHTML = `
                <div class="text-center py-5 text-muted small">
                    <i data-lucide="search-x" style="width: 28px; height: 28px;" class="mb-2 opacity-50"></i>
                    <div>No commands, challenges, or pages matching your search.</div>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
            return;
        }

        let html = '';
        let currentCategory = '';

        filteredItems.forEach((item, idx) => {
            if (item.category !== currentCategory) {
                currentCategory = item.category;
                html += `<div class="command-palette-section-title">${currentCategory}</div>`;
            }

            const isActive = idx === activeIndex;
            html += `
                <div class="command-palette-item ${isActive ? 'active' : ''}" data-idx="${idx}" onclick="window.executePaletteItem(${idx})">
                    <div class="command-palette-item-left">
                        <div class="command-palette-item-icon">
                            <i data-lucide="${item.icon}" style="width: 16px; height: 16px;"></i>
                        </div>
                        <div>
                            <div class="command-palette-item-title">${escapeHtml(item.title)}</div>
                            <div class="command-palette-item-desc">${escapeHtml(item.desc)}</div>
                        </div>
                    </div>
                    <span class="command-palette-keycap">&crarr;</span>
                </div>
            `;
        });

        body.innerHTML = html;
        if (window.lucide) lucide.createIcons();

        // Scroll active item into view
        const activeEl = body.querySelector('.command-palette-item.active');
        if (activeEl) {
            activeEl.scrollIntoView({ block: 'nearest' });
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function navigateItems(delta) {
        if (filteredItems.length === 0) return;
        activeIndex = (activeIndex + delta + filteredItems.length) % filteredItems.length;
        renderItems();
        if (window.SkillSphereSFX) window.SkillSphereSFX.play('click');
    }

    function executeActiveItem() {
        if (filteredItems.length === 0) return;
        executeItem(activeIndex);
    }

    function executeItem(index) {
        const item = filteredItems[index];
        if (!item) return;

        if (window.SkillSphereSFX) window.SkillSphereSFX.play('click');
        closePalette();

        if (item.action) {
            item.action();
        } else if (item.url) {
            window.location.href = item.url;
        }
    }

    function showPaletteToast(msg) {
        const toast = document.createElement('div');
        toast.className = 'position-fixed bottom-0 end-0 p-3';
        toast.style.zIndex = '100000';
        toast.innerHTML = `
            <div class="toast show align-items-center text-white bg-primary border-0 shadow-lg" role="alert">
                <div class="d-flex">
                    <div class="toast-body small fw-medium">${escapeHtml(msg)}</div>
                </div>
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2500);
    }

    window.openCommandPalette = togglePalette;
    window.executePaletteItem = executeItem;

    document.addEventListener('DOMContentLoaded', initCommandPalette);
})();
