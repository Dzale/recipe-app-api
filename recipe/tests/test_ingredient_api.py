from django import setup

setup()

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from recipe.serializers import IngredientSerializer

from core.models import Ingredient, Recipe
from decimal import Decimal

INGREDIENT_URL = reverse('ingredient-list')


def detail_url(ingredient_id):
    return reverse('ingredient-detail', args=[ingredient_id])


def create_recipe(user, **params):
    defaults = {
        'title': 'Test title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Test desc'
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


def create_ingredient(user, **params):
    defaults = {
        'name': 'Test name',
    }
    defaults.update(params)
    return Ingredient.objects.create(user=user, **defaults)


class PublicIngredientApiTests(TransactionTestCase):

    def setUp(self) -> None:
        self.client = APIClient()

    def test_without_auth_should_return_401(self):
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, res.status_code)


class PrivateIngredientApiTests(TransactionTestCase):

    def setUp(self) -> None:
        payload = {
            'email': 'test@example.com',
            'password': 'test123',
            'name': 'Test name'
        }
        self.user = get_user_model().objects.create_user(**payload)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredient_should_return_200(self):
        payload = {
            'email': 'test123@example.com',
            'password': 'test123',
            'name': 'Test name2'
        }
        other_user = get_user_model().objects.create_user(**payload)
        create_ingredient(user=self.user)
        create_ingredient(user=self.user)
        create_ingredient(user=other_user)
        create_ingredient(user=other_user)

        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(status.HTTP_200_OK, res.status_code)

        ingredients = Ingredient.objects.filter(user=self.user).order_by('-name')
        serialize = IngredientSerializer(ingredients, many=True)
        self.assertEqual(2, len(res.data))
        self.assertEqual(res.data, serialize.data)

    def test_ingredient_partial_update_should_return_200(self):
        ingredient = create_ingredient(user=self.user)
        payload = {
            'name': 'Updated name',
        }
        self.assertEqual(1, Ingredient.objects.count())
        res = self.client.patch(detail_url(ingredient.id), payload)
        self.assertEqual(1, Ingredient.objects.count())

        self.assertEqual(status.HTTP_200_OK, res.status_code)

        ingredient = Ingredient.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(ingredient, k), v)
        self.assertEqual(self.user, ingredient.user)

    def test_ingredient_partial_update_with_new_user_should_return_400(self):
        payload = {
            'email': 'test123@example.com',
            'password': 'test123',
            'name': 'Test name2'
        }
        other_user = get_user_model().objects.create_user(**payload)
        ingredient = create_ingredient(user=self.user)
        payload = {
            'user': other_user.id,
        }

        self.client.patch(detail_url(ingredient.id), payload)

        ingredient.refresh_from_db()
        self.assertEqual(self.user, ingredient.user)

    def test_ingredient_delete_should_return_200(self):
        ingredient = create_ingredient(user=self.user)

        self.assertEqual(1, Ingredient.objects.count())
        res = self.client.delete(detail_url(ingredient.id))
        self.assertEqual(0, Ingredient.objects.count())

        self.assertEqual(status.HTTP_204_NO_CONTENT, res.status_code)

    def test_ingredient_delete_from_other_user_should_return_404(self):
        payload = {
            'email': 'test123@example.com',
            'password': 'test123',
            'name': 'Test name2'
        }
        other_user = get_user_model().objects.create_user(**payload)
        ingredient = create_ingredient(user=other_user)

        self.assertEqual(1, Ingredient.objects.count())
        res = self.client.delete(detail_url(ingredient.id))
        self.assertEqual(1, Ingredient.objects.count())

        self.assertEqual(status.HTTP_404_NOT_FOUND, res.status_code)

    def test_filter_ingredients_assigned_to_recipes_should_return_200(self):
        i1 = create_ingredient(user=self.user, name='I1')
        i2 = create_ingredient(user=self.user, name='I2')
        r1 = create_recipe(user=self.user)
        r2 = create_recipe(user=self.user)
        r1.ingredients.add(i1)
        r2.ingredients.add(i1)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})
        self.assertEqual(status.HTTP_200_OK, res.status_code)
        self.assertEqual(1, len(res.data))

        s1 = IngredientSerializer(i1)
        s2 = IngredientSerializer(i2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)
