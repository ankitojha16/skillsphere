from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import StudentProfile

class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('accounts:signup')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.profile_setup_url = reverse('accounts:profile_setup')
        self.profile_url = reverse('accounts:profile')

    def test_user_registration_success(self):
        response = self.client.post(self.signup_url, {
            'full_name': 'Test Student',
            'email': 'student@test.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
            'terms_accepted': True
        })
        # Should redirect to profile setup
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(self.profile_setup_url))
        
        # Verify user & profile created
        user = User.objects.get(email='student@test.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.profile.full_name, 'Test Student')

    def test_duplicate_email_registration_rejected(self):
        User.objects.create_user(username='existing', email='duplicate@test.com', password='Password123!')
        response = self.client.post(self.signup_url, {
            'full_name': 'Duplicate User',
            'email': 'duplicate@test.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
            'terms_accepted': True
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', 'An account with this email address already exists.')

    def test_password_mismatch_rejected(self):
        response = self.client.post(self.signup_url, {
            'full_name': 'Mismatch User',
            'email': 'mismatch@test.com',
            'password': 'StrongPassword123!',
            'confirm_password': 'DifferentPassword123!',
            'terms_accepted': True
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'confirm_password', 'Passwords do not match.')

    def test_login_and_logout(self):
        user = User.objects.create_user(username='loginuser', email='login@test.com', password='Password123!')
        # Login
        response = self.client.post(self.login_url, {
            'email': 'login@test.com',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 302)

        # Logout
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)

    def test_profile_update(self):
        user = User.objects.create_user(username='profileuser', email='profile@test.com', password='Password123!')
        self.client.force_login(user)

        response = self.client.post(self.profile_setup_url, {
            'full_name': 'Updated Name',
            'education_level': 'postgraduate',
            'institution': 'Stanford University',
            'learning_level': 'advanced',
            'selected_interests': ['python', 'ai'],
            'career_goal': 'AI Engineer'
        })
        self.assertEqual(response.status_code, 302)

        profile = StudentProfile.objects.get(user=user)
        self.assertEqual(profile.full_name, 'Updated Name')
        self.assertEqual(profile.education_level, 'postgraduate')
        self.assertEqual(profile.institution, 'Stanford University')
        self.assertIn('python', profile.get_interests_list())
        self.assertIn('ai', profile.get_interests_list())

    def test_profile_setup_with_avatar_upload(self):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile

        user = User.objects.create_user(username='avataruser', email='avatar@test.com', password='Password123!')
        self.client.force_login(user)

        # Create dummy PNG image
        img = Image.new('RGB', (100, 100), color='purple')
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_file = SimpleUploadedFile("my_dp.png", img_io.getvalue(), content_type="image/png")

        response = self.client.post(self.profile_setup_url, {
            'full_name': 'Ankit Kumar',
            'avatar': img_file,
            'education_level': 'undergraduate',
            'institution': 'IIT Delhi',
            'learning_level': 'intermediate',
            'selected_interests': ['python', 'dsa'],
            'career_goal': 'Full-Stack Developer'
        })
        self.assertEqual(response.status_code, 302)

        profile = StudentProfile.objects.get(user=user)
        self.assertEqual(profile.full_name, 'Ankit Kumar')
        self.assertEqual(profile.institution, 'IIT Delhi')
        self.assertTrue(profile.avatar_data_uri.startswith('data:image/jpeg;base64,'))
        self.assertEqual(profile.avatar_url, profile.avatar_data_uri)
