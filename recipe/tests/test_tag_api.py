from django import setup

setup()

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from recipe.serializers import TagSerializer

from core.models import Tag

TAG_URL = reverse('tag-list')


def detail_url(tag_id):
    return reverse('tag-detail', args=[tag_id])


def create_tag(user, **params):
    defaults = {
        'name': 'Test name',
    }
    defaults.update(params)
    return Tag.objects.create(user=user, **defaults)


class PublicTagApiTests(TransactionTestCase):

    def setUp(self) -> None:
        self.client = APIClient()

    def test_without_auth_should_return_401(self):
        res = self.client.get(TAG_URL)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, res.status_code)


class PrivateTagApiTests(TransactionTestCase):

    def setUp(self) -> None:
        payload = {
            'email': 'test@example.com',
            'password': 'test123',
            'name': 'Test name'
        }
        self.user = get_user_model().objects.create_user(**payload)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tag_should_return_200(self):
        payload = {
            'email': 'test123@example.com',
            'password': 'test123',
            'name': 'Test name2'
        }
        other_user = get_user_model().objects.create_user(**payload)
        create_tag(user=self.user)
        create_tag(user=self.user)
        create_tag(user=other_user)
        create_tag(user=other_user)

        res = self.client.get(TAG_URL)
        self.assertEqual(status.HTTP_200_OK, res.status_code)

        tags = Tag.objects.filter(user=self.user).order_by('-name')
        serialize = TagSerializer(tags, many=True)
        self.assertEqual(2, len(res.data))
        self.assertEqual(res.data, serialize.data)

    def test_tag_partial_update_should_return_200(self):
        tag = create_tag(user=self.user)
        payload = {
            'name': 'Updated name',
        }
        self.assertEqual(1, Tag.objects.count())
        res = self.client.patch(detail_url(tag.id), payload)
        self.assertEqual(1, Tag.objects.count())

        self.assertEqual(status.HTTP_200_OK, res.status_code)

        tag = Tag.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(tag, k), v)
        self.assertEqual(self.user, tag.user)

    def test_tag_partial_update_with_new_user_should_return_400(self):
        payload = {
            'email': 'test123@example.com',
            'password': 'test123',
            'name': 'Test name2'
        }
        other_user = get_user_model().objects.create_user(**payload)
        tag = create_tag(user=self.user)
        payload = {
            'user': other_user.id,
        }

        self.client.patch(detail_url(tag.id), payload)

        tag.refresh_from_db()
        self.assertEqual(self.user, tag.user)

    def test_tag_delete_should_return_200(self):
        tag = create_tag(user=self.user)

        self.assertEqual(1, Tag.objects.count())
        res = self.client.delete(detail_url(tag.id))
        self.assertEqual(0, Tag.objects.count())

        self.assertEqual(status.HTTP_204_NO_CONTENT, res.status_code)

    def test_tag_delete_from_other_user_should_return_404(self):
        payload = {
            'email': 'test123@example.com',
            'password': 'test123',
            'name': 'Test name2'
        }
        other_user = get_user_model().objects.create_user(**payload)
        tag = create_tag(user=other_user)

        self.assertEqual(1, Tag.objects.count())
        res = self.client.delete(detail_url(tag.id))
        self.assertEqual(1, Tag.objects.count())

        self.assertEqual(status.HTTP_404_NOT_FOUND, res.status_code)
