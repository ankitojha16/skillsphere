from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from notifications.models import Notification

class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='notiftester', email='notif@test.com', password='Password123!')
        self.client = Client()
        self.client.login(username='notiftester', password='Password123!')
        self.notif1 = Notification.objects.create(
            user=self.user,
            title='Teammate Request',
            message='Someone requested to join your project.',
            is_read=False
        )
        self.notif2 = Notification.objects.create(
            user=self.user,
            title='Event Reminder',
            message='Hackathon starts tomorrow.',
            is_read=False
        )

    def test_notification_list_and_context_processor(self):
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Teammate Request')
        self.assertContains(response, 'Event Reminder')
        self.assertEqual(response.context['unread_notifications_count'], 2)

    def test_mark_single_notification_read(self):
        response = self.client.get(reverse('notifications:mark_read', kwargs={'pk': self.notif1.pk}))
        self.assertEqual(response.status_code, 302)
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.is_read)

    def test_mark_all_read(self):
        response = self.client.get(reverse('notifications:mark_all_read'))
        self.assertEqual(response.status_code, 302)
        unread = Notification.objects.filter(user=self.user, is_read=False).count()
        self.assertEqual(unread, 0)

    def test_delete_notification(self):
        response = self.client.post(reverse('notifications:delete', kwargs={'pk': self.notif2.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Notification.objects.filter(id=self.notif2.id).exists())
