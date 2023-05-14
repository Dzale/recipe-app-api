from django import setup
from django.test import TestCase
from django.contrib.auth import get_user_model

setup()


class ModelTests(TestCase):
    def test_create_user_with_email_should_succeed(self):
        email = 'test@example.com'
        password = '123456'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_user_email_normalized(self):
        sample_emails = [
            [
                'test1@Example.com', 'test1@example.com'
            ],
            [
                'Test2@Example.com', 'Test2@example.com'
            ],
            [
                'TEST3@EXAMPLE.COM', 'TEST3@example.com'
            ],
            [
                'test4@example.COM', 'test4@example.com'
            ],
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email=email, password='test123')
            self.assertEqual(expected, user.email)

    def test_create_user_without_email_should_raise_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email='', password='test123')

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            email='test@example.com',
            password='test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
