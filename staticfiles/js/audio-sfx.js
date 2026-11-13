/**
 * SkillSphere Web Audio SFX Engine
 * Zero external asset dependencies. Synthesizes crisp acoustic and haptic sound effects
 * using standard HTML5 AudioContext oscillators and gain envelopes.
 */
(function() {
    let audioCtx = null;
    let sfxEnabled = localStorage.getItem('skillsphere_sfx_enabled') !== 'false'; // default true

    function getAudioContext() {
        if (!audioCtx) {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (AudioContextClass) {
                audioCtx = new AudioContextClass();
            }
        }
        if (audioCtx && audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        return audioCtx;
    }

    const SFX = {
        isEnabled() {
            return sfxEnabled;
        },
        toggle() {
            sfxEnabled = !sfxEnabled;
            localStorage.setItem('skillsphere_sfx_enabled', sfxEnabled ? 'true' : 'false');
            this.updateUi();
            if (sfxEnabled) {
                this.play('success');
            }
            return sfxEnabled;
        },
        set(enabled) {
            sfxEnabled = !!enabled;
            localStorage.setItem('skillsphere_sfx_enabled', sfxEnabled ? 'true' : 'false');
            this.updateUi();
        },
        updateUi() {
            const toggleBtns = document.querySelectorAll('.sfx-toggle-btn');
            toggleBtns.forEach(btn => {
                const icon = btn.querySelector('[data-lucide]') || btn.querySelector('i');
                if (sfxEnabled) {
                    btn.classList.add('text-primary');
                    btn.classList.remove('text-muted');
                    btn.setAttribute('title', 'Sound Effects: ON (Click to mute)');
                } else {
                    btn.classList.remove('text-primary');
                    btn.classList.add('text-muted');
                    btn.setAttribute('title', 'Sound Effects: OFF (Click to unmute)');
                }
            });
            if (window.lucide) lucide.createIcons();
        },
        play(soundName) {
            if (!sfxEnabled) return;
            const ctx = getAudioContext();
            if (!ctx) return;

            const now = ctx.currentTime;

            try {
                if (soundName === 'click') {
                    // Subtle UI tap
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(600, now);
                    osc.frequency.exponentialRampToValueAtTime(200, now + 0.04);
                    gain.gain.setValueAtTime(0.08, now);
                    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start(now);
                    osc.stop(now + 0.04);
                } else if (soundName === 'success' || soundName === 'complete') {
                    // Pleasant ascending major triad chime (C5 -> E5 -> G5)
                    const freqs = [523.25, 659.25, 783.99];
                    freqs.forEach((freq, idx) => {
                        const noteOsc = ctx.createOscillator();
                        const noteGain = ctx.createGain();
                        noteOsc.type = 'triangle';
                        noteOsc.frequency.setValueAtTime(freq, now + (idx * 0.07));
                        noteGain.gain.setValueAtTime(0.001, now + (idx * 0.07));
                        noteGain.gain.exponentialRampToValueAtTime(0.12, now + (idx * 0.07) + 0.02);
                        noteGain.gain.exponentialRampToValueAtTime(0.001, now + (idx * 0.07) + 0.28);
                        noteOsc.connect(noteGain);
                        noteGain.connect(ctx.destination);
                        noteOsc.start(now + (idx * 0.07));
                        noteOsc.stop(now + (idx * 0.07) + 0.28);
                    });
                } else if (soundName === 'victory') {
                    // Triumphant duel victory fanfare (G4 -> C5 -> E5 -> G5 sustain)
                    const melody = [
                        { f: 392.00, t: 0.00, d: 0.10 },
                        { f: 523.25, t: 0.10, d: 0.10 },
                        { f: 659.25, t: 0.20, d: 0.12 },
                        { f: 783.99, t: 0.32, d: 0.45 },
                    ];
                    melody.forEach(note => {
                        const osc = ctx.createOscillator();
                        const gain = ctx.createGain();
                        osc.type = 'sine';
                        osc.frequency.setValueAtTime(note.f, now + note.t);
                        gain.gain.setValueAtTime(0.001, now + note.t);
                        gain.gain.linearRampToValueAtTime(0.15, now + note.t + 0.03);
                        gain.gain.exponentialRampToValueAtTime(0.001, now + note.t + note.d);
                        osc.connect(gain);
                        gain.connect(ctx.destination);
                        osc.start(now + note.t);
                        osc.stop(now + note.t + note.d);
                    });
                } else if (soundName === 'combo') {
                    // High-energy combo pitch slide
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(440, now);
                    osc.frequency.exponentialRampToValueAtTime(880, now + 0.12);
                    gain.gain.setValueAtTime(0.06, now);
                    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start(now);
                    osc.stop(now + 0.14);
                } else if (soundName === 'patch') {
                    // Socratic code patch apply chime
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(880, now);
                    osc.frequency.exponentialRampToValueAtTime(1174.66, now + 0.08);
                    gain.gain.setValueAtTime(0.09, now);
                    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start(now);
                    osc.stop(now + 0.15);
                } else if (soundName === 'error') {
                    // Low gentle thud
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = 'square';
                    osc.frequency.setValueAtTime(150, now);
                    osc.frequency.exponentialRampToValueAtTime(80, now + 0.15);
                    gain.gain.setValueAtTime(0.08, now);
                    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start(now);
                    osc.stop(now + 0.15);
                }
            } catch (err) {
                console.debug("Audio SFX play muted/blocked:", err);
            }
        }
    };

    window.SkillSphereSFX = SFX;
    document.addEventListener('DOMContentLoaded', () => SFX.updateUi());
})();
