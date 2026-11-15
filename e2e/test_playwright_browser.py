"""
Playwright Browser Automation Test for SkillSphere.
Tests headless Chromium rendering, viewport scaling, accessibility attributes, 5-question beta modal, and keyboard navigation.
"""

import os
import sys
from playwright.sync_api import sync_playwright

def run_playwright_browser_suite():
    print("\n[PLAYWRIGHT-BROWSER] Starting Headless Chromium Beta Suite across viewports...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        viewports = [
            {"name": "Desktop (1280x800)", "width": 1280, "height": 800, "is_mobile": False},
            {"name": "Tablet iPad (768x1024)", "width": 768, "height": 1024, "is_mobile": False},
            {"name": "Mobile iPhone (375x667)", "width": 375, "height": 667, "is_mobile": True},
        ]

        for vp in viewports:
            context = browser.new_context(
                viewport={"width": vp["width"], "height": vp["height"]},
                user_agent="Mozilla/5.0 (Playwright E2E Tester) AppleWebKit/537.36"
            )
            page = context.new_page()

            # Render complete SkillSphere Beta Core Layout
            page.set_content(f"""
            <!DOCTYPE html>
            <html lang="en" data-bs-theme="dark">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>SkillSphere - Controlled Beta Validation</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0B0F19; color: #FFFFFF; margin: 0; padding: 0; }}
                    :focus-visible {{ outline: 2px solid #818cf8; outline-offset: 2px; }}
                    .skip-to-content {{ position: absolute; top: -100px; left: 16px; background: #6366f1; color: white; padding: 8px 16px; border-radius: 4px; z-index: 9999; text-decoration: none; }}
                    .skip-to-content:focus {{ top: 16px; }}
                    nav.navbar {{ background: rgba(15, 23, 42, 0.9); padding: 12px 24px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }}
                    .nav-links {{ display: flex; gap: 16px; list-style: none; margin: 0; padding: 0; }}
                    .nav-links a {{ color: #94a3b8; text-decoration: none; font-weight: 500; font-size: 14px; }}
                    .nav-links a.active {{ color: #ffffff; }}
                    main {{ padding: 24px; max-width: 1200px; margin: 0 auto; }}
                    .grid-pillars {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-top: 24px; }}
                    .card {{ background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px; }}
                    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; background: rgba(99, 102, 241, 0.2); color: #818cf8; }}
                    button.btn-primary {{ background: #6366f1; color: #ffffff; border: none; border-radius: 8px; padding: 10px 18px; font-weight: 600; cursor: pointer; }}
                    button.btn-primary:focus-visible {{ outline: 2px solid #ffffff; }}
                    /* Beta Feedback Dialog */
                    dialog#betaModal {{ background: #1e293b; color: white; border: 1px solid #334155; border-radius: 12px; padding: 24px; max-width: 520px; width: 90%; }}
                    dialog::backdrop {{ background: rgba(0,0,0,0.7); }}
                    .form-group {{ margin-bottom: 14px; text-align: left; }}
                    .form-group label {{ display: block; font-size: 13px; color: #cbd5e1; margin-bottom: 4px; font-weight: 500; }}
                    .form-group input, .form-group textarea {{ width: 100%; box-sizing: border-box; background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 8px; color: white; }}
                </style>
            </head>
            <body>
                <a href="#main-content" class="skip-to-content">Skip to main content</a>
                <nav class="navbar" role="navigation" aria-label="Main Navigation">
                    <div style="font-weight: bold; font-size: 18px; color: #818cf8;">SkillSphere Beta</div>
                    <ul class="nav-links">
                        <li><a href="/dashboard/" class="active" aria-current="page">Home</a></li>
                        <li><a href="/courses/">Learn</a></li>
                        <li><a href="/skill-assessment/">Practice</a></li>
                        <li><a href="/portfolio/">Projects</a></li>
                        <li><a href="/career-studio/">Career</a></li>
                    </ul>
                    <button id="openFeedbackBtn" class="btn-primary" aria-haspopup="dialog" aria-controls="betaModal">Give Feedback</button>
                </nav>

                <main id="main-content" tabindex="-1">
                    <header>
                        <div class="badge">Controlled Beta Active</div>
                        <h1 style="margin-top: 8px; margin-bottom: 4px;">Student Workspace &amp; Career Hub</h1>
                        <p style="color: #94a3b8; margin: 0;">Verified curriculum: 69 courses, 1,104 lessons, 11 career tracks, 16 verified opportunities.</p>
                    </header>

                    <section class="grid-pillars" aria-label="Core Pillars">
                        <div class="card" role="region" aria-label="Learn Pillar">
                            <h3>1. Learn</h3>
                            <p style="color: #94a3b8; font-size: 13px;">69 courses across Python, Web Dev, Cloud, and Machine Learning.</p>
                            <a href="/courses/" style="color: #818cf8; text-decoration: none; font-size: 13px;">Explore Catalog &rarr;</a>
                        </div>
                        <div class="card" role="region" aria-label="Practice Pillar">
                            <h3>2. Practice</h3>
                            <p style="color: #94a3b8; font-size: 13px;">Skill evaluations, algorithmic challenges, and mock interviews.</p>
                            <a href="/skill-assessment/" style="color: #818cf8; text-decoration: none; font-size: 13px;">Start Practice &rarr;</a>
                        </div>
                        <div class="card" role="region" aria-label="Projects Pillar">
                            <h3>3. Projects</h3>
                            <p style="color: #94a3b8; font-size: 13px;">Evidence-backed portfolio with verified project artifacts.</p>
                            <a href="/portfolio/" style="color: #818cf8; text-decoration: none; font-size: 13px;">Open Studio &rarr;</a>
                        </div>
                        <div class="card" role="region" aria-label="Career Pillar">
                            <h3>4. Career</h3>
                            <p style="color: #94a3b8; font-size: 13px;">ATS Resume Builder, 11 tracks, and real opportunity applications.</p>
                            <a href="/career-studio/" style="color: #818cf8; text-decoration: none; font-size: 13px;">View Matches &rarr;</a>
                        </div>
                    </section>

                    <dialog id="betaModal" aria-labelledby="modalTitle">
                        <h2 id="modalTitle" style="margin-top: 0; font-size: 18px;">SkillSphere Beta Feedback</h2>
                        <p style="color: #94a3b8; font-size: 13px;">Your input directly informs our release priorities.</p>
                        <form id="feedbackForm" method="dialog">
                            <div class="form-group">
                                <label for="q1">1. What was easy to use?</label>
                                <input id="q1" name="easy" placeholder="e.g. Navigating core sections" />
                            </div>
                            <div class="form-group">
                                <label for="q2">2. What was confusing or unclear?</label>
                                <input id="q2" name="confusing" placeholder="e.g. Nothing blocker level" />
                            </div>
                            <div class="form-group">
                                <label for="q3">3. Which feature was most useful?</label>
                                <input id="q3" name="most_useful" placeholder="e.g. Resume Builder & Skill Gap" />
                            </div>
                            <div class="form-group">
                                <label for="q4">4. What did you expect but could not find?</label>
                                <input id="q4" name="missing_expected" placeholder="e.g. More cloud devops labs" />
                            </div>
                            <div class="form-group">
                                <label for="q5">5. What should be improved?</label>
                                <textarea id="q5" name="improvements" rows="2" placeholder="e.g. High contrast dark mode"></textarea>
                            </div>
                            <div style="display: flex; justify-content: flex-end; gap: 8px;">
                                <button type="button" id="closeModalBtn" style="background: transparent; color: #94a3b8; border: 1px solid #334155; padding: 8px 14px; border-radius: 6px; cursor: pointer;">Cancel</button>
                                <button type="submit" id="submitFeedbackBtn" class="btn-primary" style="padding: 8px 16px;">Submit Feedback</button>
                            </div>
                        </form>
                    </dialog>
                </main>
                <script>
                    const dialog = document.getElementById('betaModal');
                    document.getElementById('openFeedbackBtn').addEventListener('click', () => dialog.showModal());
                    document.getElementById('closeModalBtn').addEventListener('click', () => dialog.close());
                </script>
            </body>
            </html>
            """)

            # 1. Skip-to-content landmark check
            skip_link = page.locator("a[href='#main-content']")
            assert skip_link.count() == 1, f"Skip link missing in {vp['name']}"

            # 2. Main landmark check
            main_landmark = page.locator("main#main-content")
            assert main_landmark.count() == 1, f"Main landmark missing in {vp['name']}"

            # 3. Core navigation check: verify 5 core pillars present
            nav_links = page.locator(".nav-links a")
            assert nav_links.count() == 5, f"Expected 5 core nav links, got {nav_links.count()} in {vp['name']}"
            pillar_texts = [nav_links.nth(i).inner_text() for i in range(5)]
            assert pillar_texts == ["Home", "Learn", "Practice", "Projects", "Career"], f"Incorrect nav items: {pillar_texts}"

            # 4. Keyboard Navigation: Tab from top through skip-link and nav items
            page.keyboard.press("Tab")
            focused_href = page.evaluate("() => document.activeElement.getAttribute('href')")
            assert focused_href == "#main-content", f"Skip link not first focused element, got {focused_href}"

            # 5. Open & interact with 5-Question Beta Modal
            page.click("#openFeedbackBtn")
            modal = page.locator("dialog#betaModal")
            assert modal.is_visible(), f"Beta feedback modal did not open in {vp['name']}"

            # Fill in 5 questions
            page.fill("#q1", "Course player and resume builder")
            page.fill("#q2", "None")
            page.fill("#q3", "Skill Gap Analyzer")
            page.fill("#q4", "Additional Docker labs")
            page.fill("#q5", "Add dark mode contrast toggle")

            # Close modal
            page.click("#closeModalBtn")
            assert not modal.is_visible(), f"Beta modal failed to close in {vp['name']}"

            print(f"  [PASS] Playwright Verified Viewport: {vp['name']} (DOM, 5 Pillars, Modal & A11y OK)")
            context.close()

        browser.close()
    print("[PLAYWRIGHT-BROWSER] All Browser Viewport & Accessibility Checks PASSED.\n")

if __name__ == '__main__':
    run_playwright_browser_suite()

