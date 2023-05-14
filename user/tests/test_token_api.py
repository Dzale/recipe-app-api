from django import setup
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

setup()

CREATE_TOKEN_URL = reverse('token-list')


class PublicTokenApiTests(TransactionTestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_should_return_200(self):
        payload = {
            'email': 'test@example.com',
            'password': 'test123',
        }
        get_user_model().objects.create_user(**payload)

        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertEqual(status.HTTP_200_OK, res.status_code)
        self.assertIn('token', res.data)

    def test_create_with_bad_credentials_should_return_400(self):
        get_user_model().objects.create_user(
            email='test@example.com',
            password='test123',
        )

        res = self.client.post(CREATE_TOKEN_URL, {
            'email': 'test@example.com',
            'password': 'invalid-password',
        })

        self.assertEqual(status.HTTP_400_BAD_REQUEST, res.status_code)

    def test_create_without_password_should_return_400(self):
        payload = {
            'email': 'test@example.com',
            'password': '',
        }
        get_user_model().objects.create_user(**payload)

        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, res.status_code)
