from django import setup

setup()

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from recipe.serializers import RecipeSerializer

from core.models import Recipe

RECIPES_URL = reverse('recipe-list')


def create_recipe(user, **params):
    defaults = {
        'title': 'Test title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Test desc'
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TransactionTestCase):

    def setUp(self) -> None:
        self.client = APIClient()

    def test_without_auth_should_return_401(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, res.status_code)


class PrivateRecipeApiTests(TransactionTestCase):

    def setUp(self) -> None:
        payload = {
            'email': 'test@example.com',
            'password': 'test123',
            'name': 'Test name'
        }
        self.user = get_user_model().objects.create_user(**payload)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes_should_return_200(self):
        payload = {
            'email': 'test123@example.com',
            'password': 'test123',
            'name': 'Test name2'
        }
        other_user = get_user_model().objects.create_user(**payload)
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        create_recipe(user=other_user)
        create_recipe(user=other_user)

        res = self.client.get(RECIPES_URL)
        self.assertEqual(status.HTTP_200_OK, res.status_code)

        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serialize = RecipeSerializer(recipes, many=True)
        self.assertEqual(2, len(res.data))
        self.assertEqual(res.data, serialize.data)
