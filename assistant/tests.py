from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from assistant.models import AIConversation, AIMessage

class AssistantTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='aistudent', email='ai@test.com', password='Password123!')
        self.client.force_login(self.user)

    def test_assistant_index_view(self):
        response = self.client.get(reverse('assistant:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Study Assistant')

    def test_ask_question_creates_messages(self):
        conv = AIConversation.objects.create(user=self.user, title='Session 1', mode='detailed')
        url = reverse('assistant:chat_detail', kwargs={'conversation_id': conv.id})
        
        response = self.client.post(url, {
            'question': 'Explain Python OOP with examples',
            'mode': 'detailed'
        })
        self.assertEqual(response.status_code, 302)

        # Verify messages created
        self.assertEqual(conv.messages.count(), 2)
        user_msg = conv.messages.filter(role='user').first()
        ai_msg = conv.messages.filter(role='assistant').first()
        self.assertEqual(user_msg.content, 'Explain Python OOP with examples')
        self.assertIn('Object-Oriented Programming', ai_msg.content)
        # Verify provider and fallback tracking
        self.assertTrue(ai_msg.provider)
        self.assertIsInstance(ai_msg.is_fallback, bool)

    def test_delete_conversation(self):
        conv = AIConversation.objects.create(user=self.user, title='To Delete', mode='code')
        del_url = reverse('assistant:delete_chat', kwargs={'conversation_id': conv.id})
        response = self.client.post(del_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AIConversation.objects.filter(id=conv.id).exists())

    def test_ai_status_endpoint(self):
        status_url = reverse('assistant:status')
        resp = self.client.get(status_url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('online'))
        self.assertIn('provider', data)

    def test_ajax_post_greeting_returns_warm_welcome(self):
        """Conversational greetings ('hi') via AJAX succeed with 200 and a helpful introduction."""
        conv = AIConversation.objects.create(user=self.user, title='Session Greeting', mode='detailed')
        url = reverse('assistant:chat_detail', kwargs={'conversation_id': conv.id})
        response = self.client.post(url, {
            'question': 'hi',
            'mode': 'detailed'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('SkillSphere AI Study Assistant', data.get('ai_message', ''))
        self.assertNotIn('Please enter a valid academic or programming question', data.get('ai_message', ''))

    def test_ajax_post_marketing_and_business_domain(self):
        """Business/Management inquiries (4Ps) return structured academic marketing concepts."""
        conv = AIConversation.objects.create(user=self.user, title='Business Strategy', mode='detailed')
        url = reverse('assistant:chat_detail', kwargs={'conversation_id': conv.id})
        response = self.client.post(url, {
            'question': 'Explain the 4 Ps of marketing for BBA/MBA',
            'mode': 'detailed'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('Product', data.get('ai_message', ''))
        self.assertIn('Price', data.get('ai_message', ''))
        self.assertIn('Place', data.get('ai_message', ''))
        self.assertIn('Promotion', data.get('ai_message', ''))

    def test_empty_question_returns_400(self):
        """Empty question via AJAX returns 400 with helpful prompt validation message."""
        conv = AIConversation.objects.create(user=self.user, title='Empty Test', mode='detailed')
        url = reverse('assistant:chat_detail', kwargs={'conversation_id': conv.id})
        response = self.client.post(url, {
            'question': '   ',
            'mode': 'detailed'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_gadget_query_returns_scope_notice(self):
        """Shopping/phone queries return polite scope notice directing to academic curriculum."""
        conv = AIConversation.objects.create(user=self.user, title='Phone Advice', mode='detailed')
        url = reverse('assistant:chat_detail', kwargs={'conversation_id': conv.id})
        response = self.client.post(url, {
            'question': 'best phone under 10k',
            'mode': 'detailed'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        ai_text = data.get('ai_message', '')
        self.assertIn('Domain Scope Notice', ai_text)
        self.assertIn('outside our academic coursework', ai_text)
        self.assertIn('Computer Science & IT', ai_text)
        self.assertNotIn('Redmi', ai_text)

    def test_off_topic_query_returns_scope_notice(self):
        """Off-topic queries (e.g. movies) return a polite scope notice explaining what to ask."""
        conv = AIConversation.objects.create(user=self.user, title='Movie Chat', mode='detailed')
        url = reverse('assistant:chat_detail', kwargs={'conversation_id': conv.id})
        response = self.client.post(url, {
            'question': 'suggest a movie for tonight',
            'mode': 'detailed'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        ai_text = data.get('ai_message', '')
        self.assertIn('Domain Scope Notice', ai_text)
        self.assertIn('outside our academic coursework', ai_text)
        self.assertIn('Computer Science & IT', ai_text)

    def test_fitness_query_returns_scope_notice(self):
        """Queries for 'for healthy legs' return a polite scope notice directing to learning disciplines."""
        conv = AIConversation.objects.create(user=self.user, title='Fitness Chat', mode='detailed')
        url = reverse('assistant:chat_detail', kwargs={'conversation_id': conv.id})
        response = self.client.post(url, {
            'question': 'for healthy legs',
            'mode': 'detailed'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        ai_text = data.get('ai_message', '')
        self.assertIn('Domain Scope Notice', ai_text)
        self.assertIn('outside our academic coursework', ai_text)
        self.assertIn('Business Administration & Management', ai_text)
        self.assertNotIn('Squats', ai_text)
        self.assertNotIn('underlying computational mechanics', ai_text)

    def test_user_query_with_typo_ooen_best_couse_recommends_courses(self):
        """User query 'ooen a best couse for me' (with typos) correctly returns course recommendations, not scope notice."""
        conv = AIConversation.objects.create(user=self.user, title='Course Advice', mode='detailed')
        url = reverse('assistant:chat_detail', kwargs={'conversation_id': conv.id})
        response = self.client.post(url, {
            'question': 'ooen a best couse for me',
            'mode': 'detailed'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        ai_text = data.get('ai_message', '')
        # Must NOT be flagged as out-of-domain scope notice
        self.assertNotIn('Domain Scope Notice', ai_text)
        self.assertNotIn('outside our academic coursework', ai_text)
        # Must provide course recommendations and navigation instructions
        self.assertIn('Recommended Courses', ai_text)
        self.assertIn('/courses/', ai_text)
        self.assertIn('B.Tech', ai_text)

    def test_open_best_course_for_me_in_domain(self):
        """User query 'open a best course for me' returns course guidance and catalog link."""
        conv = AIConversation.objects.create(user=self.user, title='Course Inquiry', mode='detailed')
        url = reverse('assistant:chat_detail', kwargs={'conversation_id': conv.id})
        response = self.client.post(url, {
            'question': 'open a best course for me',
            'mode': 'detailed'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        ai_text = data.get('ai_message', '')
        self.assertNotIn('Domain Scope Notice', ai_text)
        self.assertIn('Recommended Courses', ai_text)
        self.assertIn('/courses/', ai_text)




