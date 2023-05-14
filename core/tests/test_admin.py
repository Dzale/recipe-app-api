from django import setup
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

setup()


class AdminSiteTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin1@example.com',
            password='test123'
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='user1@example.com',
            password='test123',
            name='Test User'
        )

    def test_user_changelist_should_return_list_of_users(self):
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_user_change_should_return_200(self):
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(200, res.status_code)

    def test_user_add_should_return_200(self):
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(200, res.status_code)
