from django import setup
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

setup()

CREATE_USER_URL = reverse('user-list')


class PublicUserApiTests(TransactionTestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_should_return_201(self):
        payload = {
            'email': 'test@example.com',
            'password': 'test123',
            'name': 'Test name'
        }

        self.assertEqual(0, get_user_model().objects.count())
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(1, get_user_model().objects.count())

        self.assertEqual(status.HTTP_201_CREATED, res.status_code)

        user = get_user_model().objects.first()
        self.assertEqual(payload['email'], user.email)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_create_with_existing_email_should_return_400(self):
        payload = {
            'email': 'test@example.com',
            'password': 'test123',
            'name': 'Test name'
        }
        get_user_model().objects.create_user(**payload)

        self.assertEqual(1, get_user_model().objects.count())
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(1, get_user_model().objects.count())

        self.assertEqual(status.HTTP_400_BAD_REQUEST, res.status_code)

    def test_create_with_short_password_should_return_400(self):
        payload = {
            'email': 'test@example.com',
            'password': 'test',
            'name': 'Test name'
        }

        self.assertEqual(0, get_user_model().objects.count())
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(0, get_user_model().objects.count())

        self.assertEqual(status.HTTP_400_BAD_REQUEST, res.status_code)
