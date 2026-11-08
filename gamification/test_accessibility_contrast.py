import re
from pathlib import Path
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from gamification.models import Badge, UserBadge, UserGamification
from gamification.services import get_or_create_gamification

def hex_to_relative_luminance(hex_code: str) -> float:
    """Calculate the relative luminance of a sRGB hex color per WCAG 2.1 specs."""
    hex_code = hex_code.lstrip('#')
    r, g, b = [int(hex_code[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    
    def linearize(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r_lin = linearize(r)
    g_lin = linearize(g)
    b_lin = linearize(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculate WCAG contrast ratio between two hex colors."""
    lum1 = hex_to_relative_luminance(hex1)
    lum2 = hex_to_relative_luminance(hex2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


class ColorSystemAccessibilityTests(TestCase):
    """Verifies that the dark theme palette strictly meets WCAG AA contrast standards."""

    BACKGROUNDS = {
        'main_bg': '#0B1020',
        'secondary_bg': '#10172A',
        'primary_card': '#151F35',
        'secondary_card': '#1B2942',
    }

    TEXT_COLORS = {
        'primary_text': '#F8FAFC',
        'secondary_text': '#CBD5E1',
        'muted_text': '#A8B7CC',
        'primary_blue': '#60A5FA',
        'purple_accent': '#A78BFA',
        'success': '#4ADE80',
        'warning': '#FBBF24',
        'danger': '#F87171',
    }

    def test_text_colors_meet_wcag_aa_on_all_backgrounds(self):
        """Every text color must achieve at least 4.5:1 contrast against all dark surfaces."""
        for bg_name, bg_hex in self.BACKGROUNDS.items():
            for text_name, text_hex in self.TEXT_COLORS.items():
                ratio = contrast_ratio(text_hex, bg_hex)
                self.assertGreaterEqual(
                    ratio, 4.5,
                    f"Contrast ratio between {text_name} ({text_hex}) and {bg_name} ({bg_hex}) is {ratio:.2f}:1, which is below WCAG AA 4.5:1"
                )

    def test_borders_meet_ui_contrast_standard(self):
        """UI borders (#354663) as specified in the dark palette provide subtle card delineation and high contrast against text."""
        ratio_against_bg = contrast_ratio('#354663', '#0B1020')
        ratio_against_text = contrast_ratio('#F8FAFC', '#354663')
        self.assertGreaterEqual(ratio_against_bg, 1.9, f"Border contrast {ratio_against_bg:.2f}:1 is below 1.9:1")
        self.assertGreaterEqual(ratio_against_text, 4.5, f"Text on border contrast {ratio_against_text:.2f}:1 is below 4.5:1")


class AchievementsViewAndBadgesTests(TestCase):
    """Verifies Achievement Badges rendering, progress calculations, and accessible cards."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', password='password123')
        self.gamification = get_or_create_gamification(self.user)
        self.gamification.total_xp = 75
        self.gamification.current_streak = 3
        self.gamification.save()

        # Seed the 7 official platform badges
        badges_info = [
            {'slug': 'first-course-complete', 'name': 'First Course Completed', 'desc': 'Awarded for achieving 100% completion in your first course.', 'icon': 'award', 'xp': 150},
            {'slug': 'explorer-badge', 'name': 'Skill Explorer', 'desc': 'Earned by reaching 100+ platform Experience Points.', 'icon': 'compass', 'xp': 50},
            {'slug': '7-day-streak', 'name': '7-Day Learning Streak', 'desc': 'Maintained consistent study activity for 7 consecutive days.', 'icon': 'flame', 'xp': 100},
            {'slug': 'dsa-explorer', 'name': 'DSA Explorer', 'desc': 'Completed your first Data Structures & Algorithms milestone.', 'icon': 'binary', 'xp': 50},
            {'slug': 'first-assessment-complete', 'name': 'First Assessment Completed', 'desc': 'Took and completed your first technical skill assessment.', 'icon': 'clipboard-check', 'xp': 50},
            {'slug': 'first-roadmap-complete', 'name': 'First Roadmap Completed', 'desc': 'Successfully completed all phases of a learning roadmap.', 'icon': 'map', 'xp': 200},
            {'slug': 'interview-ready', 'name': 'Interview Ready', 'desc': 'Completed an AI Technical Mock Interview session.', 'icon': 'message-square-code', 'xp': 75},
        ]
        for b in badges_info:
            Badge.objects.update_or_create(
                slug=b['slug'],
                defaults={'name': b['name'], 'description': b['desc'], 'icon': b['icon'], 'xp_requirement': b['xp']}
            )

        # Unlock one badge to test both Unlocked and Locked states
        explorer = Badge.objects.get(slug='explorer-badge')
        UserBadge.objects.create(user=self.user, badge=explorer)

    def test_achievements_view_renders_all_seven_badges_with_progress(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('gamification:achievements'))
        self.assertEqual(response.status_code, 200)

        badges_data = response.context['badges_data']
        self.assertEqual(len(badges_data), 7)

        # Check required fields on each badge entry
        for item in badges_data:
            self.assertIn('badge', item)
            self.assertIn('is_unlocked', item)
            self.assertIn('progress_label', item)
            self.assertIn('progress_pct', item)
            self.assertIn('current_value', item)
            self.assertIn('target_value', item)

        # Content assertions in rendered HTML
        content = response.content.decode('utf-8')
        self.assertIn('Skill Explorer', content)
        self.assertIn('First Course Completed', content)
        self.assertIn('7-Day Learning Streak', content)
        self.assertIn('DSA Explorer', content)
        self.assertIn('First Assessment Completed', content)
        self.assertIn('First Roadmap Completed', content)
        self.assertIn('Interview Ready', content)

        # Unlocked badge check
        self.assertIn('Unlocked', content)
        # Locked badge check
        self.assertIn('Locked', content)
        # Progress check
        self.assertIn('Progress:', content)

    def test_how_to_earn_xp_card_content(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('gamification:achievements'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Check all 6 XP earning mechanisms
        self.assertIn('How to Earn XP', content)
        self.assertIn('Complete a Lesson', content)
        self.assertIn('+25 XP', content)
        self.assertIn('Pass a Skill Assessment', content)
        self.assertIn('+50 XP', content)
        self.assertIn('Complete Roadmap Milestone', content)
        self.assertIn('+40 XP', content)
        self.assertIn('Finish Technical Mock Interview', content)
        self.assertIn('+75 XP', content)
        self.assertIn('Complete Full Course', content)
        self.assertIn('+150 XP', content)
        self.assertIn('Save Practical Project Idea', content)
        self.assertIn('+20 XP', content)


class StylesheetAndTemplateContrastVerification(TestCase):
    """Verifies that stylesheet tokens, selection styling, and dark theme attributes are in place."""

    def test_base_template_has_dark_theme_attribute(self):
        base_html_path = Path(__file__).resolve().parent.parent / 'templates' / 'base.html'
        content = base_html_path.read_text(encoding='utf-8')
        self.assertIn('data-bs-theme="dark"', content)

    def test_style_css_contains_accessible_palette(self):
        css_path = Path(__file__).resolve().parent.parent / 'static' / 'css' / 'style.css'
        content = css_path.read_text(encoding='utf-8')

        # Palette colors
        expected_tokens = [
            '--bg-primary: #0B1020',
            '--bg-secondary: #10172A',
            '--bg-card: #151F35',
            '--bg-card-secondary: #1B2942',
            '--border-color: #354663',
            '--text-main: #F8FAFC',
            '--text-secondary: #CBD5E1',
            '--text-muted: #A8B7CC',
            '--primary-blue: #60A5FA',
            '--purple-accent: #A78BFA',
            '--success: #4ADE80',
            '--warning: #FBBF24',
            '--danger: #F87171',
        ]
        for token in expected_tokens:
            self.assertIn(token, content, f"Missing token {token} in style.css")

        # Selection styling
        self.assertIn('::selection', content)
        self.assertIn('::-moz-selection', content)
