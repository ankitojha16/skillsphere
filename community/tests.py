from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from community.models import CommunityPost, CommunityComment, CommunityLike, ContentReport

class CommunityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='comtester', email='com@test.com', password='Password123!')
        self.client = Client()
        self.client.login(username='comtester', password='Password123!')
        self.post = CommunityPost.objects.create(
            user=self.user,
            title='Understanding ACID Transactions in PostgreSQL',
            category='python',
            content='Atomicity, Consistency, Isolation, and Durability ensure data integrity.'
        )

    def test_community_feed_view(self):
        response = self.client.get(reverse('community:feed'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Understanding ACID Transactions')

    def test_create_discussion_post(self):
        response = self.client.post(reverse('community:create_post'), {
            'title': 'How to optimize Django query sets?',
            'category': 'web-development',
            'content': 'Using select_related for ForeignKeys and prefetch_related for ManyToMany.',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CommunityPost.objects.filter(title='How to optimize Django query sets?').exists())

    def test_add_comment_and_like(self):
        # Comment
        response = self.client.post(reverse('community:post_detail', kwargs={'pk': self.post.pk}), {
            'comment': 'Great explanation! Isolation levels are key.',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.post.comments.count(), 1)

        # Like
        like_resp = self.client.post(reverse('community:toggle_like', kwargs={'pk': self.post.pk}))
        self.assertEqual(like_resp.status_code, 302)
        self.assertTrue(CommunityLike.objects.filter(user=self.user, post=self.post).exists())

    def test_submit_content_report(self):
        response = self.client.post(reverse('community:report'), {
            'content_type': 'post',
            'object_id': self.post.id,
            'reason': 'spam',
            'description': 'Suspicious advertising link',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ContentReport.objects.filter(object_id=self.post.id, reason='spam').exists())
