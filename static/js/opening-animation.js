/**
 * SkillSphere Cinematic Opening Splash Animation Controller
 * Handles 3D orbital animation, ambient particle canvas, session memory,
 * keyboard accessibility (Esc to skip), and replay triggers.
 */
(function() {
    'use strict';

    const STORAGE_KEY = 'skillsphere_intro_shown_v1';
    let canvasAnimationId = null;
    let isDismissed = false;

    function shouldPlayIntro() {
        // 1. URL override (e.g. ?intro=1 or ?splash=1)
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('intro') || urlParams.has('splash')) {
            return true;
        }

        // 2. Accessibility check
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            return false;
        }

        // 3. Session storage check (plays once per browser tab session)
        try {
            return !sessionStorage.getItem(STORAGE_KEY);
        } catch (e) {
            return false;
        }
    }

    function initCanvas(canvas) {
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight;

        const handleResize = () => {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        };
        window.addEventListener('resize', handleResize);

        // Generate subtle floating star dust particles
        const particleCount = Math.min(45, Math.floor(width / 30));
        const particles = [];
        const colors = ['#6366F1', '#38BDF8', '#8B5CF6', '#F43F5E', '#C7D2FE'];

        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                radius: Math.random() * 1.8 + 0.6,
                color: colors[Math.floor(Math.random() * colors.length)],
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                alpha: Math.random() * 0.6 + 0.2
            });
        }

        function render() {
            if (isDismissed) return;
            ctx.clearRect(0, 0, width, height);

            for (let i = 0; i < particles.length; i++) {
                const p = particles[i];
                p.x += p.vx;
                p.y += p.vy;

                if (p.x < 0) p.x = width;
                if (p.x > width) p.x = 0;
                if (p.y < 0) p.y = height;
                if (p.y > height) p.y = 0;

                ctx.save();
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = p.color;
                ctx.globalAlpha = p.alpha;
                ctx.shadowBlur = p.radius * 3;
                ctx.shadowColor = p.color;
                ctx.fill();
                ctx.restore();
            }

            canvasAnimationId = requestAnimationFrame(render);
        }

        canvasAnimationId = requestAnimationFrame(render);
    }

    function dismissSplash(fast) {
        if (isDismissed) return;
        isDismissed = true;

        const splashEl = document.getElementById('skillsphereIntroSplash');
        if (!splashEl) return;

        try {
            sessionStorage.setItem(STORAGE_KEY, 'true');
        } catch (e) {}

        if (canvasAnimationId) {
            cancelAnimationFrame(canvasAnimationId);
            canvasAnimationId = null;
        }

        if (fast) {
            splashEl.classList.add('splash-hidden');
            return;
        }

        splashEl.classList.add('splash-hiding');
        setTimeout(() => {
            splashEl.classList.add('splash-hidden');
        }, 440);
    }

    function playIntro() {
        const splashEl = document.getElementById('skillsphereIntroSplash');
        if (!splashEl) return;

        isDismissed = false;
        splashEl.classList.remove('splash-hidden', 'splash-hiding');

        const canvas = document.getElementById('splashStarsCanvas');
        if (canvas) {
            initCanvas(canvas);
        }

        const progressEl = document.getElementById('splashProgressFill');
        if (progressEl) {
            progressEl.style.width = '0%';
            setTimeout(() => {
                progressEl.style.width = '100%';
            }, 100);
        }

        // Auto dismiss smoothly after 1450ms
        setTimeout(() => {
            dismissSplash(false);
        }, 1450);
    }

    // Expose global methods
    window.dismissSkillSphereSplash = function(fast) {
        dismissSplash(fast);
    };

    window.playSkillSphereIntro = function() {
        playIntro();
    };

    // Auto-initialize on DOM ready
    function init() {
        const splashEl = document.getElementById('skillsphereIntroSplash');
        if (!splashEl) return;

        if (shouldPlayIntro()) {
            playIntro();
        } else {
            // Already viewed in session -> hide immediately with zero layout shift
            splashEl.classList.add('splash-hidden');
        }

        // ESC key dismisses immediately
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                dismissSplash(true);
            }
        });

        // Clicking anywhere on splash overlay dismisses
        splashEl.addEventListener('click', (e) => {
            if (!e.target.closest('.splash-skip-btn')) {
                dismissSplash(false);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
