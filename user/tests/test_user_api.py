from django import setup
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

setup()

CREATE_USER_URL = reverse('user-list')
ME_URL = reverse('user-me')
UPDATE_ME_URL = reverse('user-update-me')


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

    def test_me_without_authorization_should_return_401(self):
        res = self.client.get(ME_URL)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, res.status_code)

    def test_update_me_without_authorization_should_return_401(self):
        res = self.client.get(UPDATE_ME_URL)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, res.status_code)


class PrivateUserApiTests(TransactionTestCase):

    def setUp(self) -> None:
        payload = {
            'email': 'test@example.com',
            'password': 'test123',
            'name': 'Test name'
        }
        self.user = get_user_model().objects.create_user(**payload)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_me_should_return_200(self):
        res = self.client.get(ME_URL)
        self.assertEqual(status.HTTP_200_OK, res.status_code)

    def test_me_with_post_method_should_return_405(self):
        res = self.client.post(ME_URL)

        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, res.status_code)

    def test_update_me_should_return_200(self):
        payload = {
            'password': 'updated123',
            'name': 'Updated name'
        }

        res = self.client.patch(UPDATE_ME_URL, payload)
        
        self.assertEqual(status.HTTP_200_OK, res.status_code)
        self.user.refresh_from_db()

        self.assertEqual(payload['name'], self.user.name)
        self.assertTrue(self.user.check_password(payload['password']))

    def test_update_me_without_password_should_return_200(self):
        payload = {
            'name': 'Updated name'
        }

        res = self.client.patch(UPDATE_ME_URL, payload)

        self.assertEqual(status.HTTP_200_OK, res.status_code)
        self.user.refresh_from_db()

        self.assertEqual(payload['name'], self.user.name)
        self.assertTrue(self.user.check_password('test123'))
