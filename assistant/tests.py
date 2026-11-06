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
