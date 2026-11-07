import json
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse

from services.ai_service import (
    AIService,
    validate_roadmap_schema,
    validate_interview_schema,
    validate_project_schema,
    validate_ats_schema,
)
from assistant.models import AIConversation, AIMessage


class GeminiCascadeProductionTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_gemini_models_cascade_configuration(self):
        """Verify the model cascade contains officially supported Gemini models."""
        cascade = AIService.get_gemini_models_cascade()
        self.assertIsInstance(cascade, list)
        self.assertGreaterEqual(len(cascade), 3)
        self.assertEqual(cascade[0], 'gemini-3.8-flash')
        self.assertEqual(cascade[1], 'gemini-3.6-flash')
        self.assertEqual(cascade[2], 'gemini-3.5-flash-lite')

    @patch('services.ai_service.AIService._call_gemini_single')
    def test_gemini_cascade_success_on_primary(self, mock_single):
        """Primary model (gemini-3.8-flash) responds successfully."""
        mock_single.return_value = ('Primary model response', 200, None, False)

        res = AIService._call_gemini("Test prompt")
        self.assertIsNotNone(res)
        self.assertEqual(res['model'], 'gemini-3.8-flash')
        self.assertEqual(res['text'], 'Primary model response')
        self.assertEqual(mock_single.call_count, 1)

    @patch('services.ai_service.time.sleep', return_value=None)
    @patch('services.ai_service.AIService._call_gemini_single')
    def test_gemini_cascade_fallback_on_transient_error(self, mock_single, mock_sleep):
        """Primary model fails with 503; cascade shifts to gemini-3.6-flash."""
        def side_effect(model, api_key, data_bytes, timeout):
            if model == 'gemini-3.8-flash':
                return (None, 503, "503 Service Unavailable", False)
            return ('Fallback response from 3.6', 200, None, False)

        mock_single.side_effect = side_effect

        res = AIService._call_gemini("Test prompt")
        self.assertIsNotNone(res)
        self.assertEqual(res['model'], 'gemini-3.6-flash')
        self.assertEqual(res['text'], 'Fallback response from 3.6')

    @patch('services.ai_service.time.sleep', return_value=None)
    @patch('services.ai_service.AIService._call_gemini_single')
    def test_gemini_cascade_permanent_error_aborts_without_retry(self, mock_single, mock_sleep):
        """Permanent failure (401 / 403 / 400) immediately aborts without retrying or calling fallbacks."""
        mock_single.return_value = (None, 401, "401 Invalid API Key", True)

        res = AIService._call_gemini("Test prompt")
        self.assertIsNone(res)
        # Should call only 1 time for the first model and stop immediately
        self.assertEqual(mock_single.call_count, 1)
        mock_sleep.assert_not_called()


class StructuredJSONValidationTests(TestCase):
    def test_roadmap_schema_validator(self):
        """Strict validation of roadmap phase schema, week bounds, and key types."""
        valid_roadmap = [
            {
                "title": "Phase 1: Foundations",
                "description": "Learn syntax and basic constructs",
                "topics": ["Variables", "Loops", "Functions"],
                "mini_project": "CLI Calculator",
                "estimated_weeks": 2
            },
            {
                "title": "Phase 2: Advanced OOP",
                "description": "Master inheritance and design patterns",
                "topics": ["Classes", "Dunder methods", "Composition"],
                "mini_project": "Bank Account Manager",
                "estimated_weeks": 3
            },
            {
                "title": "Phase 3: Production Deployment",
                "description": "Learn packaging, docker, and cloud deployment",
                "topics": ["Docker", "CI/CD", "Monitoring"],
                "mini_project": "Cloud Microservice",
                "estimated_weeks": 4
            }
        ]
        is_valid, err = validate_roadmap_schema(valid_roadmap)
        self.assertTrue(is_valid, msg=err)

        # Invalid: missing mini_project
        invalid_roadmap = [
            {
                "title": "Phase 1",
                "description": "Desc",
                "topics": ["Topic 1", "Topic 2"],
                "estimated_weeks": 2
            },
            {
                "title": "Phase 2",
                "description": "Desc 2",
                "topics": ["Topic 2A", "Topic 2B"],
                "estimated_weeks": 2
            },
            {
                "title": "Phase 3",
                "description": "Desc 3",
                "topics": ["Topic 3A", "Topic 3B"],
                "estimated_weeks": 2
            }
        ]
        is_valid, err = validate_roadmap_schema(invalid_roadmap)
        self.assertFalse(is_valid)
        self.assertIn("missing a valid 'mini_project'", err)

        # Invalid: estimated_weeks > 16
        invalid_weeks = [
            {
                "title": "Phase 1",
                "description": "Desc",
                "topics": ["Topic 1", "Topic 2"],
                "mini_project": "Project",
                "estimated_weeks": 52
            },
            {
                "title": "Phase 2",
                "description": "Desc 2",
                "topics": ["Topic 2A", "Topic 2B"],
                "mini_project": "Project 2",
                "estimated_weeks": 2
            },
            {
                "title": "Phase 3",
                "description": "Desc 3",
                "topics": ["Topic 3A", "Topic 3B"],
                "mini_project": "Project 3",
                "estimated_weeks": 2
            }
        ]
        is_valid, err = validate_roadmap_schema(invalid_weeks)
        self.assertFalse(is_valid)
        self.assertIn("must be between 1 and 16", err)

    def test_interview_schema_validator(self):
        """Strict validation of interview rubric rating 1-10 and feedback keys."""
        valid_interview = {
            "rating": 8,
            "technical_correctness": "Accurate explanation of indexing.",
            "clarity": "Logical flow and good terminology.",
            "constructive_feedback": "Mention composite indexes and write trade-offs.",
            "sample_ideal_answer": "Indexes use B-Trees to provide O(log n) lookup..."
        }
        is_valid, err = validate_interview_schema(valid_interview)
        self.assertTrue(is_valid, msg=err)

        # Invalid: rating out of range
        invalid_rating = dict(valid_interview)
        invalid_rating["rating"] = 15
        is_valid, err = validate_interview_schema(invalid_rating)
        self.assertFalse(is_valid)
        self.assertIn("Rating must be an integer between 1 and 10", err)

    def test_project_schema_validator(self):
        """Strict validation of project idea keys."""
        valid_project = {
            "title": "Real-Time Telemetry Dashboard",
            "description": "Full-stack monitoring solution for connected IoT sensors and microservices.",
            "problem_statement": "Managing high-velocity time-series data without dropping messages or UI stalls.",
            "objectives": "Build a scalable ingestion pipeline and reactive streaming dashboard.",
            "technology_stack": "Django Channels, Redis, PostgreSQL, Chart.js, Docker",
            "main_features": "Live sensor streaming, anomaly alert thresholding, automated daily health summaries.",
            "database_requirements": "Device, Reading, Alert, and TelemetryBatch relational models with indexed timestamps.",
            "development_phases": "Phase 1 Setup; Phase 2 Ingestion; Phase 3 WebSockets; Phase 4 Polishing.",
            "portfolio_tips": "Highlight the async consumer architecture and write load test metrics in README."
        }
        is_valid, err = validate_project_schema(valid_project)
        self.assertTrue(is_valid, msg=err)

        invalid_project = dict(valid_project)
        del invalid_project["development_phases"]
        is_valid, err = validate_project_schema(invalid_project)
        self.assertFalse(is_valid)
        self.assertIn("Missing required key 'development_phases'", err)

    def test_ats_schema_validator(self):
        """Strict validation of ATS resume score 0-100."""
        valid_ats = {
            "score": 85,
            "readability_status": "High",
            "strengths": ["Strong action verbs", "Clean formatting"],
            "improvements": ["Quantify results with metrics"],
            "keywords_matched": ["Python", "Django", "PostgreSQL"],
            "keywords_missing": ["Docker", "Kubernetes"],
            "format_feedback": "Use standard single column format",
            "summary_critique": "Solid headline and summary."
        }
        is_valid, err = validate_ats_schema(valid_ats)
        self.assertTrue(is_valid, msg=err)

        invalid_ats = dict(valid_ats)
        invalid_ats["score"] = 120
        is_valid, err = validate_ats_schema(invalid_ats)
        self.assertFalse(is_valid)
        self.assertIn("Score must be between 0 and 100", err)

    @patch('services.ai_service.AIService.generate_text_with_meta')
    def test_structured_json_repair_retry(self, mock_meta):
        """First call produces malformed JSON; repair retry succeeds with valid schema."""
        bad_json = "Here is the data: { invalid json"
        good_json = json.dumps({
            "rating": 9,
            "technical_correctness": "Excellent explanation.",
            "clarity": "Crystal clear.",
            "constructive_feedback": "None needed.",
            "sample_ideal_answer": "Top answer."
        })

        mock_meta.side_effect = [
            {'text': bad_json, 'provider': 'gemini', 'is_fallback': False},
            {'text': good_json, 'provider': 'gemini', 'is_fallback': False}
        ]

        def fallback():
            return {"rating": 5, "technical_correctness": "", "clarity": "", "constructive_feedback": "", "sample_ideal_answer": ""}

        data, meta = AIService.generate_structured_json(
            prompt="Evaluate candidate",
            system_instruction="Rubric instructions",
            validator_fn=validate_interview_schema,
            fallback_fn=fallback
        )

        self.assertEqual(mock_meta.call_count, 2)
        self.assertEqual(data["rating"], 9)
        self.assertEqual(data["clarity"], "Crystal clear.")

    @patch('services.ai_service.AIService.generate_text_with_meta')
    def test_structured_json_fallback_when_repair_also_fails(self, mock_meta):
        """Both attempts fail schema validation; clean fallback is returned without error."""
        bad_json = json.dumps({"incomplete": True})
        mock_meta.return_value = {'text': bad_json, 'provider': 'gemini', 'is_fallback': False}

        def fallback():
            return {
                "rating": 7,
                "technical_correctness": "Fallback valid explanation",
                "clarity": "Good clarity",
                "constructive_feedback": "Add trade-offs",
                "sample_ideal_answer": "Demonstrate STAR method"
            }

        data, meta = AIService.generate_structured_json(
            prompt="Evaluate candidate",
            system_instruction="Rubric",
            validator_fn=validate_interview_schema,
            fallback_fn=fallback
        )

        self.assertEqual(data["rating"], 7)
        self.assertTrue(meta["is_fallback"])
        self.assertEqual(meta["provider"], "offline-knowledge-engine")


class SecurityAndIsolationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user_a = User.objects.create_user(username='student_a', email='a@example.com', password='Password123!')
        self.user_b = User.objects.create_user(username='student_b', email='b@example.com', password='Password123!')

    def test_user_scoped_cache_keys(self):
        """User A and User B querying same prompt have completely isolated cache keys."""
        prompt = "Explain my resume ATS score"
        key_a = AIService._build_cache_key('ats_check', f"user_{self.user_a.id}", prompt)
        key_b = AIService._build_cache_key('ats_check', f"user_{self.user_b.id}", prompt)
        key_global = AIService._build_cache_key('concepts', 'global', prompt)

        self.assertNotEqual(key_a, key_b)
        self.assertIn(f"user_{self.user_a.id}", key_a)
        self.assertIn(f"user_{self.user_b.id}", key_b)
        self.assertIn("global", key_global)

    def test_rate_limiting_per_user(self):
        """Max 20 requests per minute allowed; 21st is blocked."""
        user_id = self.user_a.id
        for i in range(20):
            allowed, retry_after = AIService.check_rate_limit(user_id, max_per_minute=20)
            self.assertTrue(allowed, msg=f"Request {i+1} should be allowed")
            self.assertEqual(retry_after, 0)

        # 21st request must be blocked
        allowed, retry_after = AIService.check_rate_limit(user_id, max_per_minute=20)
        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)

    def test_chat_memory_retrieves_10_most_recent_messages(self):
        """Verify the 10 most recent messages are included in reverse chronological order."""
        conv = AIConversation.objects.create(user=self.user_a, title="Memory Test")
        for i in range(15):
            AIMessage.objects.create(
                conversation=conv,
                role='user' if i % 2 == 0 else 'assistant',
                content=f"Message {i+1}"
            )

        self.client.force_login(self.user_a)

        with patch('services.ai_service.AIService.ask_study_assistant_with_meta') as mock_ai:
            mock_ai.return_value = {
                'text': 'Memory response',
                'provider': 'gemini',
                'provider_label': 'Google Gemini',
                'is_fallback': False
            }

            url = reverse('assistant:chat_detail', kwargs={'conversation_id': conv.id})
            resp = self.client.post(url, {'question': 'What did we talk about?'})
            self.assertEqual(resp.status_code, 302)

            self.assertTrue(mock_ai.called)
            history = mock_ai.call_args[1].get('conversation_history', [])
            # Must contain the 10 most recent messages (indices 5 through 14)
            self.assertEqual(len(history), 10)
            self.assertEqual(history[0]['content'], 'Message 6')
            self.assertEqual(history[-1]['content'], 'Message 15')

    def test_duplicate_request_prevention(self):
        """Duplicate request within 3 seconds returns 429."""
        self.client.force_login(self.user_a)
        conv = AIConversation.objects.create(user=self.user_a, title="Duplicate Test")
        url = reverse('assistant:chat_detail', kwargs={'conversation_id': conv.id})

        with patch('services.ai_service.AIService.ask_study_assistant_with_meta') as mock_ai:
            mock_ai.return_value = {
                'text': 'OK',
                'provider': 'gemini',
                'provider_label': 'Google Gemini',
                'is_fallback': False
            }

            # First call
            r1 = self.client.post(url, {'question': 'Explain quicksort'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(r1.status_code, 200)

            # Duplicate call immediately
            r2 = self.client.post(url, {'question': 'Explain quicksort'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(r2.status_code, 429)
            self.assertIn('Duplicate request detected', r2.json().get('error', ''))

    def test_conversation_privacy_isolation(self):
        """User B cannot view or post to User A's conversation."""
        conv_a = AIConversation.objects.create(user=self.user_a, title="Private Session A")
        self.client.force_login(self.user_b)

        url = reverse('assistant:chat_detail', kwargs={'conversation_id': conv_a.id})
        # User B should get 404 when trying to access User A's conversation
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        resp_post = self.client.post(url, {'question': 'Spying on user A'})
        self.assertEqual(resp_post.status_code, 404)
