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

