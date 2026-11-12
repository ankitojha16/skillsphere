/**
 * SkillSphere Universal Spotlight Command Palette
 * Trigger via Cmd+K (macOS), Ctrl+K (Windows/Linux), or UI search trigger.
 */
(function() {
    const COMMAND_ITEMS = [
        // Navigation
        { category: "Navigation", title: "Dashboard", desc: "Your daily overview, study streak, and analytics", icon: "layout-dashboard", url: "/dashboard/" },
        { category: "Navigation", title: "Explore Courses", desc: "Full catalog of production engineering paths", icon: "compass", url: "/courses/" },
        { category: "Navigation", title: "My Learning", desc: "Active enrollments, course milestones, and certificates", icon: "book-marked", url: "/courses/my-learning/" },
        { category: "Navigation", title: "Study Lounge & Pomodoro", desc: "Lofi ambient music, timer, and task manager", icon: "headphones", url: "/dashboard/study-lounge/" },
        { category: "Navigation", title: "Spaced Repetition Flashcards (SM-2)", desc: "Memory retention decks and review drills", icon: "layers", url: "/learn/flashcards/" },
        { category: "Navigation", title: "Weekly Competitive Leagues", desc: "Duolingo-style cohort standings and promotion zones", icon: "trophy", url: "/achievements/leagues/" },
        { category: "Navigation", title: "AI Job Tracker & Co-Pilot", desc: "6-stage Kanban board and AI cold outreach generator", icon: "kanban", url: "/careers/tracker/" },
        { category: "Navigation", title: "Career Readiness Hub", desc: "Bridge courses and projects to market skills", icon: "target", url: "/careers/career-hub/" },
        { category: "Navigation", title: "AI Resume Studio", desc: "ATS keyword optimizer and 1-click export", icon: "file-text", url: "/resume/builder/" },
        { category: "Navigation", title: "AI Voice Mock Interview Studio", desc: "Real-time speech evaluation and tech scoring", icon: "mic", url: "/career/mock-interview-studio/" },
        { category: "Navigation", title: "AI Capstone Project Generator", desc: "Production blueprints with 1-click GitHub sync", icon: "sparkles", url: "/projects/generator/" },
        { category: "Navigation", title: "Public Developer Portfolio", desc: "Showcase verified capstones and certifications", icon: "globe", url: "/portfolios/builder/" },
        { category: "Navigation", title: "Verify Credential (QR)", desc: "Cryptographic certificate validation portal", icon: "qr-code", url: "/verify/" },
        { category: "Navigation", title: "Achievements & Badges", desc: "XP levels and milestone rewards", icon: "award", url: "/achievements/" },

        // Quick Actions
        { category: "Quick Actions", title: "Start 60s Skill Duel", desc: "Compete in Python or SQL rapid-fire challenge", icon: "swords", action: () => { window.location.href = '/achievements/leagues/'; } },
        { category: "Quick Actions", title: "Track New Job Application", desc: "Log a company and analyze ATS match score", icon: "plus-circle", action: () => { window.location.href = '/careers/tracker/'; } },
        { category: "Quick Actions", title: "Toggle Sound Effects (SFX)", desc: "Enable or mute subtle acoustic haptic feedback", icon: "volume-2", action: () => {
            if (window.SkillSphereSFX) {
                const state = window.SkillSphereSFX.toggle();
                showPaletteToast(`Sound Effects ${state ? 'Enabled' : 'Muted'}`);
            }
        }},
        { category: "Quick Actions", title: "Replay Cinematic Intro Splash", desc: "Trigger 3D orbital sphere animation", icon: "play", action: () => {
            if (window.playSkillSphereIntro) window.playSkillSphereIntro();
        }},
        { category: "Quick Actions", title: "Launch AI Coding Assistant", desc: "Ask technical architecture and debugging questions", icon: "bot", url: "/assistant/" },
    ];

    let activeIndex = 0;
    let filteredItems = [...COMMAND_ITEMS];

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

        // Render initial items
        renderItems();
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
        if (!q) {
            filteredItems = [...COMMAND_ITEMS];
        } else {
            filteredItems = COMMAND_ITEMS.filter(item => 
                item.title.toLowerCase().includes(q) ||
                item.desc.toLowerCase().includes(q) ||
                item.category.toLowerCase().includes(q)
            );
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
                    <div>No commands or pages matching your search.</div>
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
                            <div class="command-palette-item-title">${item.title}</div>
                            <div class="command-palette-item-desc">${item.desc}</div>
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
                    <div class="toast-body small fw-medium">${msg}</div>
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
