from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from events.models import Event, SavedEvent

class EventTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='eventtester', email='ev@test.com', password='Password123!')
        self.client = Client()
        self.client.login(username='eventtester', password='Password123!')
        self.event = Event.objects.create(
            title='Global Student Hackathon 2026',
            organizer='Collegiate League',
            category='hackathon',
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=12),
            registration_url='https://example.com/hack',
            description='A 48-hour student hackathon.'
        )

    def test_event_list_and_filter(self):
        response = self.client.get(reverse('events:list'), {'category': 'hackathon'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Global Student Hackathon 2026')

    def test_save_event_and_reminder(self):
        response = self.client.post(reverse('events:toggle_save_event', kwargs={'pk': self.event.pk}))
        self.assertEqual(response.status_code, 302)
        saved = SavedEvent.objects.filter(user=self.user, event=self.event).first()
        self.assertIsNotNone(saved)
        self.assertTrue(saved.reminder_set)
