// SkillSphere PWA Installation & Service Worker Registration Engine

(function() {
    'use strict';

    let deferredPrompt = null;
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isStandalone = window.navigator.standalone === true || window.matchMedia('(display-mode: standalone)').matches;

    // 1. Service Worker Registration
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/sw.js', { scope: '/' })
                .then((registration) => {
                    console.log('[PWA] Service Worker registered successfully with scope:', registration.scope);
                })
                .catch((err) => {
                    console.warn('[PWA] Service Worker registration failed:', err);
                });
        });
    }

    // If already running as standalone app, don't show install buttons
    if (isStandalone) {
        document.documentElement.classList.add('is-pwa-standalone');
        return;
    }

    // 2. Global Install Trigger
    window.triggerPWAInstall = function() {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('[PWA] User accepted the install prompt');
                    hideInstallUI();
                } else {
                    console.log('[PWA] User dismissed the install prompt');
                }
                deferredPrompt = null;
            });
        } else if (isIOS) {
            showIOSInstallModal();
        } else {
            // Android / Desktop fallback if prompt already fired or not yet fired
            const banner = document.getElementById('pwaInstallBanner');
            if (banner) banner.classList.remove('d-none');
            alert('To install SkillSphere:\n• Chrome/Edge: Tap menu (⋮) and select "Install App" or "Add to Home screen"\n• Safari: Tap Share (⎋) and select "Add to Home Screen"');
        }
    };

    function showInstallUI() {
        const installBtns = document.querySelectorAll('.pwa-install-trigger');
        installBtns.forEach(btn => {
            btn.classList.remove('d-none');
            btn.style.display = 'inline-flex';
        });

        // Show floating install snackbar if not previously dismissed in session
        if (!sessionStorage.getItem('pwa_banner_dismissed')) {
            const banner = document.getElementById('pwaInstallBanner');
            if (banner) {
                banner.classList.remove('d-none');
            }
        }
    }

    function hideInstallUI() {
        const installBtns = document.querySelectorAll('.pwa-install-trigger');
        installBtns.forEach(btn => {
            btn.classList.add('d-none');
            btn.style.display = 'none';
        });
        const banner = document.getElementById('pwaInstallBanner');
        if (banner) {
            banner.classList.add('d-none');
        }
    }

    function showIOSInstallModal() {
        const modal = document.getElementById('iosInstallModal');
        if (modal && typeof bootstrap !== 'undefined') {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        } else {
            alert('To install SkillSphere on your iPhone/iPad:\n1. Tap the Share button at the bottom of Safari (box with up arrow).\n2. Scroll down and tap "Add to Home Screen".');
        }
    }

    // 3. Listen for Chromium beforeinstallprompt
    window.addEventListener('beforeinstallprompt', (e) => {
        // Prevent default mini-infobar on mobile Chrome
        e.preventDefault();
        deferredPrompt = e;
        showInstallUI();
    });

    // 4. Handle iOS Safari Detection
    if (isIOS && !isStandalone) {
        window.addEventListener('DOMContentLoaded', () => {
            showInstallUI();
        });
    }

    // 5. Handle Post-Installation
    window.addEventListener('appinstalled', () => {
        console.log('[PWA] SkillSphere App was installed successfully');
        hideInstallUI();
        deferredPrompt = null;
    });

    // 6. Dismiss handler for banner
    window.dismissPWABanner = function() {
        sessionStorage.setItem('pwa_banner_dismissed', 'true');
        const banner = document.getElementById('pwaInstallBanner');
        if (banner) {
            banner.classList.add('d-none');
        }
    };

    // 7. Real-time Network Connectivity Monitoring
    function updateNetworkStatus(online) {
        const pill = document.getElementById('networkStatusPill');
        const text = document.getElementById('networkStatusText');
        if (!pill || !text) return;

        if (!online) {
            pill.className = 'position-fixed bottom-0 start-0 m-3 px-3 py-2 rounded-pill small fw-semibold shadow-lg d-flex align-items-center gap-2 text-warning';
            pill.style.background = 'rgba(26, 20, 8, 0.94)';
            pill.style.border = '1px solid rgba(245, 158, 11, 0.45)';
            pill.style.zIndex = '1060';
            pill.style.fontSize = '0.78rem';
            pill.style.backdropFilter = 'blur(10px)';
            const dot = pill.querySelector('.status-indicator-dot');
            if (dot) dot.style.background = '#f59e0b';
            text.innerHTML = '<span>Offline Mode — Cached lessons & resources remain accessible</span>';
            pill.classList.remove('d-none');
        } else {
            if (!pill.classList.contains('d-none')) {
                pill.className = 'position-fixed bottom-0 start-0 m-3 px-3 py-2 rounded-pill small fw-semibold shadow-lg d-flex align-items-center gap-2 text-success';
                pill.style.background = 'rgba(6, 30, 20, 0.94)';
                pill.style.border = '1px solid rgba(16, 185, 129, 0.45)';
                const dot = pill.querySelector('.status-indicator-dot');
                if (dot) dot.style.background = '#10b981';
                text.innerHTML = '<span>Back Online — Connected to SkillSphere cloud</span>';
                setTimeout(() => {
                    pill.classList.add('d-none');
                }, 3500);
            }
        }
    }

    window.addEventListener('offline', () => updateNetworkStatus(false));
    window.addEventListener('online', () => updateNetworkStatus(true));
    if (typeof navigator !== 'undefined' && !navigator.onLine) {
        window.addEventListener('DOMContentLoaded', () => updateNetworkStatus(false));
    }

})();
