from django import setup

setup()

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

from core.models import Recipe

RECIPES_URL = reverse('recipe-list')


def detail_url(recipe_id):
    return reverse('recipe-detail', args=[recipe_id])


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

    def test_get_recipe_details_should_return_200(self):
        recipe = create_recipe(user=self.user)

        res = self.client.get(detail_url(recipe.id))
        self.assertEqual(status.HTTP_200_OK, res.status_code)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe_should_return_201(self):
        payload = {
            'title': 'Test title',
            'time_minutes': 22,
            'price': Decimal('5.25'),
            'description': 'Test desc'
        }
        self.assertEqual(0, Recipe.objects.count())
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(1, Recipe.objects.count())

        self.assertEqual(status.HTTP_201_CREATED, res.status_code)

        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(self.user, recipe.user)

    def test_recipe_partial_update_should_return_200(self):
        recipe = create_recipe(user=self.user)
        payload = {
            'title': 'Updated title',
        }
        self.assertEqual(1, Recipe.objects.count())
        res = self.client.patch(detail_url(recipe.id), payload)
        self.assertEqual(1, Recipe.objects.count())

        self.assertEqual(status.HTTP_200_OK, res.status_code)

        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(self.user, recipe.user)

    def test_recipe_update_should_return_200(self):
        recipe = create_recipe(user=self.user)
        payload = {
            'title': 'Updated title',
            'time_minutes': 222,
            'price': Decimal('52.25'),
            'description': 'Updated desc'
        }
        self.assertEqual(1, Recipe.objects.count())
        res = self.client.put(detail_url(recipe.id), payload)
        self.assertEqual(1, Recipe.objects.count())

        self.assertEqual(status.HTTP_200_OK, res.status_code)

        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(self.user, recipe.user)

    def test_recipe_partial_update_with_new_user_should_return_400(self):
        payload = {
            'email': 'test123@example.com',
            'password': 'test123',
            'name': 'Test name2'
        }
        other_user = get_user_model().objects.create_user(**payload)
        recipe = create_recipe(user=self.user)
        payload = {
            'user': other_user.id,
        }

        self.client.patch(detail_url(recipe.id), payload)

        recipe.refresh_from_db()
        self.assertEqual(self.user, recipe.user)

    def test_recipe_delete_should_return_200(self):
        recipe = create_recipe(user=self.user)

        self.assertEqual(1, Recipe.objects.count())
        res = self.client.delete(detail_url(recipe.id))
        self.assertEqual(0, Recipe.objects.count())

        self.assertEqual(status.HTTP_204_NO_CONTENT, res.status_code)

    def test_recipe_delete_from_other_user_should_return_404(self):
        payload = {
            'email': 'test123@example.com',
            'password': 'test123',
            'name': 'Test name2'
        }
        other_user = get_user_model().objects.create_user(**payload)
        recipe = create_recipe(user=other_user)

        self.assertEqual(1, Recipe.objects.count())
        res = self.client.delete(detail_url(recipe.id))
        self.assertEqual(1, Recipe.objects.count())

        self.assertEqual(status.HTTP_404_NOT_FOUND, res.status_code)
